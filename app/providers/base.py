from abc import ABC, abstractmethod

from app.models import RunDetails, RunSummary


class RunProvider(ABC):
    @abstractmethod
    def list_runs(self) -> list[RunSummary]:
        pass

    @abstractmethod
    def get_run_by_id(self, activity_id: int) -> RunDetails | None:
        pass
