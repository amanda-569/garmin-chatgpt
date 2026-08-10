from __future__ import annotations
from datetime import datetime, date
from pydantic import BaseModel, Field


class RunSummary(BaseModel):
    activity_id: int
    name: str
    started_at: datetime
    distance_meters: float
    duration_seconds: float
    average_heart_rate: float | None = None
    maximum_heart_rate: float | None = None


class RunWeather(BaseModel):
    temperature_celsius: float | None = None
    feels_like_celsius: float | None = None
    dew_point_celsius: float | None = None
    relative_humidity_percent: float | None = None
    wind_direction_degrees: float | None = None
    wind_direction_compass: str | None = None


class RunLap(BaseModel):
    lap_index: int
    started_at: datetime | None = None
    intensity_type: str | None = None
    workout_step_index: int | None = None

    distance_meters: float
    duration_seconds: float
    moving_duration_seconds: float | None = None
    average_pace_seconds_per_km: float | None = None

    average_heart_rate: float | None = None
    maximum_heart_rate: float | None = None
    average_cadence_spm: float | None = None

    elevation_gain_meters: float | None = None
    workout_compliance_percent: float | None = None


class HeartRateZone(BaseModel):
    zone_number: int
    seconds_in_zone: float
    low_boundary_bpm: int | None = None
    percent_of_recorded_hr_time: float


class PlannedWorkoutStep(BaseModel):
    step_order: int
    step_type: str

    duration_type: str | None = None
    duration_seconds: float | None = None
    distance_meters: float | None = None

    repeat_count: int | None = None

    target_type: str | None = None
    target_pace_fast_seconds_per_km: float | None = None
    target_pace_slow_seconds_per_km: float | None = None

    execution_index: int | None = None

    child_steps: list[PlannedWorkoutStep] = Field(default_factory=list)


class PlannedWorkout(BaseModel):
    workout_id: int
    name: str

    estimated_duration_seconds: float | None = None
    estimated_distance_meters: float | None = None

    steps: list[PlannedWorkoutStep] = Field(default_factory=list)


class RunDetails(RunSummary):
    moving_duration_seconds: float | None = None
    average_speed_mps: float | None = None
    maximum_speed_mps: float | None = None

    planned_workout: PlannedWorkout | None = None

    average_cadence_spm: float | None = None
    elevation_gain_meters: float | None = None

    aerobic_training_effect: float | None = None
    anaerobic_training_effect: float | None = None
    training_load: float | None = None
    training_effect_label: str | None = None

    vo2_max: float | None = None
    lap_count: int | None = None
    laps: list[RunLap] = Field(default_factory=list)
    heart_rate_zones: list[HeartRateZone] = Field(default_factory=list)

    weather: RunWeather | None = None


class IntervalExecution(BaseModel):
    repetition: int

    actual_pace_seconds_per_km: float
    target_fast_seconds_per_km: float
    target_slow_seconds_per_km: float

    seconds_from_target_range: float
    within_target: bool

    average_heart_rate: float | None = None
    maximum_heart_rate: float | None = None
    average_cadence_spm: float | None = None

    workout_compliance_percent: float | None = None


class RunAnalysis(BaseModel):
    activity_id: int
    workout_name: str | None = None

    planned_repetitions: int
    completed_repetitions: int
    completion_percent: float

    average_interval_pace_seconds_per_km: float | None = None
    pace_range_seconds_per_km: float | None = None
    first_to_last_pace_change_percent: float | None = None

    average_interval_heart_rate: float | None = None
    average_interval_cadence_spm: float | None = None

    zone_4_5_percent: float

    intervals: list[IntervalExecution] = Field(default_factory=list)

    warnings: list[str] = Field(default_factory=list)


class RecoveryDay(BaseModel):
    date: date

    sleep_duration_seconds: int | None = None
    sleep_score: int | None = None

    deep_sleep_seconds: int | None = None
    light_sleep_seconds: int | None = None
    rem_sleep_seconds: int | None = None
    awake_seconds: int | None = None
    nap_seconds: int | None = None

    average_sleep_stress: float | None = None

    body_battery_change: int | None = None
    body_battery_charged: int | None = None
    body_battery_drained: int | None = None

    overnight_hrv_ms: float | None = None
    weekly_hrv_ms: float | None = None
    hrv_status: str | None = None
    hrv_baseline_low_ms: float | None = None
    hrv_baseline_high_ms: float | None = None

    resting_heart_rate_bpm: float | None = None

    training_readiness_score: int | None = None
    training_readiness_level: str | None = None

    average_stress_level: int | None = None

    missing_fields: list[str] = Field(default_factory=list)

    warnings: list[str] = Field(default_factory=list)


class CycleDay(BaseModel):
    date: date

    cycle_day: int | None = None
    cycle_type: str | None = None

    phase_code: int | None = None
    days_until_next_phase: int | None = None
    phase_length_days: int | None = None

    period_length_days: int | None = None
    cycle_start_date: date | None = None

    cycle_is_predicted: bool | None = None
    predicted_cycle_length_days: int | None = None

    has_logged_day_data: bool = False

    missing_fields: list[str] = Field(default_factory=list)

    warnings: list[str] = Field(default_factory=list)


class ActivitySummary(BaseModel):
    activity_id: int
    activity_type: str
    name: str
    started_at: datetime

    distance_meters: float | None = None
    duration_seconds: float | None = None

    average_heart_rate: float | None = None
    maximum_heart_rate: float | None = None

    elevation_gain_meters: float | None = None
