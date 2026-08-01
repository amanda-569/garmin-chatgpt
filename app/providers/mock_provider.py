from app.mock_data import MOCK_RUNS
from app.models import RunDetails, RunSummary
from app.providers.base import RunProvider


class MockRunProvider(RunProvider):
    def list_runs(self) -> list[RunSummary]:
        return list(MOCK_RUNS)

    def get_run_by_id(self, activity_id: int) -> RunDetails | None:
        for run in MOCK_RUNS:
            if run.activity_id == activity_id:
                return RunDetails(**run.model_dump())

        return None
