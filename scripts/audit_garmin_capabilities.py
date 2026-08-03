from __future__ import annotations

import inspect
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version

from garminconnect import Garmin

# These keywords find both the methods we expect
# and similarly named methods we may not know about yet.
SEARCH_KEYWORDS = (
    "sleep",
    "hrv",
    "resting",
    "rhr",
    "body_battery",
    "stress",
    "readiness",
    "menstrual",
    "cycle",
    "workout",
    "schedule",
    "device",
)


# These prefixes usually indicate that calling the method
# could modify the Garmin account.
MUTATING_PREFIXES = (
    "add_",
    "create_",
    "delete_",
    "remove_",
    "schedule_",
    "set_",
    "unschedule_",
    "update_",
    "upload_",
    "push_",
)


def get_package_version() -> str:
    """Return the installed garminconnect package version."""
    try:
        return version("garminconnect")
    except PackageNotFoundError:
        return "unknown"


def classify_method(method_name: str) -> str:
    """
    Classify a method by name.

    This is only a safety label for our audit.
    It does not prove what the method does internally.
    """
    if method_name.startswith(MUTATING_PREFIXES):
        return "MUTATING"

    if method_name.startswith("get_"):
        return "READ"

    return "REVIEW"


def get_signature(method: object) -> str:
    """Return a readable signature without crashing the audit."""
    try:
        return str(inspect.signature(method))
    except (TypeError, ValueError):
        return "(signature unavailable)"


def main() -> None:
    print("This script only inspects installed Python code.")
    print("It does not log in or make Garmin API requests.")
    print()
    print(
        "Installed garminconnect version:",
        get_package_version(),
    )
    print()

    matching_methods: list[tuple[str, str, str]] = []

    for method_name, method in inspect.getmembers(
        Garmin,
        predicate=callable,
    ):
        if method_name.startswith("_"):
            continue

        normalized_name = method_name.lower()

        if not any(keyword in normalized_name for keyword in SEARCH_KEYWORDS):
            continue

        matching_methods.append(
            (
                classify_method(method_name),
                method_name,
                get_signature(method),
            )
        )

    if not matching_methods:
        print("No matching methods were found.")
        return

    category_order = {
        "READ": 0,
        "REVIEW": 1,
        "MUTATING": 2,
    }

    matching_methods.sort(
        key=lambda item: (
            category_order[item[0]],
            item[1],
        )
    )

    current_category: str | None = None

    for category, method_name, method_signature in matching_methods:
        if category != current_category:
            current_category = category
            print(f"=== {category} METHODS ===")

        print(f"{method_name}{method_signature}")

    print()
    print("No methods above were called.")


if __name__ == "__main__":
    main()
