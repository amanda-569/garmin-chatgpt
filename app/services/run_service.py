from app.models import RunDetails, RunSummary, RunAnalysis
from app.providers.base import RunProvider
from app.providers.factory import create_run_provider
from app.services.run_analysis_service import analyze_run

provider: RunProvider = create_run_provider()


def list_runs() -> list[RunSummary]:
    return provider.list_runs()


def find_latest_run() -> RunSummary | None:
    runs = provider.list_runs()

    if not runs:
        return None

    return max(runs, key=lambda run: run.started_at)


def find_run_by_id(activity_id: int) -> RunDetails | None:
    return provider.get_run_by_id(activity_id)


def get_run_analysis(
    activity_id: int,
) -> RunAnalysis | None:
    run = find_run_by_id(activity_id)

    if run is None:
        return None

    return analyze_run(run)


def get_latest_run_analysis() -> RunAnalysis | None:
    run = find_latest_run()

    if run is None:
        return None

    run_details = find_run_by_id(run.activity_id)

    if run_details is None:
        return None

    return analyze_run(run_details)
