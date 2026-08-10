from __future__ import annotations

import inspect
from enum import Enum
from typing import Any

import garminconnect.workout as workout
from pydantic import BaseModel


def format_annotation(annotation: Any) -> str:
    """Produce a readable field-type description."""
    return str(annotation).replace(
        "typing.",
        "",
    )


def print_enum(
    name: str,
    enum_class: type[Enum],
) -> None:
    print("=" * 72)
    print(f"ENUM: {name}")

    for member in enum_class:
        print(f"- {member.name} = {member.value!r}")

    print()


def print_model(
    name: str,
    model_class: type[BaseModel],
) -> None:
    print("=" * 72)
    print(f"MODEL: {name}")

    try:
        print(
            "Signature:",
            inspect.signature(model_class),
        )
    except (TypeError, ValueError):
        print("Signature: unavailable")

    print("Fields:")

    for field_name, field in model_class.model_fields.items():
        required = field.is_required()

        print(f"- {field_name}")
        print(
            "  type:",
            format_annotation(field.annotation),
        )
        print(
            "  required:",
            required,
        )

        if not required:
            print(
                "  default:",
                repr(field.default),
            )

    print()


def print_helper(
    name: str,
    helper: Any,
) -> None:
    print("=" * 72)
    print(f"HELPER: {name}")

    try:
        print(
            "Signature:",
            inspect.signature(helper),
        )
    except (TypeError, ValueError):
        print("Signature: unavailable")

    print()

    docstring = inspect.getdoc(helper)

    if docstring:
        print("Docstring:")
        print(docstring)
        print()

    print("Source:")

    try:
        print(inspect.getsource(helper))
    except (OSError, TypeError):
        print("<source unavailable>")

    print()


def main() -> None:
    print(
        "Workout module:",
        workout.__file__,
    )
    print()

    members = inspect.getmembers(workout)

    enums: list[tuple[str, type[Enum]]] = []

    models: list[tuple[str, type[BaseModel]]] = []

    helpers: list[tuple[str, Any]] = []

    for name, value in members:
        if name.startswith("_"):
            continue

        # Ignore classes and functions imported into
        # the module from somewhere else.
        if (
            getattr(
                value,
                "__module__",
                None,
            )
            != workout.__name__
        ):
            continue

        if inspect.isclass(value):
            if issubclass(value, Enum):
                enums.append((name, value))
            elif issubclass(value, BaseModel):
                models.append((name, value))

        elif inspect.isfunction(value) and name.startswith("create_"):
            helpers.append((name, value))

    print("Discovered enums:")
    for name, _ in enums:
        print(f"- {name}")

    print()

    print("Discovered Pydantic models:")
    for name, _ in models:
        print(f"- {name}")

    print()

    print("Discovered create helpers:")
    for name, _ in helpers:
        print(f"- {name}")

    print()

    for name, enum_class in enums:
        print_enum(
            name,
            enum_class,
        )

    for name, model_class in models:
        print_model(
            name,
            model_class,
        )

    for name, helper in helpers:
        print_helper(
            name,
            helper,
        )


if __name__ == "__main__":
    main()
