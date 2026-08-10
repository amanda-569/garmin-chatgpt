from __future__ import annotations

from garminconnect.workout import (
    ExecutableStep,
    RepeatGroup,
    RunningWorkout,
    WorkoutSegment,
    create_cooldown_step,
    create_interval_step,
    create_recovery_step,
    create_repeat_group,
    create_warmup_step,
)

from app.workout_models import (
    RepeatWorkoutBlock,
    TimedWorkoutStep,
    WorkoutDraftRequest,
)

RUNNING_SPORT = {
    "sportTypeId": 1,
    "sportTypeKey": "running",
}

HEART_RATE_TARGET = {
    "workoutTargetTypeId": 4,
    "workoutTargetTypeKey": "heart.rate.zone",
    "displayOrder": 4,
}


def _apply_heart_rate_target(
    garmin_step: ExecutableStep,
    step: TimedWorkoutStep,
) -> ExecutableStep:
    """
    Add Garmin's explicit BPM target fields when the
    draft step contains a heart-rate range.
    """
    if step.heart_rate_min_bpm is None or step.heart_rate_max_bpm is None:
        return garmin_step

    data = garmin_step.model_dump()

    data["targetType"] = HEART_RATE_TARGET
    data["targetValueOne"] = float(step.heart_rate_min_bpm)
    data["targetValueTwo"] = float(step.heart_rate_max_bpm)
    data["zoneNumber"] = None

    return ExecutableStep(**data)


def _build_timed_step(
    step: TimedWorkoutStep,
    step_order: int,
) -> ExecutableStep:
    """
    Convert one safe internal step into Garmin's format.
    """
    if step.kind == "warmup":
        garmin_step = create_warmup_step(
            duration_seconds=step.duration_seconds,
            step_order=step_order,
        )

    elif step.kind == "interval":
        garmin_step = create_interval_step(
            duration_seconds=step.duration_seconds,
            step_order=step_order,
        )

    elif step.kind == "recovery":
        garmin_step = create_recovery_step(
            duration_seconds=step.duration_seconds,
            step_order=step_order,
        )

    elif step.kind == "cooldown":
        garmin_step = create_cooldown_step(
            duration_seconds=step.duration_seconds,
            step_order=step_order,
        )

    else:
        raise ValueError(f"Unsupported workout step: " f"{step.kind}")

    return _apply_heart_rate_target(
        garmin_step,
        step,
    )


def _build_repeat_block(
    block: RepeatWorkoutBlock,
    step_order: int,
) -> RepeatGroup:
    """
    Convert a safe repeat block into Garmin's repeat format.

    Child step numbering starts again at 1 inside the block.
    """
    child_steps = [
        _build_timed_step(
            step,
            child_order,
        )
        for child_order, step in enumerate(
            block.steps,
            start=1,
        )
    ]

    return create_repeat_group(
        iterations=block.repetitions,
        workout_steps=child_steps,
        step_order=step_order,
    )


def calculate_workout_duration(
    draft: WorkoutDraftRequest,
) -> int:
    """Calculate the total workout duration."""
    total_seconds = 0

    for step in draft.steps:
        if isinstance(step, TimedWorkoutStep):
            total_seconds += step.duration_seconds
        else:
            repeat_duration = sum(child.duration_seconds for child in step.steps)

            total_seconds += step.repetitions * repeat_duration

    return total_seconds


def build_running_workout(
    draft: WorkoutDraftRequest,
) -> RunningWorkout:
    """
    Convert a validated draft into Garmin's RunningWorkout.

    This function only builds the object. It does not upload or
    schedule anything.
    """
    garmin_steps: list[ExecutableStep | RepeatGroup] = []

    for step_order, step in enumerate(
        draft.steps,
        start=1,
    ):
        if isinstance(step, TimedWorkoutStep):
            garmin_step = _build_timed_step(
                step,
                step_order,
            )
        else:
            garmin_step = _build_repeat_block(
                step,
                step_order,
            )

        garmin_steps.append(garmin_step)

    estimated_duration = calculate_workout_duration(draft)

    return RunningWorkout(
        workoutName=draft.name,
        estimatedDurationInSecs=(estimated_duration),
        description=("Created by Garmin Running Coach"),
        workoutSegments=[
            WorkoutSegment(
                segmentOrder=1,
                sportType=RUNNING_SPORT,
                workoutSteps=garmin_steps,
            )
        ],
    )
