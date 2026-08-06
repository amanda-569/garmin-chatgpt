from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Protocol
from uuid import UUID

from app.config import settings
from app.storage.vercel_blob import (
    BlobStorageError,
    VercelBlobTokenStore,
)
from app.workout_models import (
    StoredWorkoutDraft,
)


class WorkoutDraftNotFoundError(LookupError):
    pass


class WorkoutDraftStore(Protocol):
    def save(
        self,
        record: StoredWorkoutDraft,
    ) -> None: ...

    def get(
        self,
        draft_id: UUID,
    ) -> StoredWorkoutDraft: ...


class LocalWorkoutDraftStore:
    def __init__(
        self,
        directory: Path,
    ) -> None:
        self.directory = directory

    def _path_for(
        self,
        draft_id: UUID,
    ) -> Path:
        return self.directory / (f"{draft_id}.json")

    def save(
        self,
        record: StoredWorkoutDraft,
    ) -> None:
        self.directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        destination = self._path_for(record.draft_id)

        temporary = destination.with_suffix(".tmp")

        temporary.write_text(
            record.model_dump_json(indent=2),
            encoding="utf-8",
        )

        os.chmod(temporary, 0o600)
        temporary.replace(destination)

    def get(
        self,
        draft_id: UUID,
    ) -> StoredWorkoutDraft:
        source = self._path_for(draft_id)

        if not source.exists():
            raise WorkoutDraftNotFoundError(
                f"Workout draft {draft_id} " "was not found."
            )

        return StoredWorkoutDraft.model_validate_json(
            source.read_text(encoding="utf-8")
        )


class VercelBlobWorkoutDraftStore:
    def __init__(
        self,
        store_id: str,
        read_write_token: str,
        blob_prefix: str,
    ) -> None:
        self.store_id = store_id
        self.read_write_token = read_write_token
        self.blob_prefix = blob_prefix.rstrip("/")

    def _blob_store_for(
        self,
        draft_id: UUID,
    ) -> VercelBlobTokenStore:
        return VercelBlobTokenStore(
            store_id=self.store_id,
            read_write_token=(self.read_write_token),
            blob_path=(f"{self.blob_prefix}/" f"{draft_id}.json"),
        )

    def save(
        self,
        record: StoredWorkoutDraft,
    ) -> None:
        with TemporaryDirectory() as directory:
            temporary = Path(directory) / "draft.json"

            temporary.write_text(
                record.model_dump_json(indent=2),
                encoding="utf-8",
            )

            self._blob_store_for(record.draft_id).upload_from(temporary)

    def get(
        self,
        draft_id: UUID,
    ) -> StoredWorkoutDraft:
        with TemporaryDirectory() as directory:
            temporary = Path(directory) / "draft.json"

            try:
                self._blob_store_for(draft_id).download_to(temporary)
            except BlobStorageError as exc:
                if "404" in str(exc):
                    raise (
                        WorkoutDraftNotFoundError(
                            f"Workout draft " f"{draft_id} was " "not found."
                        )
                    ) from exc

                raise

            return StoredWorkoutDraft.model_validate_json(
                temporary.read_text(encoding="utf-8")
            )


@lru_cache
def get_workout_draft_store() -> WorkoutDraftStore:
    if settings.garmin_token_storage == "vercel_blob":
        if settings.blob_store_id is None:
            raise RuntimeError("BLOB_STORE_ID is required " "for Blob draft storage.")

        if settings.blob_read_write_token is None:
            raise RuntimeError(
                "BLOB_READ_WRITE_TOKEN is " "required for Blob draft " "storage."
            )

        return VercelBlobWorkoutDraftStore(
            store_id=settings.blob_store_id,
            read_write_token=(settings.blob_read_write_token.get_secret_value()),
            blob_prefix=(settings.workout_draft_blob_prefix),
        )

    return LocalWorkoutDraftStore(settings.workout_draft_directory)
