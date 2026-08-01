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


class GarminRunProvider(RunProvider):
    def __init__(self) -> None:
        token_directory = settings.garmin_token_directory

        self.client = Garmin()
        self.client.login(str(token_directory))

    def list_runs(self) -> list[RunSummary]:
        end_date = date.today()
        start_date = end_date - timedelta(days=settings.garmin_lookback_days)

        raw_activities = self.client.get_activities_by_date(
            startdate=start_date.isoformat(),
            enddate=end_date.isoformat(),
            activitytype="running",
        )

        return [map_garmin_activity_to_run(activity) for activity in raw_activities]

    def get_run_by_id(
        self,
        activity_id: int,
    ) -> RunDetails | None:
        activity_id_string = str(activity_id)

        raw_activity = self.client.get_activity(activity_id_string)

        if not raw_activity:
            return None

        raw_weather = self.client.get_activity_weather(activity_id_string)

        raw_splits = self.client.get_activity_splits(activity_id_string)

        raw_hr_zones = self.client.get_activity_hr_in_timezones(activity_id_string)

        workout_id = self.get_workout_id(raw_activity)

        if workout_id is None:
            raw_workout = None
        else:
            raw_workout = self.client.get_workout_by_id(workout_id)

        return map_garmin_activity_to_run_details(
            raw_activity=raw_activity,
            raw_weather=raw_weather,
            raw_splits=raw_splits,
            raw_hr_zones=raw_hr_zones,
            raw_workout=raw_workout,
            temperature_unit=(settings.garmin_temperature_unit),
        )

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
