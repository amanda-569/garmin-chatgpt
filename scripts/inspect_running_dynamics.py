from __future__ import annotations

from typing import Any

from garminconnect import Garmin

from app.config import settings

SEARCH_TERMS = (
    "ground",
    "contact",
    "stride",
    "spring",
    "stiff",
    "vertical",
    "oscillation",
    "power",
    "form",
    "impact",
    "loading",
    "duty",
    "cadence",
    "air",
)


def search(
    value: Any,
    path: str = "root",
) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"

            if any(term in key.lower() for term in SEARCH_TERMS):
                print(
                    child_path,
                    "->",
                    type(child).__name__,
                )

            search(
                child,
                child_path,
            )

    elif isinstance(value, list):
        for index, child in enumerate(value[:5]):
            search(
                child,
                f"{path}[{index}]",
            )


def main() -> None:
    activity_id = input("Activity ID: ").strip()

    client = Garmin()

    client.login(str(settings.garmin_token_directory))

    payloads = {
        "activity": client.get_activity(activity_id),
        "splits": client.get_activity_splits(activity_id),
        "details": client.get_activity_details(activity_id),
    }

    for name, payload in payloads.items():
        print()
        print("=" * 60)
        print(name.upper())
        print("=" * 60)

        search(payload)


if __name__ == "__main__":
    main()
