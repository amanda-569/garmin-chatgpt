from fastapi import FastAPI
from app.routers import runs
from app.config import settings
from copy import deepcopy
from typing import Any

app = FastAPI(
    title="Garmin Running Coach API",
    description=(
        "A private API that retrieves Garmin running data, "
        "compares completed runs with planned workouts, "
        "and returns deterministic workout analysis."
    ),
    version="0.1.0",
    servers=[
        {
            "url": "https://garmin-chatgpt.vercel.app",
            "description": "Production",
        }
    ],
)
app.include_router(runs.router)


@app.get(
    "/health",
    include_in_schema=False,
)
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get(
    "/action-openapi.json",
    include_in_schema=False,
)
def get_action_openapi_schema() -> dict[str, Any]:
    schema = deepcopy(app.openapi())

    component_schemas = schema.get("components", {}).get("schemas", {})

    planned_step_schema = component_schemas.get("PlannedWorkoutStep")

    if not isinstance(planned_step_schema, dict):
        return schema

    child_step_schema = deepcopy(planned_step_schema)

    child_step_schema["title"] = "PlannedWorkoutChildStep"

    child_properties = child_step_schema.get("properties")

    if isinstance(child_properties, dict):
        child_properties.pop(
            "child_steps",
            None,
        )

    child_required = child_step_schema.get("required")

    if isinstance(child_required, list):
        child_step_schema["required"] = [
            field_name for field_name in child_required if field_name != "child_steps"
        ]

    component_schemas["PlannedWorkoutChildStep"] = child_step_schema

    planned_properties = planned_step_schema.get("properties")

    if isinstance(planned_properties, dict):
        child_steps_property = planned_properties.get("child_steps")

        if isinstance(
            child_steps_property,
            dict,
        ):
            child_steps_property["items"] = {
                "$ref": ("#/components/schemas/" "PlannedWorkoutChildStep")
            }

    return schema
