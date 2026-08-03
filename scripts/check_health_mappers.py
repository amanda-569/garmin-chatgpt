from __future__ import annotations

from datetime import date, timedelta

from garminconnect import Garmin

from app.config import settings
from app.mappers.garmin_health import (
    map_garmin_cycle_day,
    map_garmin_recovery_day,
)


def main() -> None:
    target_date = date.today() - timedelta(days=1)

    date_string = target_date.isoformat()

    client = Garmin()

    client.login(str(settings.garmin_token_directory))

    recovery = map_garmin_recovery_day(
        target_date=target_date,
        sleep_payload=client.get_sleep_data(date_string),
        hrv_payload=client.get_hrv_data(date_string),
        resting_heart_rate_payload=(client.get_rhr_day(date_string)),
        training_readiness_payload=(client.get_morning_training_readiness(date_string)),
        body_battery_payload=(
            client.get_body_battery(
                date_string,
                date_string,
            )
        ),
        stress_payload=client.get_all_day_stress(date_string),
    )

    cycle = map_garmin_cycle_day(
        target_date=target_date,
        menstrual_payload=(client.get_menstrual_data_for_date(date_string)),
    )

    print("Recovery mapper succeeded.")
    print(
        "Populated recovery fields:",
        len(recovery.model_fields_set) - 3,
    )
    print(
        "Missing recovery fields:",
        recovery.missing_fields,
    )
    print(
        "Recovery warnings:",
        recovery.warnings,
    )
    print()

    print("Cycle mapper succeeded.")
    print(
        "Cycle data predicted:",
        cycle.cycle_is_predicted,
    )
    print(
        "Has logged day data:",
        cycle.has_logged_day_data,
    )
    print(
        "Missing cycle fields:",
        cycle.missing_fields,
    )
    print(
        "Cycle warnings:",
        cycle.warnings,
    )


if __name__ == "__main__":
    main()
