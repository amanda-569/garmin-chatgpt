from __future__ import annotations
from datetime import datetime
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
