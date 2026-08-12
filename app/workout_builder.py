from __future__ import annotations

from garminconnect.workout import (
    ConditionType,
    ExecutableStep,
    RepeatGroup,
    RunningWorkout,
    StepType,
    TargetType,
    WorkoutSegment,
    create_repeat_group,
)

from app.workout_models import (
    RepeatWorkoutBlock,
    WorkoutDraftRequest,
    WorkoutStep,
)

RUNNING_SPORT = {
    "sportTypeId": 1,
    "sportTypeKey": "running",
}


STEP_TYPES = {
    "warmup": {
        "stepTypeId": StepType.WARMUP,
        "stepTypeKey": "warmup",
        "displayOrder": 1,
    },
    "cooldown": {
        "stepTypeId": StepType.COOLDOWN,
        "stepTypeKey": "cooldown",
        "displayOrder": 2,
    },
    "interval": {
        "stepTypeId": StepType.INTERVAL,
        "stepTypeKey": "interval",
        "displayOrder": 3,
    },
    "recovery": {
        "stepTypeId": StepType.RECOVERY,
        "stepTypeKey": "recovery",
        "displayOrder": 4,
    },
}


END_CONDITIONS = {
    "lap_button": {
        "conditionTypeId": (ConditionType.LAP_BUTTON),
        "conditionTypeKey": "lap.button",
        "displayOrder": 1,
        "displayable": True,
    },
    "time": {
        "conditionTypeId": (ConditionType.TIME),
        "conditionTypeKey": "time",
        "displayOrder": 2,
        "displayable": True,
    },
    "distance": {
        "conditionTypeId": (ConditionType.DISTANCE),
        "conditionTypeKey": "distance",
        "displayOrder": 3,
        "displayable": True,
    },
}


NO_TARGET = {
    "workoutTargetTypeId": (TargetType.NO_TARGET),
    "workoutTargetTypeKey": "no.target",
    "displayOrder": 1,
}


HEART_RATE_TARGET = {
    "workoutTargetTypeId": (TargetType.HEART_RATE_ZONE),
    "workoutTargetTypeKey": "heart.rate.zone",
    "displayOrder": 4,
}


PACE_TARGET = {
    "workoutTargetTypeId": (TargetType.PACE_ZONE),
    "workoutTargetTypeKey": "pace.zone",
    "displayOrder": 6,
}


def _pace_seconds_per_km_to_speed_mps(
    pace_seconds_per_km: float,
) -> float:
    return 1000.0 / pace_seconds_per_km


def _apply_target(
    garmin_step: ExecutableStep,
    step: WorkoutStep,
) -> ExecutableStep:
    if step.target_type == "open":
        return garmin_step

    data = garmin_step.model_dump()

    if step.target_type == "heart_rate":
        assert step.heart_rate_min_bpm is not None
        assert step.heart_rate_max_bpm is not None

        data["targetType"] = HEART_RATE_TARGET

        data["targetValueOne"] = float(step.heart_rate_min_bpm)

        data["targetValueTwo"] = float(step.heart_rate_max_bpm)

        data["zoneNumber"] = None

    elif step.target_type == "pace":
        assert step.target_pace_fast_seconds_per_km is not None

        assert step.target_pace_slow_seconds_per_km is not None

        slow_speed = _pace_seconds_per_km_to_speed_mps(
            step.target_pace_slow_seconds_per_km
        )

        fast_speed = _pace_seconds_per_km_to_speed_mps(
            step.target_pace_fast_seconds_per_km
        )

        data["targetType"] = PACE_TARGET

        data["targetValueOne"] = slow_speed

        data["targetValueTwo"] = fast_speed

        data["zoneNumber"] = None

    return ExecutableStep(**data)


def _build_step(
    step: WorkoutStep,
    step_order: int,
) -> ExecutableStep:
    if step.end_type == "time":
        assert step.duration_seconds is not None

        end_value: float | None = float(step.duration_seconds)

    elif step.end_type == "distance":
        assert step.distance_meters is not None

        end_value = float(step.distance_meters)

    else:
        end_value = None

    garmin_step = ExecutableStep(
        stepOrder=step_order,
        stepType=STEP_TYPES[step.kind],
        endCondition=(END_CONDITIONS[step.end_type]),
        endConditionValue=end_value,
        targetType=NO_TARGET,
    )

    return _apply_target(
        garmin_step,
        step,
    )


def _build_repeat_block(
    block: RepeatWorkoutBlock,
    step_order: int,
) -> tuple[RepeatGroup, int]:
    child_steps: list[ExecutableStep] = []

    next_order = step_order + 1

    for step in block.steps:
        child_steps.append(
            _build_step(
                step,
                next_order,
            )
        )

        next_order += 1

    group = create_repeat_group(
        iterations=block.repetitions,
        workout_steps=child_steps,
        step_order=step_order,
    )

    return group, next_order


def _estimate_step_duration(
    step: WorkoutStep,
) -> int | None:
    if step.end_type == "time":
        return step.duration_seconds

    if (
        step.end_type == "distance"
        and step.distance_meters is not None
        and step.target_pace_fast_seconds_per_km is not None
        and step.target_pace_slow_seconds_per_km is not None
    ):
        average_pace = (
            step.target_pace_fast_seconds_per_km + step.target_pace_slow_seconds_per_km
        ) / 2

        estimated_seconds = step.distance_meters / 1000.0 * average_pace

        return max(
            1,
            round(estimated_seconds),
        )

    return None


def calculate_workout_duration(
    draft: WorkoutDraftRequest,
) -> int | None:
    total_seconds = 0

    for step in draft.steps:
        if isinstance(
            step,
            WorkoutStep,
        ):
            step_duration = _estimate_step_duration(step)

            if step_duration is None:
                return None

            total_seconds += step_duration

        else:
            repeat_duration = 0

            for child in step.steps:
                child_duration = _estimate_step_duration(child)

                if child_duration is None:
                    return None

                repeat_duration += child_duration

            total_seconds += step.repetitions * repeat_duration

    return total_seconds


def calculate_known_workout_duration(
    draft: WorkoutDraftRequest,
) -> int:
    """
    Calculate the duration of all workout portions
    that can be estimated.

    Unknown distance or lap-button steps contribute
    zero rather than making the entire estimate zero.
    """
    total_seconds = 0

    for step in draft.steps:
        if isinstance(
            step,
            WorkoutStep,
        ):
            step_duration = _estimate_step_duration(step)

            if step_duration is not None:
                total_seconds += step_duration

        else:
            repeat_duration = 0

            for child in step.steps:
                child_duration = _estimate_step_duration(child)

                if child_duration is not None:
                    repeat_duration += child_duration

            total_seconds += step.repetitions * repeat_duration

    return total_seconds


def build_running_workout(
    draft: WorkoutDraftRequest,
) -> RunningWorkout:
    garmin_steps: list[ExecutableStep | RepeatGroup] = []

    next_order = 1

    for step in draft.steps:
        if isinstance(
            step,
            WorkoutStep,
        ):
            garmin_steps.append(
                _build_step(
                    step,
                    next_order,
                )
            )

            next_order += 1

        else:
            (
                repeat_group,
                next_order,
            ) = _build_repeat_block(
                step,
                next_order,
            )

            garmin_steps.append(repeat_group)

    estimated_duration = calculate_workout_duration(draft)

    garmin_estimated_duration = (
        estimated_duration
        if estimated_duration is not None
        else calculate_known_workout_duration(draft)
    )
    return RunningWorkout(
        workoutName=draft.name,
        estimatedDurationInSecs=(garmin_estimated_duration),
        description=("Created by Garmin Running Coach"),
        workoutSegments=[
            WorkoutSegment(
                segmentOrder=1,
                sportType=RUNNING_SPORT,
                workoutSteps=garmin_steps,
            )
        ],
    )
