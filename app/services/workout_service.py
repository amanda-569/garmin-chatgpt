from __future__ import annotations

from datetime import date, datetime, timezone
from uuid import uuid4, UUID
from zoneinfo import ZoneInfo

from app.config import settings
from app.workout_builder import (
    calculate_workout_duration,
)
from app.providers.workout_base import (
    WorkoutWriteProvider,
)
from app.services.run_service import (
    provider as shared_provider,
)
from app.storage.workout_drafts import (
    get_workout_draft_store,
)
from app.workout_builder import (
    build_running_workout,
    calculate_workout_duration,
)
from app.workout_models import (
    RepeatWorkoutBlock,
    StoredWorkoutDraft,
    TimedWorkoutStep,
    WorkoutCommitResult,
    WorkoutDraftPreview,
    WorkoutDraftRequest,
)

draft_store = get_workout_draft_store()


def _local_today() -> date:
    timezone = ZoneInfo(settings.user_timezone)

    return datetime.now(timezone).date()


def _format_duration(seconds: int) -> str:
    minutes, remaining_seconds = divmod(
        seconds,
        60,
    )

    if remaining_seconds == 0:
        return f"{minutes} min"

    return f"{minutes} min " f"{remaining_seconds} sec"


def _describe_timed_step(
    step: TimedWorkoutStep,
) -> str:
    labels = {
        "warmup": "Warm up",
        "interval": "Run interval",
        "recovery": "Recover",
        "cooldown": "Cool down",
    }

    return f"{labels[step.kind]} for " f"{_format_duration(step.duration_seconds)}"


def _describe_repeat_block(
    block: RepeatWorkoutBlock,
) -> str:
    child_description = ", ".join(_describe_timed_step(step) for step in block.steps)

    return f"Repeat {block.repetitions} times: " f"{child_description}"


def create_workout_preview(
    draft: WorkoutDraftRequest,
) -> WorkoutDraftPreview:
    """
    Validate and describe a workout proposal.

    This function does not contact Garmin.
    """
    if draft.scheduled_date < _local_today():
        raise ValueError("The scheduled date cannot be " "in the past.")

    duration_seconds = calculate_workout_duration(draft)

    if duration_seconds < 300:
        raise ValueError("The total workout must be at " "least 5 minutes.")

    if duration_seconds > 14400:
        raise ValueError("The total workout cannot exceed " "4 hours.")

    summary: list[str] = []

    for step in draft.steps:
        if isinstance(
            step,
            TimedWorkoutStep,
        ):
            summary.append(_describe_timed_step(step))
        else:
            summary.append(_describe_repeat_block(step))

    warnings: list[str] = []

    has_warmup = any(
        isinstance(step, TimedWorkoutStep) and step.kind == "warmup"
        for step in draft.steps
    )

    has_cooldown = any(
        isinstance(step, TimedWorkoutStep) and step.kind == "cooldown"
        for step in draft.steps
    )

    if not has_warmup:
        warnings.append("The workout has no warmup step.")

    if not has_cooldown:
        warnings.append("The workout has no cooldown step.")

    draft_id = uuid4()

    preview = WorkoutDraftPreview(
        draft_id=draft_id,
        draft=draft,
        estimated_duration_seconds=(duration_seconds),
        summary=summary,
        warnings=warnings,
    )

    record = StoredWorkoutDraft(
        draft_id=draft_id,
        created_at=datetime.now(timezone.utc),
        draft=draft,
        estimated_duration_seconds=(duration_seconds),
        summary=summary,
        warnings=warnings,
    )

    draft_store.save(record)

    return preview


class WorkoutCommitConflictError(RuntimeError):
    pass


class WorkoutCommitExternalError(RuntimeError):
    pass


def _get_write_provider() -> WorkoutWriteProvider:
    if not isinstance(
        shared_provider,
        WorkoutWriteProvider,
    ):
        raise WorkoutCommitConflictError(
            "The configured provider does not " "support workout uploads."
        )

    return shared_provider


def _extract_workout_id(
    response: dict,
) -> int:
    possible_fields = (
        "workoutId",
        "workoutIdPk",
        "id",
    )

    for field_name in possible_fields:
        value = response.get(field_name)

        if value is None:
            continue

        try:
            workout_id = int(value)
        except (TypeError, ValueError):
            continue

        if workout_id > 0:
            return workout_id

    raise WorkoutCommitExternalError(
        "Garmin uploaded the workout but did " "not return a recognizable workout ID."
    )


def commit_workout_draft(
    draft_id: UUID,
) -> WorkoutCommitResult:
    record = draft_store.get(draft_id)

    if record.status == "committed":
        if record.garmin_workout_id is None:
            raise WorkoutCommitConflictError(
                "Committed draft has no Garmin " "workout ID."
            )

        return WorkoutCommitResult(
            draft_id=record.draft_id,
            status="committed",
            workout_name=record.draft.name,
            scheduled_date=(record.draft.scheduled_date),
            garmin_workout_id=(record.garmin_workout_id),
            already_committed=True,
        )

    if record.draft.scheduled_date < _local_today():
        raise WorkoutCommitConflictError(
            "The workout date is now in the past. " "Create a new preview."
        )

    if record.status in {
        "uploading",
        "scheduling",
        "failed",
    }:
        raise WorkoutCommitConflictError(
            f"Draft is currently marked "
            f"{record.status!r}. Check Garmin "
            "before attempting another write."
        )

    provider = _get_write_provider()

    if record.status == "previewed":
        record.status = "uploading"
        record.failure_message = None
        draft_store.save(record)

        workout = build_running_workout(record.draft)

        try:
            upload_response = provider.upload_running_workout(workout)

            workout_id = _extract_workout_id(upload_response)
        except Exception as exc:
            record.failure_message = (
                "Upload failed or its result is "
                "uncertain. Check Garmin before "
                "retrying."
            )
            draft_store.save(record)

            raise WorkoutCommitExternalError(record.failure_message) from exc

        record.garmin_workout_id = workout_id
        record.status = "uploaded"
        draft_store.save(record)

    if record.status == "uploaded":
        if record.garmin_workout_id is None:
            raise WorkoutCommitConflictError(
                "Uploaded draft has no Garmin " "workout ID."
            )

        record.status = "scheduling"
        record.failure_message = None
        draft_store.save(record)

        try:
            provider.schedule_workout(
                record.garmin_workout_id,
                record.draft.scheduled_date,
            )
        except Exception as exc:
            record.failure_message = (
                "Scheduling failed or its result "
                "is uncertain. Check the Garmin "
                "calendar before retrying."
            )
            draft_store.save(record)

            raise WorkoutCommitExternalError(record.failure_message) from exc

        record.status = "committed"
        record.committed_at = datetime.now(timezone.utc)
        record.failure_message = None
        draft_store.save(record)

    return WorkoutCommitResult(
        draft_id=record.draft_id,
        status="committed",
        workout_name=record.draft.name,
        scheduled_date=(record.draft.scheduled_date),
        garmin_workout_id=(record.garmin_workout_id),
    )
