from statistics import mean

from app.models import (
    IntervalExecution,
    PlannedWorkoutStep,
    RunAnalysis,
    RunDetails,
)


def find_interval_candidate(
    steps: list[PlannedWorkoutStep],
    pace_target_only: bool,
    repeat_count: int | None = None,
) -> tuple[PlannedWorkoutStep, int] | None:
    fallback_result: (
        tuple[
            PlannedWorkoutStep,
            int,
        ]
        | None
    ) = None

    for step in steps:
        active_repeat_count = (
            step.repeat_count if step.repeat_count is not None else repeat_count
        )

        nested_result = find_interval_candidate(
            step.child_steps,
            pace_target_only=pace_target_only,
            repeat_count=active_repeat_count,
        )

        if nested_result is not None:
            nested_step, nested_repetitions = nested_result

            if nested_repetitions > 1:
                return nested_result

            if fallback_result is None:
                fallback_result = nested_result

        is_interval = step.step_type == "interval" and step.execution_index is not None

        if not is_interval:
            continue

        has_pace_target = (
            step.target_type == "pace"
            and step.target_pace_fast_seconds_per_km is not None
            and step.target_pace_slow_seconds_per_km is not None
        )

        if pace_target_only and not has_pace_target:
            continue

        repetitions = active_repeat_count or 1

        result = (
            step,
            repetitions,
        )

        if repetitions > 1:
            return result

        if fallback_result is None:
            fallback_result = result

    return fallback_result


def find_planned_interval(
    steps: list[PlannedWorkoutStep],
) -> tuple[PlannedWorkoutStep, int] | None:
    pace_interval = find_interval_candidate(
        steps,
        pace_target_only=True,
    )

    if pace_interval is not None:
        return pace_interval

    return find_interval_candidate(
        steps,
        pace_target_only=False,
    )


def calculate_target_deviation(
    actual_pace: float,
    target_fast_pace: float,
    target_slow_pace: float,
) -> float:
    if actual_pace < target_fast_pace:
        return round(
            actual_pace - target_fast_pace,
            1,
        )

    if actual_pace > target_slow_pace:
        return round(
            actual_pace - target_slow_pace,
            1,
        )

    return 0.0


def average_optional_values(
    values: list[float | None],
    digits: int = 1,
) -> float | None:
    available_values = [float(value) for value in values if value is not None]

    if not available_values:
        return None

    return round(
        mean(available_values),
        digits,
    )


def calculate_zone_4_5_percent(
    run: RunDetails,
) -> float:
    total_percent = sum(
        zone.percent_of_recorded_hr_time
        for zone in run.heart_rate_zones
        if zone.zone_number in {4, 5}
    )

    return round(total_percent, 1)


def calculate_first_to_last_percent_change(
    values: list[float | None],
) -> float | None:
    if len(values) < 2:
        return None

    first = values[0]
    last = values[-1]

    if first is None or last is None:
        return None

    if first == 0:
        return None

    return round(
        (last - first) / first * 100,
        1,
    )


def analyze_run(
    run: RunDetails,
) -> RunAnalysis:
    warnings: list[str] = []

    zone_4_5_percent = calculate_zone_4_5_percent(run)

    if run.planned_workout is None:
        return RunAnalysis(
            activity_id=run.activity_id,
            workout_name=None,
            planned_repetitions=0,
            completed_repetitions=0,
            completion_percent=0.0,
            zone_4_5_percent=zone_4_5_percent,
            warnings=["This activity was not linked " "to a planned workout."],
        )

    planned_interval_result = find_planned_interval(run.planned_workout.steps)

    if planned_interval_result is None:
        return RunAnalysis(
            activity_id=run.activity_id,
            workout_name=run.planned_workout.name,
            planned_repetitions=0,
            completed_repetitions=0,
            completion_percent=0.0,
            zone_4_5_percent=zone_4_5_percent,
            warnings=["No planned interval " "was found in this workout."],
        )

    planned_step, planned_repetitions = planned_interval_result

    matching_laps = [
        lap
        for lap in run.laps
        if lap.workout_step_index == planned_step.execution_index
    ]

    completed_repetitions = len(matching_laps)

    if completed_repetitions < planned_repetitions:
        warnings.append("Fewer completed repetitions were " "found than planned.")

    if completed_repetitions > planned_repetitions:
        warnings.append("More completed repetitions were " "found than planned.")

    target_fast_pace = planned_step.target_pace_fast_seconds_per_km

    target_slow_pace = planned_step.target_pace_slow_seconds_per_km

    has_pace_target = target_fast_pace is not None and target_slow_pace is not None

    intervals: list[IntervalExecution] = []

    for repetition, lap in enumerate(
        matching_laps,
        start=1,
    ):
        actual_pace = lap.average_pace_seconds_per_km

        if actual_pace is None:
            warnings.append(f"Repetition {repetition} " "did not contain pace data.")
            continue

        seconds_from_target = None
        within_target = None

        if has_pace_target:
            seconds_from_target = calculate_target_deviation(
                actual_pace=actual_pace,
                target_fast_pace=target_fast_pace,
                target_slow_pace=target_slow_pace,
            )

            within_target = target_fast_pace <= actual_pace <= target_slow_pace

        intervals.append(
            IntervalExecution(
                repetition=repetition,
                actual_pace_seconds_per_km=round(
                    actual_pace,
                    1,
                ),
                target_fast_seconds_per_km=(target_fast_pace),
                target_slow_seconds_per_km=(target_slow_pace),
                seconds_from_target_range=(seconds_from_target),
                within_target=within_target,
                average_heart_rate=(lap.average_heart_rate),
                maximum_heart_rate=(lap.maximum_heart_rate),
                average_cadence_spm=(lap.average_cadence_spm),
                average_ground_contact_time_ms=(lap.average_ground_contact_time_ms),
                average_stride_length_m=(lap.average_stride_length_m),
                average_vertical_oscillation_cm=(lap.average_vertical_oscillation_cm),
                average_vertical_ratio_percent=(lap.average_vertical_ratio_percent),
                workout_compliance_percent=(lap.workout_compliance_percent),
            )
        )

    interval_paces = [interval.actual_pace_seconds_per_km for interval in intervals]

    average_interval_pace = None
    pace_range = None
    first_to_last_change = None

    if interval_paces:
        average_interval_pace = round(
            mean(interval_paces),
            1,
        )

        pace_range = round(
            max(interval_paces) - min(interval_paces),
            1,
        )

    if len(interval_paces) >= 2 and interval_paces[0] > 0:
        first_to_last_change = round(
            (interval_paces[-1] - interval_paces[0]) / interval_paces[0] * 100,
            1,
        )

    # Running mechanics for the matched work intervals

    ground_contact_times = [lap.average_ground_contact_time_ms for lap in matching_laps]

    stride_lengths = [lap.average_stride_length_m for lap in matching_laps]

    vertical_oscillations = [
        lap.average_vertical_oscillation_cm for lap in matching_laps
    ]

    vertical_ratios = [lap.average_vertical_ratio_percent for lap in matching_laps]

    first_to_last_ground_contact_change = calculate_first_to_last_percent_change(
        ground_contact_times
    )

    first_to_last_stride_length_change = calculate_first_to_last_percent_change(
        stride_lengths
    )

    first_to_last_vertical_ratio_change = calculate_first_to_last_percent_change(
        vertical_ratios
    )

    if planned_repetitions > 0:
        completion_percent = round(
            completed_repetitions / planned_repetitions * 100,
            1,
        )
    else:
        completion_percent = 0.0

    return RunAnalysis(
        activity_id=run.activity_id,
        workout_name=run.planned_workout.name,
        planned_repetitions=planned_repetitions,
        completed_repetitions=(completed_repetitions),
        completion_percent=completion_percent,
        average_interval_pace_seconds_per_km=(average_interval_pace),
        pace_range_seconds_per_km=pace_range,
        first_to_last_pace_change_percent=(first_to_last_change),
        average_interval_heart_rate=(
            average_optional_values([lap.average_heart_rate for lap in matching_laps])
        ),
        average_interval_cadence_spm=(
            average_optional_values([lap.average_cadence_spm for lap in matching_laps])
        ),
        average_interval_ground_contact_time_ms=(
            average_optional_values(ground_contact_times)
        ),
        average_interval_stride_length_m=(
            average_optional_values(
                stride_lengths,
                digits=3,
            )
        ),
        average_interval_vertical_oscillation_cm=(
            average_optional_values(vertical_oscillations)
        ),
        average_interval_vertical_ratio_percent=(
            average_optional_values(vertical_ratios)
        ),
        first_to_last_ground_contact_time_change_percent=(
            first_to_last_ground_contact_change
        ),
        first_to_last_stride_length_change_percent=(first_to_last_stride_length_change),
        first_to_last_vertical_ratio_change_percent=(
            first_to_last_vertical_ratio_change
        ),
        zone_4_5_percent=zone_4_5_percent,
        intervals=intervals,
        warnings=warnings,
    )
