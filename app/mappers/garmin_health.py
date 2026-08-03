from __future__ import annotations

from datetime import date
from typing import Any

from app.models import CycleDay, RecoveryDay


def _as_dict(value: Any) -> dict[str, Any]:
    """
    Return the value when it is a dictionary.

    Garmin occasionally returns null or a differently shaped
    payload when data is unavailable.
    """
    if isinstance(value, dict):
        return value

    return {}


def _as_list(value: Any) -> list[Any]:
    """Return the value when it is a list."""
    if isinstance(value, list):
        return value

    return []


def _get_nested(
    payload: dict[str, Any],
    *keys: str,
) -> Any:
    """
    Safely traverse nested dictionaries.

    Example:
        _get_nested(
            payload,
            "dailySleepDTO",
            "sleepScores",
            "overall",
            "value",
        )
    """
    current: Any = payload

    for key in keys:
        if not isinstance(current, dict):
            return None

        current = current.get(key)

    return current


def _first_list_item(value: Any) -> Any:
    """Return the first list item, or None."""
    items = _as_list(value)

    if not items:
        return None

    return items[0]


def _first_non_none(*values: Any) -> Any:
    """
    Return the first value that is not None.

    We cannot use `or` here because zero could be a valid
    measured value.
    """
    for value in values:
        if value is not None:
            return value

    return None


def _parse_date(value: Any) -> date | None:
    """Convert a Garmin date string into a date."""
    if isinstance(value, date):
        return value

    if not isinstance(value, str):
        return None

    try:
        # Garmin calendar dates normally use YYYY-MM-DD.
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def _find_missing_fields(
    values: dict[str, Any],
    field_names: tuple[str, ...],
) -> list[str]:
    """List requested fields whose mapped values are missing."""
    return [field_name for field_name in field_names if values.get(field_name) is None]


def map_garmin_recovery_day(
    *,
    target_date: date,
    sleep_payload: dict[str, Any] | None,
    hrv_payload: dict[str, Any] | None,
    resting_heart_rate_payload: dict[str, Any] | None,
    training_readiness_payload: dict[str, Any] | None,
    body_battery_payload: list[dict[str, Any]] | None,
    stress_payload: dict[str, Any] | None,
) -> RecoveryDay:
    """
    Normalize Garmin sleep and recovery payloads.

    This mapper intentionally keeps only fields that are useful
    for coaching decisions. It excludes raw timelines, feedback
    text, user IDs, and device IDs.
    """
    sleep = _as_dict(sleep_payload)
    sleep_dto = _as_dict(sleep.get("dailySleepDTO"))

    hrv = _as_dict(hrv_payload)
    hrv_summary = _as_dict(hrv.get("hrvSummary"))
    hrv_baseline = _as_dict(hrv_summary.get("baseline"))

    resting_heart_rate = _as_dict(resting_heart_rate_payload)

    resting_heart_rate_records = _get_nested(
        resting_heart_rate,
        "allMetrics",
        "metricsMap",
        "WELLNESS_RESTING_HEART_RATE",
    )

    resting_heart_rate_record = _as_dict(_first_list_item(resting_heart_rate_records))

    readiness = _as_dict(training_readiness_payload)

    body_battery_day = _as_dict(_first_list_item(body_battery_payload))

    stress = _as_dict(stress_payload)

    values: dict[str, Any] = {
        "date": target_date,
        "sleep_duration_seconds": (sleep_dto.get("sleepTimeSeconds")),
        "sleep_score": _get_nested(
            sleep_dto,
            "sleepScores",
            "overall",
            "value",
        ),
        "deep_sleep_seconds": (sleep_dto.get("deepSleepSeconds")),
        "light_sleep_seconds": (sleep_dto.get("lightSleepSeconds")),
        "rem_sleep_seconds": (sleep_dto.get("remSleepSeconds")),
        "awake_seconds": (sleep_dto.get("awakeSleepSeconds")),
        "nap_seconds": (sleep_dto.get("napTimeSeconds")),
        "average_sleep_stress": (sleep_dto.get("avgSleepStress")),
        "body_battery_change": (sleep.get("bodyBatteryChange")),
        "body_battery_charged": (body_battery_day.get("charged")),
        "body_battery_drained": (body_battery_day.get("drained")),
        "overnight_hrv_ms": _first_non_none(
            hrv_summary.get("lastNightAvg"),
            sleep.get("avgOvernightHrv"),
        ),
        "weekly_hrv_ms": (hrv_summary.get("weeklyAvg")),
        "hrv_status": _first_non_none(
            hrv_summary.get("status"),
            sleep.get("hrvStatus"),
        ),
        "hrv_baseline_low_ms": (hrv_baseline.get("balancedLow")),
        "hrv_baseline_high_ms": (hrv_baseline.get("balancedUpper")),
        "resting_heart_rate_bpm": (resting_heart_rate_record.get("value")),
        "training_readiness_score": (readiness.get("score")),
        "training_readiness_level": (readiness.get("level")),
        "average_stress_level": (stress.get("avgStressLevel")),
    }

    tracked_fields = (
        "sleep_duration_seconds",
        "sleep_score",
        "deep_sleep_seconds",
        "light_sleep_seconds",
        "rem_sleep_seconds",
        "awake_seconds",
        "nap_seconds",
        "average_sleep_stress",
        "body_battery_change",
        "body_battery_charged",
        "body_battery_drained",
        "overnight_hrv_ms",
        "weekly_hrv_ms",
        "hrv_status",
        "hrv_baseline_low_ms",
        "hrv_baseline_high_ms",
        "resting_heart_rate_bpm",
        "training_readiness_score",
        "training_readiness_level",
        "average_stress_level",
    )

    warnings: list[str] = []

    sleep_calendar_date = _parse_date(sleep_dto.get("calendarDate"))

    if sleep_calendar_date is not None and sleep_calendar_date != target_date:
        warnings.append(
            "Garmin sleep data was returned for a " "different calendar date."
        )

    hrv_calendar_date = _parse_date(hrv_summary.get("calendarDate"))

    if hrv_calendar_date is not None and hrv_calendar_date != target_date:
        warnings.append(
            "Garmin HRV data was returned for a " "different calendar date."
        )

    if readiness.get("validSleep") is False:
        warnings.append(
            "Garmin marked the sleep input used for " "training readiness as invalid."
        )

    values["missing_fields"] = _find_missing_fields(
        values,
        tracked_fields,
    )

    values["warnings"] = warnings

    return RecoveryDay.model_validate(values)


def map_garmin_cycle_day(
    *,
    target_date: date,
    menstrual_payload: dict[str, Any] | None,
) -> CycleDay:
    """
    Normalize Garmin menstrual-cycle data.

    Fertility-window fields are intentionally excluded because
    they are unnecessary for running-coaching decisions.
    """
    menstrual = _as_dict(menstrual_payload)

    summary = _as_dict(menstrual.get("daySummary"))

    day_log = menstrual.get("dayLog")

    values: dict[str, Any] = {
        "date": target_date,
        "cycle_day": (summary.get("dayInCycle")),
        "cycle_type": (summary.get("cycleType")),
        "phase_code": (summary.get("currentPhase")),
        "days_until_next_phase": (summary.get("daysUntilNextPhase")),
        "phase_length_days": (summary.get("lengthOfCurrentPhase")),
        "period_length_days": (summary.get("periodLength")),
        "cycle_start_date": _parse_date(summary.get("startDate")),
        "cycle_is_predicted": (summary.get("predictedCycle")),
        "predicted_cycle_length_days": (summary.get("predictedCycleLength")),
        "has_logged_day_data": (day_log is not None),
    }

    tracked_fields = (
        "cycle_day",
        "cycle_type",
        "phase_code",
        "days_until_next_phase",
        "phase_length_days",
        "period_length_days",
        "cycle_start_date",
        "cycle_is_predicted",
        "predicted_cycle_length_days",
    )

    warnings: list[str] = []

    if values["cycle_is_predicted"] is True:
        warnings.append(
            "Garmin marked this cycle as predicted. "
            "Cycle phase should be treated as an "
            "estimate, not a confirmed hormonal state."
        )

    values["missing_fields"] = _find_missing_fields(
        values,
        tracked_fields,
    )

    values["warnings"] = warnings

    return CycleDay.model_validate(values)
