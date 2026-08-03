from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends

from app.models import CycleDay, RecoveryDay
from app.security import verify_api_key
from app.services.health_service import (
    get_cycle_day,
    get_latest_cycle_day,
    get_latest_recovery,
    get_recovery_day,
)

router = APIRouter(
    dependencies=[
        Depends(verify_api_key),
    ],
)


@router.get(
    "/recovery/latest",
    response_model=RecoveryDay,
    operation_id="getLatestRecovery",
    tags=["recovery"],
    summary="Get latest recovery data",
    description=(
        "Returns normalized Garmin sleep, HRV, "
        "resting-heart-rate, Body Battery, stress, "
        "and training-readiness data for the current "
        "local date."
    ),
)
def latest_recovery_route() -> RecoveryDay:
    return get_latest_recovery()


@router.get(
    "/recovery/{target_date}",
    response_model=RecoveryDay,
    operation_id="getRecoveryDay",
    tags=["recovery"],
    summary="Get recovery data by date",
    description=("Returns normalized Garmin recovery data " "for one calendar date."),
)
def recovery_day_route(
    target_date: date,
) -> RecoveryDay:
    return get_recovery_day(target_date)


@router.get(
    "/cycle/latest",
    response_model=CycleDay,
    operation_id="getLatestCycleDay",
    tags=["cycle"],
    summary="Get latest menstrual-cycle context",
    description=(
        "Returns normalized Garmin menstrual-cycle "
        "context for the current local date. "
        "Predicted data is explicitly labelled."
    ),
)
def latest_cycle_day_route() -> CycleDay:
    return get_latest_cycle_day()


@router.get(
    "/cycle/{target_date}",
    response_model=CycleDay,
    operation_id="getCycleDay",
    tags=["cycle"],
    summary="Get menstrual-cycle context by date",
    description=(
        "Returns normalized Garmin menstrual-cycle " "context for one calendar date."
    ),
)
def cycle_day_route(
    target_date: date,
) -> CycleDay:
    return get_cycle_day(target_date)
