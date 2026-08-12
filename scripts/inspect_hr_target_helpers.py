from __future__ import annotations

import inspect

import garminconnect.workout as workout


def print_member(name: str) -> None:
    member = getattr(workout, name, None)

    print("=" * 72)
    print(name)

    if member is None:
        print("Not found.")
        print()
        return

    try:
        print("Signature:")
        print(inspect.signature(member))
    except (TypeError, ValueError):
        print("Signature unavailable.")

    print()

    doc = inspect.getdoc(member)
    if doc:
        print("Docstring:")
        print(doc)
        print()

    try:
        print("Source:")
        print(inspect.getsource(member))
    except (OSError, TypeError):
        print("Source unavailable.")

    print()


def main() -> None:
    names = [
        name
        for name in dir(workout)
        if "heart" in name.lower() or "hr" in name.lower() or "target" in name.lower()
    ]

    print("Potential HR/target symbols:")
    for name in names:
        print("-", name)

    print()

    for name in names:
        print_member(name)


if __name__ == "__main__":
    main()
