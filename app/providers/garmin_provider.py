from datetime import date, timedelta

from garminconnect import Garmin

from app.config import settings
from app.mappers.garmin import (
    map_garmin_activity_to_run,
    map_garmin_activity_to_run_details,
)
from app.models import RunDetails, RunSummary
from app.providers.base import RunProvider
from typing import Any
from hashlib import sha256
from pathlib import Path
from app.storage.vercel_blob import (
    VercelBlobTokenStore,
)


class GarminRunProvider(RunProvider):
    def __init__(self) -> None:
        self.token_directory = settings.garmin_token_directory

        self.token_file = self.token_directory / "garmin_tokens.json"

        self.blob_token_store: VercelBlobTokenStore | None = None

        self.last_token_digest: str | None = None

        self.token_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        if settings.garmin_token_storage == "vercel_blob":
            self._prepare_blob_token_storage()

        self.client = Garmin()

        self.client.login(str(self.token_directory))

        self._persist_and_sync_tokens()

    def list_runs(self) -> list[RunSummary]:
        end_date = date.today()
        start_date = end_date - timedelta(days=settings.garmin_lookback_days)

        raw_activities = self.client.get_activities_by_date(
            startdate=start_date.isoformat(),
            enddate=end_date.isoformat(),
            activitytype="running",
        )

        runs = [map_garmin_activity_to_run(activity) for activity in raw_activities]

        self._persist_and_sync_tokens()

        return runs

    def get_run_by_id(
        self,
        activity_id: int,
    ) -> RunDetails | None:
        activity_id_string = str(activity_id)

        raw_activity = self.client.get_activity(activity_id_string)

        if not raw_activity:
            self._persist_and_sync_tokens()
            return None

        raw_weather = self.client.get_activity_weather(activity_id_string)

        raw_splits = self.client.get_activity_splits(activity_id_string)

        raw_hr_zones = self.client.get_activity_hr_in_timezones(activity_id_string)

        workout_id = self.get_workout_id(raw_activity)

        if workout_id is None:
            raw_workout = None
        else:
            raw_workout = self.client.get_workout_by_id(workout_id)

        run = map_garmin_activity_to_run_details(
            raw_activity=raw_activity,
            raw_weather=raw_weather,
            raw_splits=raw_splits,
            raw_hr_zones=raw_hr_zones,
            raw_workout=raw_workout,
            temperature_unit=(settings.garmin_temperature_unit),
        )

        self._persist_and_sync_tokens()

        return run

    @staticmethod
    def get_workout_id(
        raw_activity: dict[str, Any],
    ) -> int | None:
        top_level_workout_id = raw_activity.get("workoutId")

        if top_level_workout_id is not None:
            return int(top_level_workout_id)

        metadata = raw_activity.get("metadataDTO")

        if not isinstance(metadata, dict):
            return None

        associated_workout_id = metadata.get("associatedWorkoutId")

        if associated_workout_id is None:
            return None

        return int(associated_workout_id)

    def _prepare_blob_token_storage(
        self,
    ) -> None:
        store_id = settings.blob_store_id
        secret = settings.blob_read_write_token

        if not store_id:
            raise RuntimeError(
                "BLOB_STORE_ID is required when " "GARMIN_TOKEN_STORAGE=vercel_blob."
            )

        if secret is None:
            raise RuntimeError(
                "BLOB_READ_WRITE_TOKEN is required "
                "when GARMIN_TOKEN_STORAGE="
                "vercel_blob."
            )

        self.blob_token_store = VercelBlobTokenStore(
            store_id=store_id,
            read_write_token=(secret.get_secret_value()),
            blob_path=(settings.garmin_token_blob_path),
        )

        self.blob_token_store.download_to(self.token_file)

        self.last_token_digest = self._calculate_token_digest()

    def _calculate_token_digest(
        self,
    ) -> str | None:
        if not self.token_file.exists():
            return None

        return sha256(self.token_file.read_bytes()).hexdigest()

    def _persist_and_sync_tokens(
        self,
    ) -> None:
        if self.blob_token_store is None:
            return

        self.client.client.dump(str(self.token_directory))

        current_digest = self._calculate_token_digest()

        if current_digest is None:
            raise RuntimeError("Garmin did not produce a token file.")

        if current_digest == self.last_token_digest:
            return

        self.blob_token_store.upload_from(self.token_file)

        self.last_token_digest = current_digest
