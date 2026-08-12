from datetime import datetime, timezone
from typing import Any

from app.models import (
    RunDetails,
    RunSummary,
    RunWeather,
    HeartRateZone,
    RunLap,
    PlannedWorkoutStep,
    PlannedWorkout,
)


def get_activity_summary(
    raw_activity: dict[str, Any],
) -> dict[str, Any]:
    summary = raw_activity.get("summaryDTO")

    if isinstance(summary, dict):
        return summary

    return raw_activity


def parse_garmin_start_time(
    raw_activity: dict[str, Any],
) -> datetime:
    summary = get_activity_summary(raw_activity)

    started_at = parse_garmin_datetime(summary.get("startTimeGMT"))

    if started_at is None:
        raise ValueError("Garmin activity did not contain startTimeGMT")

    return started_at


def parse_garmin_datetime(
    raw_value: str | None,
) -> datetime | None:
    if not raw_value:
        return None

    parsed_value = datetime.fromisoformat(raw_value.replace("Z", "+00:00"))

    if parsed_value.tzinfo is None:
        parsed_value = parsed_value.replace(tzinfo=timezone.utc)

    return parsed_value.astimezone(timezone.utc)


def calculate_pace_seconds_per_km(
    distance_meters: float | None,
    duration_seconds: float | None,
) -> float | None:
    if distance_meters is None or duration_seconds is None or distance_meters <= 0:
        return None

    distance_kilometers = distance_meters / 1000

    return duration_seconds / distance_kilometers


def map_garmin_lap(
    raw_lap: dict[str, Any],
) -> RunLap:
    distance_meters = float(raw_lap.get("distance") or 0)
    duration_seconds = float(raw_lap.get("duration") or 0)

    return RunLap(
        lap_index=raw_lap["lapIndex"],
        started_at=parse_garmin_datetime(raw_lap.get("startTimeGMT")),
        intensity_type=raw_lap.get("intensityType"),
        workout_step_index=raw_lap.get("wktStepIndex"),
        distance_meters=distance_meters,
        duration_seconds=duration_seconds,
        moving_duration_seconds=raw_lap.get("movingDuration"),
        average_pace_seconds_per_km=(
            calculate_pace_seconds_per_km(
                distance_meters,
                duration_seconds,
            )
        ),
        average_heart_rate=raw_lap.get("averageHR"),
        maximum_heart_rate=raw_lap.get("maxHR"),
        average_cadence_spm=raw_lap.get("averageRunCadence"),
        average_ground_contact_time_ms=raw_lap.get("groundContactTime"),
        average_stride_length_m=(
            convert_stride_length_to_meters(raw_lap.get("strideLength"))
        ),
        average_vertical_oscillation_cm=raw_lap.get("verticalOscillation"),
        average_vertical_ratio_percent=raw_lap.get("verticalRatio"),
        elevation_gain_meters=raw_lap.get("elevationGain"),
        workout_compliance_percent=raw_lap.get("directWorkoutComplianceScore"),
    )


def map_garmin_laps(
    raw_splits: dict[str, Any] | None,
) -> list[RunLap]:
    if not raw_splits:
        return []

    raw_laps = raw_splits.get("lapDTOs")

    if not isinstance(raw_laps, list):
        return []

    return [
        map_garmin_lap(raw_lap) for raw_lap in raw_laps if isinstance(raw_lap, dict)
    ]


def map_garmin_activity_to_run(
    raw_activity: dict[str, Any],
) -> RunSummary:
    summary = get_activity_summary(raw_activity)

    return RunSummary(
        activity_id=raw_activity["activityId"],
        name=raw_activity["activityName"],
        started_at=parse_garmin_start_time(raw_activity),
        distance_meters=summary["distance"],
        duration_seconds=summary["duration"],
        average_heart_rate=summary.get("averageHR"),
        maximum_heart_rate=summary.get("maxHR"),
    )


def map_garmin_activity_to_run_details(
    raw_activity: dict[str, Any],
    raw_weather: dict[str, Any] | None = None,
    raw_splits: dict[str, Any] | None = None,
    raw_hr_zones: list[dict[str, Any]] | None = None,
    raw_workout: dict[str, Any] | None = None,
    temperature_unit: str = "celsius",
) -> RunDetails:
    summary = get_activity_summary(raw_activity)
    run_summary = map_garmin_activity_to_run(raw_activity)

    return RunDetails(
        **run_summary.model_dump(),
        moving_duration_seconds=summary.get("movingDuration"),
        average_speed_mps=summary.get("averageSpeed"),
        maximum_speed_mps=summary.get("maxSpeed"),
        average_cadence_spm=summary.get("averageRunCadence"),
        average_ground_contact_time_ms=summary.get("groundContactTime"),
        average_stride_length_m=(
            convert_stride_length_to_meters(summary.get("strideLength"))
        ),
        average_vertical_oscillation_cm=summary.get("verticalOscillation"),
        average_vertical_ratio_percent=summary.get("verticalRatio"),
        elevation_gain_meters=summary.get("elevationGain"),
        aerobic_training_effect=summary.get("aerobicTrainingEffect"),
        anaerobic_training_effect=summary.get("anaerobicTrainingEffect"),
        training_load=summary.get("activityTrainingLoad"),
        training_effect_label=summary.get("trainingEffectLabel"),
        vo2_max=summary.get("vO2MaxValue"),
        lap_count=summary.get("lapCount"),
        laps=map_garmin_laps(raw_splits),
        heart_rate_zones=map_garmin_hr_zones(raw_hr_zones),
        weather=map_garmin_weather(
            raw_weather,
            temperature_unit,
        ),
        planned_workout=map_garmin_planned_workout(raw_workout),
    )


def map_garmin_hr_zones(
    raw_hr_zones: list[dict[str, Any]] | None,
) -> list[HeartRateZone]:
    if not raw_hr_zones:
        return []

    total_recorded_seconds = sum(
        float(zone.get("secsInZone") or 0) for zone in raw_hr_zones
    )

    mapped_zones = []

    for raw_zone in raw_hr_zones:
        seconds_in_zone = float(raw_zone.get("secsInZone") or 0)

        if total_recorded_seconds > 0:
            percentage = round(
                seconds_in_zone / total_recorded_seconds * 100,
                1,
            )
        else:
            percentage = 0.0

        mapped_zones.append(
            HeartRateZone(
                zone_number=raw_zone["zoneNumber"],
                seconds_in_zone=seconds_in_zone,
                low_boundary_bpm=raw_zone.get("zoneLowBoundary"),
                percent_of_recorded_hr_time=percentage,
            )
        )

    return mapped_zones


def convert_temperature_to_celsius(
    value: int | float | None,
    source_unit: str,
) -> float | None:
    if value is None:
        return None

    numeric_value = float(value)

    if source_unit == "fahrenheit":
        return round(
            (numeric_value - 32) * 5 / 9,
            1,
        )

    return numeric_value


def convert_speed_to_pace_seconds_per_km(
    speed_mps: int | float | None,
) -> float | None:
    if speed_mps is None:
        return None

    numeric_speed = float(speed_mps)

    if numeric_speed <= 0:
        return None

    return round(1000 / numeric_speed, 1)


def map_garmin_weather(
    raw_weather: dict[str, Any] | None,
    temperature_unit: str,
) -> RunWeather | None:
    if not raw_weather:
        return None

    return RunWeather(
        temperature_celsius=convert_temperature_to_celsius(
            raw_weather.get("temp"),
            temperature_unit,
        ),
        feels_like_celsius=convert_temperature_to_celsius(
            raw_weather.get("apparentTemp"),
            temperature_unit,
        ),
        dew_point_celsius=convert_temperature_to_celsius(
            raw_weather.get("dewPoint"),
            temperature_unit,
        ),
        relative_humidity_percent=raw_weather.get("relativeHumidity"),
        wind_direction_degrees=raw_weather.get("windDirection"),
        wind_direction_compass=raw_weather.get("windDirectionCompassPoint"),
    )


def map_garmin_workout_step(
    raw_step: dict[str, Any],
    execution_index: int | None = None,
) -> PlannedWorkoutStep:
    raw_step_type = raw_step.get("stepType")

    step_order = int(raw_step.get("stepOrder") or 0)

    if isinstance(raw_step_type, dict):
        step_type = raw_step_type.get("stepTypeKey")
    else:
        step_type = None

    garmin_object_type = raw_step.get("type")

    if garmin_object_type == "RepeatGroupDTO":
        raw_child_steps = raw_step.get("workoutSteps")

        if not isinstance(raw_child_steps, list):
            raw_child_steps = []

        group_execution_index = step_order - 1

        child_steps = [
            map_garmin_workout_step(
                raw_child_step,
                execution_index=(group_execution_index + offset),
            )
            for offset, raw_child_step in enumerate(raw_child_steps)
            if isinstance(raw_child_step, dict)
        ]

        return PlannedWorkoutStep(
            step_order=step_order,
            execution_index=None,
            step_type=step_type or "repeat",
            repeat_count=int(raw_step.get("numberOfIterations") or 0),
            child_steps=child_steps,
        )

    raw_end_condition = raw_step.get("endCondition")

    if isinstance(raw_end_condition, dict):
        duration_type = raw_end_condition.get("conditionTypeKey")
    else:
        duration_type = None

    raw_end_value = raw_step.get("endConditionValue")

    duration_seconds = None
    distance_meters = None

    if raw_end_value is not None:
        if duration_type == "time":
            duration_seconds = float(raw_end_value)

        elif duration_type == "distance":
            distance_meters = float(raw_end_value)

    raw_target_type = raw_step.get("targetType")

    resolved_execution_index = (
        execution_index if execution_index is not None else step_order - 1
    )

    if isinstance(raw_target_type, dict):
        garmin_target_type = raw_target_type.get("workoutTargetTypeKey")
    else:
        garmin_target_type = None

    if garmin_target_type == "no.target":
        target_type = "open"
    elif garmin_target_type == "pace.zone":
        target_type = "pace"
    else:
        target_type = garmin_target_type

    target_paces: list[float] = []

    if target_type == "pace":
        first_pace = convert_speed_to_pace_seconds_per_km(
            raw_step.get("targetValueOne")
        )

        second_pace = convert_speed_to_pace_seconds_per_km(
            raw_step.get("targetValueTwo")
        )

        if first_pace is not None:
            target_paces.append(first_pace)

        if second_pace is not None:
            target_paces.append(second_pace)

    target_fast_pace = None
    target_slow_pace = None

    if target_paces:
        target_fast_pace = min(target_paces)
        target_slow_pace = max(target_paces)

    return PlannedWorkoutStep(
        step_order=step_order,
        execution_index=resolved_execution_index,
        step_type=step_type or "unknown",
        duration_type=duration_type,
        duration_seconds=duration_seconds,
        distance_meters=distance_meters,
        target_type=target_type,
        target_pace_fast_seconds_per_km=target_fast_pace,
        target_pace_slow_seconds_per_km=target_slow_pace,
    )


def map_garmin_planned_workout(
    raw_workout: dict[str, Any] | None,
) -> PlannedWorkout | None:
    if not raw_workout:
        return None

    workout_id = raw_workout.get("workoutId")

    if workout_id is None:
        return None

    mapped_steps = []

    raw_segments = raw_workout.get("workoutSegments")

    if isinstance(raw_segments, list):
        for raw_segment in raw_segments:
            if not isinstance(
                raw_segment,
                dict,
            ):
                continue

            raw_steps = raw_segment.get("workoutSteps")

            if not isinstance(raw_steps, list):
                continue

            for raw_step in raw_steps:
                if isinstance(raw_step, dict):
                    mapped_steps.append(map_garmin_workout_step(raw_step))

    return PlannedWorkout(
        workout_id=int(workout_id),
        name=raw_workout.get("workoutName") or "Unnamed workout",
        estimated_duration_seconds=(raw_workout.get("estimatedDurationInSecs")),
        estimated_distance_meters=(raw_workout.get("estimatedDistanceInMeters")),
        steps=mapped_steps,
    )


def convert_stride_length_to_meters(
    value: int | float | None,
) -> float | None:
    if value is None:
        return None

    return round(
        float(value) / 100,
        3,
    )
