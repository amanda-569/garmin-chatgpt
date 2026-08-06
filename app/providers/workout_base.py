from __future__ import annotations

from datetime import date
from typing import Any, Protocol, runtime_checkable

from garminconnect.workout import RunningWorkout


@runtime_checkable
class WorkoutWriteProvider(Protocol):
    def upload_running_workout(
        self,
        workout: RunningWorkout,
    ) -> dict[str, Any]: ...

    def schedule_workout(
        self,
        workout_id: int,
        scheduled_date: date,
    ) -> dict[str, Any]: ...
