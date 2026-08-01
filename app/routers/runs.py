from fastapi import APIRouter, HTTPException, Depends
from app.security import verify_api_key

from app.models import RunAnalysis, RunDetails, RunSummary
from app.services.run_service import (
    find_latest_run,
    find_run_by_id,
    get_latest_run_analysis,
    get_run_analysis,
    list_runs,
)

router = APIRouter(
    prefix="/runs",
    tags=["runs"],
    dependencies=[Depends(verify_api_key)],
)


@router.get(
    "",
    response_model=list[RunSummary],
    operation_id="listRuns",
    summary="List recent runs",
    description=(
        "Returns recent running activities as compact summaries. "
        "Use this when the user wants to browse or identify runs."
    ),
)
def get_runs() -> list[RunSummary]:
    return list_runs()


@router.get(
    "/latest",
    response_model=RunSummary,
    operation_id="getLatestRun",
    summary="Get latest run",
    description=(
        "Returns the most recent running activity as a detailed summary. "
        "Use this when the user wants to view the latest run."
    ),
)
def get_latest_run() -> RunSummary:
    run = find_latest_run()

    if run is None:
        raise HTTPException(
            status_code=404,
            detail="Latest run not found",
        )

    return run


@router.get(
    "/latest/analysis",
    response_model=RunAnalysis,
    operation_id="analyzeLatestRun",
    summary="Analyze latest run",
    description=(
        "Compares the latest completed run with its linked planned "
        "workout and returns deterministic interval, pace, heart-rate, "
        "cadence, completion, and target-compliance metrics."
    ),
)
def analyze_latest_run() -> RunAnalysis:
    analysis = get_latest_run_analysis()

    if analysis is None:
        raise HTTPException(
            status_code=404,
            detail="No runs found",
        )

    return analysis


@router.get(
    "/{activity_id}/analysis",
    response_model=RunAnalysis,
    operation_id="analyzeRun",
    summary="Analyze run by activity ID",
    description=(
        "Compares a completed run with its linked planned "
        "workout and returns deterministic analysis."
    ),
)
def analyze_run(activity_id: int) -> RunAnalysis:
    run_analysis = get_run_analysis(activity_id)

    if run_analysis is None:
        raise HTTPException(
            status_code=404,
            detail="Run analysis not found",
        )

    return run_analysis


@router.get(
    "/{activity_id}",
    response_model=RunDetails,
    operation_id="getRunDetails",
    summary="Get complete run details",
    description="Returns complete normalized details for one Garmin run, "
    "including laps, heart-rate zones, weather, and the linked "
    "planned workout.",
)
def get_run(activity_id: int) -> RunDetails:
    run = find_run_by_id(activity_id)

    if run is None:
        raise HTTPException(
            status_code=404,
            detail="Run not found",
        )

    return run
