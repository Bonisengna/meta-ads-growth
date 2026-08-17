from datetime import UTC, datetime

import pytest

from app.workers.meta_sync_worker import next_scheduled_run, parse_daily_time


def test_parse_daily_time_accepts_hour_and_minute() -> None:
    parsed = parse_daily_time("03:15")

    assert parsed.hour == 3
    assert parsed.minute == 15


@pytest.mark.parametrize("value", ["3:00", "24:00", "03:60", "amanhã"])
def test_parse_daily_time_rejects_invalid_values(value: str) -> None:
    with pytest.raises(ValueError, match="HH:MM"):
        parse_daily_time(value)


def test_next_scheduled_run_uses_sao_paulo_timezone_before_schedule() -> None:
    now = datetime(2026, 8, 17, 5, 30, tzinfo=UTC)  # 02:30 em São Paulo

    result = next_scheduled_run(now, "03:00", "America/Sao_Paulo")

    assert result == datetime(2026, 8, 17, 6, 0, tzinfo=UTC)


def test_next_scheduled_run_moves_to_next_day_after_schedule() -> None:
    now = datetime(2026, 8, 17, 6, 30, tzinfo=UTC)  # 03:30 em São Paulo

    result = next_scheduled_run(now, "03:00", "America/Sao_Paulo")

    assert result == datetime(2026, 8, 18, 6, 0, tzinfo=UTC)
