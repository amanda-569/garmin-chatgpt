from __future__ import annotations

from datetime import date, timedelta

from app.workout_builder import (
    build_running_workout,
)
from app.workout_models import (
    RepeatWorkoutBlock,
    TimedWorkoutStep,
    WorkoutDraftRequest,
)


def main() -> None:
    draft = WorkoutDraftRequest(
        name="Builder Test - 5 x 3 Minutes",
        scheduled_date=(date.today() + timedelta(days=1)),
        steps=[
            TimedWorkoutStep(
                kind="warmup",
                duration_seconds=600,
            ),
            RepeatWorkoutBlock(
                repetitions=5,
                steps=[
                    TimedWorkoutStep(
                        kind="interval",
                        duration_seconds=180,
                    ),
                    TimedWorkoutStep(
                        kind="recovery",
                        duration_seconds=120,
                    ),
                ],
            ),
            TimedWorkoutStep(
                kind="cooldown",
                duration_seconds=600,
            ),
        ],
    )

    workout = build_running_workout(draft)

    print("Draft accepted.")
    print(
        "Workout name:",
        workout.workoutName,
    )
    print(
        "Estimated duration:",
        workout.estimatedDurationInSecs,
    )
    print(
        "Top-level steps:",
        len(workout.workoutSegments[0].workoutSteps),
    )
    print(
        "Scheduled date:",
        draft.scheduled_date,
    )


if __name__ == "__main__":
    main()
