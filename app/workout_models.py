from __future__ import annotations

from pydantic import (
    BaseModel,
    Field,
    field_validator,
)
from datetime import date, datetime
from typing import Annotated, Literal
from uuid import UUID


class TimedWorkoutStep(BaseModel):
    """
    One normal timed step.

    ChatGPT cannot send Garmin's internal IDs or arbitrary JSON.
    It can only choose one of these four step types.
    """

    kind: Literal[
        "warmup",
        "interval",
        "recovery",
        "cooldown",
    ]

    duration_seconds: int = Field(
        ge=30,
        le=7200,
    )


class RepeatWorkoutBlock(BaseModel):
    """
    A repeat block such as:

    Repeat 5 times:
    - run for 3 minutes
    - recover for 2 minutes
    """

    kind: Literal["repeat"] = "repeat"

    repetitions: int = Field(
        ge=2,
        le=20,
    )

    steps: list[TimedWorkoutStep] = Field(
        min_length=1,
        max_length=4,
    )

    @field_validator("steps")
    @classmethod
    def validate_repeat_steps(
        cls,
        steps: list[TimedWorkoutStep],
    ) -> list[TimedWorkoutStep]:
        allowed_kinds = {
            "interval",
            "recovery",
        }

        invalid_kinds = [step.kind for step in steps if step.kind not in allowed_kinds]

        if invalid_kinds:
            raise ValueError(
                "Repeat blocks may contain only " "interval and recovery steps."
            )

        if not any(step.kind == "interval" for step in steps):
            raise ValueError(
                "A repeat block must contain " "at least one interval step."
            )

        return steps


WorkoutDraftStep = Annotated[
    TimedWorkoutStep | RepeatWorkoutBlock,
    Field(discriminator="kind"),
]


class WorkoutDraftRequest(BaseModel):
    """
    The restricted workout proposal accepted from ChatGPT.
    """

    name: str = Field(
        min_length=1,
        max_length=80,
    )

    scheduled_date: date

    steps: list[WorkoutDraftStep] = Field(
        min_length=1,
        max_length=20,
    )


class WorkoutDraftPreview(BaseModel):
    """
    The readable result returned before anything is uploaded.
    """

    draft_id: UUID

    draft: WorkoutDraftRequest

    estimated_duration_seconds: int = Field(gt=0)

    summary: list[str]

    warnings: list[str] = Field(default_factory=list)


class StoredWorkoutDraft(BaseModel):
    draft_id: UUID
    created_at: datetime

    status: Literal[
        "previewed",
        "uploading",
        "uploaded",
        "scheduling",
        "committed",
        "failed",
    ] = "previewed"

    draft: WorkoutDraftRequest

    estimated_duration_seconds: int = Field(gt=0)

    summary: list[str]

    warnings: list[str] = Field(default_factory=list)

    garmin_workout_id: int | None = None
    committed_at: datetime | None = None
    failure_message: str | None = None


class WorkoutCommitRequest(BaseModel):
    confirmation: Literal["UPLOAD_AND_SCHEDULE"]


class WorkoutCommitResult(BaseModel):
    draft_id: UUID
    status: Literal["committed"]

    workout_name: str
    scheduled_date: date
    garmin_workout_id: int

    already_committed: bool = False
