from datetime import UTC, datetime

import pytest
import app.workers.meta_sync_worker as worker_module

from app.workers.meta_sync_worker import next_scheduled_run, parse_daily_time, process_pending_requests


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


def test_worker_consumes_persistent_request_and_records_result(monkeypatch) -> None:
    request = {"id": "request-1", "client_id": "client-1", "requested_by": "user-1", "lookback_days": 30, "recovery_of": None}
    claims = iter([request, None])
    finished: list[tuple] = []
    monkeypatch.setattr(worker_module, "get_supabase_client", lambda: object())
    monkeypatch.setattr(worker_module, "claim_next_request", lambda _client: next(claims))
    monkeypatch.setattr(worker_module, "run_meta_sync", lambda *args, **kwargs: {"run_id": "run-1", "status": "SUCCESS"})
    monkeypatch.setattr(worker_module, "finish_request", lambda *args: finished.append(args))
    monkeypatch.setattr(worker_module, "emit", lambda *args, **kwargs: None)

    assert process_pending_requests() == 1
    assert finished[0][1] == "request-1"
    assert finished[0][2]["status"] == "SUCCESS"


def test_worker_records_simulated_failure_and_continues(monkeypatch) -> None:
    request = {"id": "request-2", "client_id": "client-1", "requested_by": "user-1", "lookback_days": 3, "recovery_of": None}
    claims = iter([request, None])
    finished: list[tuple] = []
    monkeypatch.setattr(worker_module, "get_supabase_client", lambda: object())
    monkeypatch.setattr(worker_module, "claim_next_request", lambda _client: next(claims))
    def fail(*_args, **_kwargs):
        raise RuntimeError("temporary upstream failure")
    monkeypatch.setattr(worker_module, "run_meta_sync", fail)
    monkeypatch.setattr(worker_module, "finish_request", lambda *args: finished.append(args))
    monkeypatch.setattr(worker_module, "emit", lambda *args, **kwargs: None)

    assert process_pending_requests() == 1
    assert finished[0][1] == "request-2"
    assert finished[0][2] is None
    assert isinstance(finished[0][3], RuntimeError)
