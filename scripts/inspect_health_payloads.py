from __future__ import annotations

import argparse
import time
from datetime import date, timedelta
from typing import Any, Callable

from garminconnect import Garmin

from app.config import settings

ReadOperation = Callable[[], Any]


def describe_structure(
    value: Any,
    path: str = "root",
    depth: int = 0,
    max_depth: int = 10,
) -> None:
    """
    Print field paths and Python types without printing values.

    This lets us inspect Garmin's response structure without
    exposing private sleep or menstrual information.
    """
    if depth > max_depth:
        print(f"{path}: depth limit reached")
        return

    if isinstance(value, dict):
        if not value:
            print(f"{path}: empty object")
            return

        for key in sorted(value):
            child_path = f"{path}.{key}"

            describe_structure(
                value=value[key],
                path=child_path,
                depth=depth + 1,
                max_depth=max_depth,
            )

        return

    if isinstance(value, list):
        print(f"{path}: array[{len(value)}]")

        if value:
            describe_structure(
                value=value[0],
                path=f"{path}[0]",
                depth=depth + 1,
                max_depth=max_depth,
            )

        return

    type_name = "null" if value is None else type(value).__name__

    print(f"{path}: {type_name}")


def create_read_operations(
    client: Garmin,
    target_date: str,
) -> dict[str, ReadOperation]:
    """
    Return read-only Garmin calls.

    Nothing in this mapping uploads, schedules, edits,
    deletes, or otherwise changes Garmin account data.
    """
    return {
        "sleep": lambda: client.get_sleep_data(target_date),
        "hrv": lambda: client.get_hrv_data(target_date),
        "resting_heart_rate": (lambda: client.get_rhr_day(target_date)),
        "morning_training_readiness": (
            lambda: client.get_morning_training_readiness(target_date)
        ),
        "training_readiness": (lambda: client.get_training_readiness(target_date)),
        "body_battery": (
            lambda: client.get_body_battery(
                target_date,
                target_date,
            )
        ),
        "stress": lambda: client.get_all_day_stress(target_date),
        "menstrual_day": (lambda: client.get_menstrual_data_for_date(target_date)),
        "menstrual_calendar": (
            lambda: client.get_menstrual_calendar_data(
                target_date,
                target_date,
            )
        ),
    }


def parse_args() -> argparse.Namespace:
    default_date = (date.today() - timedelta(days=1)).isoformat()

    parser = argparse.ArgumentParser(
        description=(
            "Inspect Garmin health-response structures "
            "without printing private values."
        )
    )

    parser.add_argument(
        "--date",
        default=default_date,
        help=("Date to inspect in YYYY-MM-DD format. " "Defaults to yesterday."),
    )

    parser.add_argument(
        "--only",
        nargs="*",
        help=(
            "Optional operation names to inspect. "
            "When omitted, all read operations run."
        ),
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # Validate the supplied date before making requests.
    date.fromisoformat(args.date)

    print("Garmin health payload inspector")
    print(f"Date: {args.date}")
    print("Only field names and Python types will be shown.")
    print("No health or menstrual values will be printed.")
    print()

    client = Garmin()

    client.login(str(settings.garmin_token_directory))

    operations = create_read_operations(
        client=client,
        target_date=args.date,
    )

    requested_names = args.only if args.only else list(operations)

    unknown_names = [name for name in requested_names if name not in operations]

    if unknown_names:
        available = ", ".join(operations)

        raise ValueError(
            "Unknown operation(s): "
            f"{', '.join(unknown_names)}. "
            f"Available operations: {available}"
        )

    for index, operation_name in enumerate(requested_names):
        print(f"=== {operation_name.upper()} ===")

        operation = operations[operation_name]

        try:
            result = operation()
            describe_structure(result)

        except Exception as error:
            print(
                "Request failed:",
                type(error).__name__,
            )
            print(
                "Message:",
                str(error),
            )

        print()

        # Be polite to Garmin's unofficial API and avoid
        # sending all requests simultaneously.
        if index < len(requested_names) - 1:
            time.sleep(1)


if __name__ == "__main__":
    main()
