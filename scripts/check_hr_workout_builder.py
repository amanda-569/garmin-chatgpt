from __future__ import annotations

import json
from datetime import date, timedelta

from app.workout_builder import (
    build_running_workout,
)
from app.workout_models import (
    TimedWorkoutStep,
    WorkoutDraftRequest,
)


def main() -> None:
    draft = WorkoutDraftRequest(
        name="HR Builder Test",
        scheduled_date=(date.today() + timedelta(days=1)),
        steps=[
            TimedWorkoutStep(
                kind="warmup",
                duration_seconds=300,
            ),
            TimedWorkoutStep(
                kind="interval",
                duration_seconds=2700,
                heart_rate_min_bpm=135,
                heart_rate_max_bpm=150,
            ),
            TimedWorkoutStep(
                kind="cooldown",
                duration_seconds=300,
            ),
        ],
    )

    workout = build_running_workout(draft)

    main_step = workout.workoutSegments[0].workoutSteps[1]

    print(
        json.dumps(
            main_step.model_dump(),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
