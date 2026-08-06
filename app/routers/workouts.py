from __future__ import annotations

from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from app.security import verify_api_key
from app.services.workout_service import (
    WorkoutCommitConflictError,
    WorkoutCommitExternalError,
    commit_workout_draft,
    create_workout_preview,
)
from app.storage.workout_drafts import (
    WorkoutDraftNotFoundError,
)
from app.workout_models import (
    WorkoutCommitRequest,
    WorkoutCommitResult,
    WorkoutDraftPreview,
    WorkoutDraftRequest,
)

router = APIRouter(
    prefix="/workouts",
    tags=["workouts"],
    dependencies=[
        Depends(verify_api_key),
    ],
)


@router.post(
    "/preview",
    response_model=WorkoutDraftPreview,
    operation_id="previewWorkout",
    summary="Preview a proposed running workout",
    description=(
        "Validates a proposed running workout and "
        "returns a readable preview. This operation "
        "does not upload or schedule anything."
    ),
)
def preview_workout_route(
    draft: WorkoutDraftRequest,
) -> WorkoutDraftPreview:
    try:
        return create_workout_preview(draft)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc


@router.post(
    "/{draft_id}/commit",
    response_model=WorkoutCommitResult,
    operation_id="commitWorkout",
    summary="Upload and schedule an approved workout",
    description=(
        "Uploads the exact saved workout draft to "
        "Garmin and schedules it. This changes the "
        "user's real Garmin account."
    ),
    openapi_extra={
        "x-openai-isConsequential": True,
    },
)
def commit_workout_route(
    draft_id: UUID,
    request: WorkoutCommitRequest,
) -> WorkoutCommitResult:
    # The Literal field proves the caller supplied
    # the explicit confirmation phrase.
    _ = request.confirmation

    try:
        return commit_workout_draft(draft_id)
    except WorkoutDraftNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except WorkoutCommitConflictError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc
    except WorkoutCommitExternalError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc
