from __future__ import annotations

from garminconnect import Garmin

from app.config import settings


def main() -> None:
    client = Garmin()

    client.login(str(settings.garmin_token_directory))

    workouts = client.get_workouts(
        start=0,
        limit=20,
    )

    print("Recent workouts:")
    print()

    for workout in workouts:
        print(
            workout.get("workoutId"),
            "-",
            workout.get("workoutName"),
        )


if __name__ == "__main__":
    main()
