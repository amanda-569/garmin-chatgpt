from datetime import datetime, timezone

from app.models import RunSummary


MOCK_RUNS = [
    RunSummary(
        activity_id=123456789,
        name="Mock Outdoor Run",
        started_at=datetime(
            year=2026,
            month=7,
            day=19,
            hour=9,
            minute=30,
            tzinfo=timezone.utc,
        ),
        distance_meters=5000.0,
        duration_seconds=1440.0,
        average_heart_rate=164,
        maximum_heart_rate=181,
    ),
    RunSummary(
        activity_id=987654321,
        name="Mock Easy Run",
        started_at=datetime(
            year=2026,
            month=7,
            day=16,
            hour=18,
            minute=15,
            tzinfo=timezone.utc,
        ),
        distance_meters=8000.0,
        duration_seconds=2880.0,
        average_heart_rate=143,
        maximum_heart_rate=158,
    ),
]