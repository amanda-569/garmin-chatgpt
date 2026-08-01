from datetime import date, timedelta
from getpass import getpass
from pathlib import Path
from xmlrpc import client
from app.mappers.garmin import (
    map_garmin_activity_to_run,
    map_garmin_activity_to_run_details,
)
from garminconnect import (
    Garmin,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
    GarminConnectAuthenticationError,
)
from app.config import settings

TOKEN_DIRECTORY = Path(".secrets/garmin").resolve()


def connect_to_garmin() -> Garmin:
    TOKEN_DIRECTORY.mkdir(parents=True, exist_ok=True)

    try:
        client = Garmin()
        client.login(str(TOKEN_DIRECTORY))

        print("Logged in using saved Garmin tokens.")
        return client

    except GarminConnectAuthenticationError:
        print("No valid saved Garmin login was found.")

    email = input("Enter your Garmin email: ").strip()
    password = getpass("Enter your Garmin password: ")

    client = Garmin(
        email=email,
        password=password,
        prompt_mfa=lambda: input("Garmin MFA code: ").strip(),
    )

    client.login(str(TOKEN_DIRECTORY))

    print("Garmin login successful.")
    print(f"Login tokens saved to {TOKEN_DIRECTORY}")

    return client


def describe_workout_step(
    step: dict[str, object],
    indent: int = 0,
) -> None:
    spacing = " " * indent

    step_type = step.get("stepType")
    end_condition = step.get("endCondition")
    target_type = step.get("targetType")

    step_type_key = (
        step_type.get("stepTypeKey") if isinstance(step_type, dict) else None
    )

    end_condition_key = (
        end_condition.get("conditionTypeKey")
        if isinstance(end_condition, dict)
        else None
    )

    target_type_key = (
        target_type.get("workoutTargetTypeKey")
        if isinstance(target_type, dict)
        else None
    )

    print(f"{spacing}Step order {step.get('stepOrder')}: " f"{step_type_key}")

    print(f"{spacing}  Garmin type: " f"{step.get('type')}")

    if step.get("type") == "RepeatGroupDTO":
        print(f"{spacing}  Repetitions: " f"{step.get('numberOfIterations')}")

        nested_steps = step.get("workoutSteps")

        if isinstance(nested_steps, list):
            print(f"{spacing}  Nested steps:")

            for nested_step in nested_steps:
                if isinstance(nested_step, dict):
                    describe_workout_step(
                        nested_step,
                        indent + 4,
                    )

        return

    print(f"{spacing}  End condition: " f"{end_condition_key}")

    print(f"{spacing}  End value: " f"{step.get('endConditionValue')}")

    print(f"{spacing}  Target type: " f"{target_type_key}")

    print(f"{spacing}  Target value one: " f"{step.get('targetValueOne')}")

    print(f"{spacing}  Target value two: " f"{step.get('targetValueTwo')}")

    print(f"{spacing}  Zone number: " f"{step.get('zoneNumber')}")


def describe_value(
    name: str,
    value: object,
    indent: int = 0,
) -> None:
    spacing = " " * indent

    if isinstance(value, dict):
        print(f"{spacing}{name}: dict with {len(value)} keys")

        for key, nested_value in value.items():
            describe_value(
                str(key),
                nested_value,
                indent + 2,
            )

    elif isinstance(value, list):
        print(f"{spacing}{name}: list with {len(value)} items")

        if value:
            describe_value(
                "[first item]",
                value[0],
                indent + 2,
            )

    else:
        print(f"{spacing}{name}: " f"{value!r} " f"({type(value).__name__})")


def main() -> None:
    try:
        client = connect_to_garmin()

        end_date = date.today()
        start_date = end_date - timedelta(days=30)

        activities = client.get_activities_by_date(
            startdate=start_date.isoformat(),
            enddate=end_date.isoformat(),
            activitytype="running",
        )
        print(f"Retrieved {len(activities)} activities:")

        if not activities:
            print("No activities found.")
            return

        latest_run = activities[0]
        activity_id = latest_run["activityId"]

        workout_id = latest_run.get("workoutId")

        if workout_id is None:
            raw_workout = None
            print("\nThis activity was not linked to a planned workout.")
        else:
            raw_workout = client.get_workout_by_id(workout_id)

            print(f"\nActivity is linked to workout {workout_id}.")
            print("\nPlanned workout steps:\n")

            segments = raw_workout.get("workoutSegments", [])

            for segment in segments:
                if not isinstance(segment, dict):
                    continue

                workout_steps = segment.get("workoutSteps", [])

                if not isinstance(workout_steps, list):
                    continue

                for workout_step in workout_steps:
                    if isinstance(workout_step, dict):
                        describe_workout_step(workout_step)

        raw_splits = client.get_activity_splits(str(activity_id))

        raw_hr_zones = client.get_activity_hr_in_timezones(str(activity_id))

        weather = client.get_activity_weather(str(activity_id))

        mapped_run = map_garmin_activity_to_run_details(
            raw_activity=latest_run,
            raw_weather=weather,
            raw_splits=raw_splits,
            raw_hr_zones=raw_hr_zones,
            temperature_unit=settings.garmin_temperature_unit,
            raw_workout=raw_workout,
        )

        print("\nMapped RunDetails:\n")
        print(mapped_run.model_dump_json(indent=2))

    except GarminConnectTooManyRequestsError as error:
        print(f"Too many requests to Garmin Connect: {error}")

    except GarminConnectAuthenticationError as error:
        print(f"Garmin authentication failed: {error}")

    except GarminConnectConnectionError as error:
        print(f"Failed to connect to Garmin Connect: {error}")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
