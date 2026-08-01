from fastapi import FastAPI
from app.routers import runs
from app.config import settings

app = FastAPI(
    title="Garmin Running Coach API",
    description=(
        "A private API that retrieves Garmin running data, "
        "compares completed runs with planned workouts, "
        "and returns deterministic workout analysis."
    ),
    version="0.1.0",
)
app.include_router(runs.router)


@app.get(
    "/health",
    include_in_schema=False,
)
def health_check() -> dict[str, str]:
    return {"status": "ok"}
