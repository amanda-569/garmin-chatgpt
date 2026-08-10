from __future__ import annotations

import inspect

import garminconnect
from garminconnect import Garmin

METHOD_NAMES = (
    "upload_running_workout",
    "upload_workout",
    "schedule_workout",
    "unschedule_workout",
    "delete_workout",
)


def print_method_details(
    method_name: str,
) -> None:
    print("=" * 72)
    print(f"METHOD: {method_name}")

    method = getattr(
        Garmin,
        method_name,
        None,
    )

    if method is None:
        print("Not present in this installed version.")
        print()
        return

    original_method = inspect.unwrap(method)

    try:
        signature = inspect.signature(original_method)
    except (TypeError, ValueError):
        signature = "<signature unavailable>"

    print("Signature:")
    print(signature)
    print()

    print("Docstring:")
    print(inspect.getdoc(original_method) or "<no docstring>")
    print()

    print("Source:")
    try:
        print(inspect.getsource(original_method))
    except (OSError, TypeError):
        print("<source unavailable>")

    print()


def main() -> None:
    print(
        "garminconnect module:",
        garminconnect.__file__,
    )
    print()

    workout_symbols = sorted(
        name for name in dir(garminconnect) if "workout" in name.lower()
    )

    print("Workout-related exported symbols:")
    for symbol in workout_symbols:
        print(f"- {symbol}")

    print()

    for method_name in METHOD_NAMES:
        print_method_details(method_name)


if __name__ == "__main__":
    main()
