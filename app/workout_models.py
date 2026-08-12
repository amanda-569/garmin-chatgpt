from __future__ import annotations

from datetime import date, datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    Field,
    field_validator,
    model_validator,
)


class WorkoutStep(BaseModel):
    kind: Literal[
        "warmup",
        "interval",
        "recovery",
        "cooldown",
    ]

    end_type: Literal[
        "time",
        "distance",
        "lap_button",
    ] = "time"

    duration_seconds: int | None = Field(
        default=None,
        ge=1,
        le=7200,
    )

    distance_meters: float | None = Field(
        default=None,
        ge=1,
        le=100000,
    )

    target_type: Literal[
        "open",
        "heart_rate",
        "pace",
    ] = "open"

    heart_rate_min_bpm: int | None = Field(
        default=None,
        ge=40,
        le=230,
    )

    heart_rate_max_bpm: int | None = Field(
        default=None,
        ge=40,
        le=230,
    )

    target_pace_fast_seconds_per_km: float | None = Field(
        default=None,
        ge=120,
        le=1800,
    )

    target_pace_slow_seconds_per_km: float | None = Field(
        default=None,
        ge=120,
        le=1800,
    )

    @model_validator(mode="after")
    def validate_step(
        self,
    ) -> "WorkoutStep":
        if self.end_type == "time":
            if self.duration_seconds is None:
                raise ValueError(
                    "duration_seconds is required " "for time-based steps."
                )

            if self.distance_meters is not None:
                raise ValueError(
                    "distance_meters must be omitted " "for time-based steps."
                )

        elif self.end_type == "distance":
            if self.distance_meters is None:
                raise ValueError(
                    "distance_meters is required " "for distance-based steps."
                )

            if self.duration_seconds is not None:
                raise ValueError(
                    "duration_seconds must be omitted " "for distance-based steps."
                )

        else:
            if self.duration_seconds is not None or self.distance_meters is not None:
                raise ValueError(
                    "lap_button steps cannot include "
                    "duration_seconds or distance_meters."
                )

        has_hr_min = self.heart_rate_min_bpm is not None

        has_hr_max = self.heart_rate_max_bpm is not None

        if has_hr_min != has_hr_max:
            raise ValueError(
                "heart_rate_min_bpm and "
                "heart_rate_max_bpm must either "
                "both be provided or both be omitted."
            )

        if (
            self.heart_rate_min_bpm is not None
            and self.heart_rate_max_bpm is not None
            and self.heart_rate_min_bpm >= self.heart_rate_max_bpm
        ):
            raise ValueError(
                "heart_rate_min_bpm must be less " "than heart_rate_max_bpm."
            )

        has_pace_fast = self.target_pace_fast_seconds_per_km is not None

        has_pace_slow = self.target_pace_slow_seconds_per_km is not None

        if has_pace_fast != has_pace_slow:
            raise ValueError(
                "target_pace_fast_seconds_per_km and "
                "target_pace_slow_seconds_per_km must "
                "either both be provided or both be omitted."
            )

        if (
            self.target_pace_fast_seconds_per_km is not None
            and self.target_pace_slow_seconds_per_km is not None
            and self.target_pace_fast_seconds_per_km
            > self.target_pace_slow_seconds_per_km
        ):
            raise ValueError(
                "target_pace_fast_seconds_per_km must "
                "be less than or equal to "
                "target_pace_slow_seconds_per_km."
            )

        has_hr_target = has_hr_min and has_hr_max

        has_pace_target = has_pace_fast and has_pace_slow

        if has_hr_target and has_pace_target:
            raise ValueError("A step cannot have both heart-rate " "and pace targets.")

        # Backward compatibility with the writer
        # format we already deployed.
        if self.target_type == "open":
            if has_hr_target:
                self.target_type = "heart_rate"

            elif has_pace_target:
                self.target_type = "pace"

        if self.target_type == "heart_rate":
            if not has_hr_target:
                raise ValueError(
                    "heart_rate target_type requires "
                    "heart_rate_min_bpm and "
                    "heart_rate_max_bpm."
                )

            if has_pace_target:
                raise ValueError(
                    "heart_rate target_type cannot " "include a pace target."
                )

        elif self.target_type == "pace":
            if not has_pace_target:
                raise ValueError("pace target_type requires both " "pace range fields.")

            if has_hr_target:
                raise ValueError(
                    "pace target_type cannot include " "a heart-rate target."
                )

        return self


class RepeatWorkoutBlock(BaseModel):
    kind: Literal["repeat"] = "repeat"

    repetitions: int = Field(
        ge=2,
        le=20,
    )

    steps: list[WorkoutStep] = Field(
        min_length=1,
        max_length=4,
    )

    @field_validator("steps")
    @classmethod
    def validate_repeat_steps(
        cls,
        steps: list[WorkoutStep],
    ) -> list[WorkoutStep]:
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
    WorkoutStep | RepeatWorkoutBlock,
    Field(discriminator="kind"),
]

# Keeps old scripts/imports working.
TimedWorkoutStep = WorkoutStep


class WorkoutDraftRequest(BaseModel):
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
    draft_id: UUID

    draft: WorkoutDraftRequest

    estimated_duration_seconds: int | None = Field(
        default=None,
        gt=0,
    )

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

    estimated_duration_seconds: int | None = Field(
        default=None,
        gt=0,
    )

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
