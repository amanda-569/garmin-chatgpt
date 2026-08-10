from __future__ import annotations

from datetime import date

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)

from app.models import ActivitySummary
from app.security import verify_api_key
from app.services.activity_service import (
    list_activities,
)

router = APIRouter(
    prefix="/activities",
    tags=["activities"],
    dependencies=[
        Depends(verify_api_key),
    ],
)


@router.get(
    "",
    response_model=list[ActivitySummary],
    operation_id="listActivities",
    summary="List Garmin activities",
    description=(
        "Returns compact Garmin activity summaries "
        "for a date range. Includes running, hiking, "
        "cycling, walking, and other recorded activity "
        "types. Optionally filters by activity type."
    ),
)
def list_activities_route(
    start_date: date = Query(...),
    end_date: date = Query(...),
    activity_type: str | None = Query(default=None),
) -> list[ActivitySummary]:
    try:
        return list_activities(
            start_date=start_date,
            end_date=end_date,
            activity_type=activity_type,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc
