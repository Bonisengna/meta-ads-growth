from datetime import UTC, date, datetime
from types import SimpleNamespace

import pytest

import app.services.meta_sync_runner as runner_module
from app.services.meta_graph_client import MetaGraphError
from app.services.meta_sync_runner import (
    MetaSyncRunner,
    SyncAlreadyRunningError,
    retry_transient,
    safe_error,
)


NOW = datetime(2026, 8, 16, 12, tzinfo=UTC)


class FakeQuery:
    def __init__(self, database: dict[str, list[dict]], table: str) -> None:
        self.database = database
        self.table = table
        self.operation = "select"
        self.payload = None
        self.filters: list[tuple[str, str, object]] = []

    def select(self, _columns: str):
        self.operation = "select"
        return self

    def insert(self, payload: dict):
        self.operation = "insert"
        self.payload = payload
        return self

    def update(self, payload: dict):
        self.operation = "update"
        self.payload = payload
        return self

    def eq(self, column: str, value: object):
        self.filters.append(("eq", column, value))
        return self

    def lt(self, column: str, value: object):
        self.filters.append(("lt", column, value))
        return self

    def order(self, _column: str):
        return self

    def limit(self, _limit: int):
        return self

    def execute(self):
        rows = self.database.setdefault(self.table, [])
        matching = [row for row in rows if self._matches(row)]
        if self.operation == "insert":
            if self.table == "sync_runs" and any(
                row["scope"] == self.payload["scope"] and row["status"] == "RUNNING"
                for row in rows
            ):
                raise RuntimeError("duplicate key")
            created = {"id": f"run-{len(rows) + 1}", **self.payload}
            rows.append(created)
            return SimpleNamespace(data=[created])
        if self.operation == "update":
            for row in matching:
                row.update(self.payload)
            return SimpleNamespace(data=matching)
        return SimpleNamespace(data=matching)

    def _matches(self, row: dict) -> bool:
        for operation, column, value in self.filters:
            if operation == "eq" and row.get(column) != value:
                return False
            if operation == "lt" and not str(row.get(column)) < str(value):
                return False
        return True


class FakeSupabase:
    def __init__(self, database: dict[str, list[dict]]) -> None:
        self.database = database

    def table(self, table: str) -> FakeQuery:
        return FakeQuery(self.database, table)


class FakeSyncService:
    calls: list[tuple] = []

    def __init__(self, _supabase, _meta) -> None:
        pass

    def sync_account(self, client_id, account_id):
        self.calls.append(("entities", client_id, account_id))
        if account_id == "failed":
            raise MetaGraphError("requisição inválida", status_code=400)
        if account_id == "expired":
            raise MetaGraphError("token inválido", code=190, status_code=400)
        return {
            "meta_accounts": 1, "campaigns": 2, "adsets": 3, "ads": 4,
            "changes": {
                "meta_accounts": {"imported": 0, "updated": 1, "archived": 0},
                "campaigns": {"imported": 1, "updated": 1, "archived": 0},
                "adsets": {"imported": 0, "updated": 3, "archived": 0},
                "ads": {"imported": 0, "updated": 4, "archived": 0},
            },
        }

    def sync_daily_metrics(self, account_id, since, until):
        self.calls.append(("metrics", account_id, since, until))
        return {"campaign": 2, "adset": 3, "ad": 4}

    def sync_breakdown_metrics(self, account_id, since, until):
        self.calls.append(("breakdowns", account_id, since, until))
        if account_id == "breakdown-failed":
            raise MetaGraphError("invalid breakdown", code=100, status_code=400)
        return {"age": 2, "gender": 2}


def make_database() -> dict[str, list[dict]]:
    return {
        "sync_runs": [],
        "meta_accounts": [
            {"id": "a1", "client_id": "c1", "meta_account_id": "123", "name": "Ativa", "status": "ACTIVE"},
            {"id": "a2", "client_id": "c1", "meta_account_id": "999", "name": "Arquivada", "status": "ARCHIVED"},
        ],
    }


def test_runner_syncs_only_active_accounts_and_reprocesses_today(monkeypatch) -> None:
    FakeSyncService.calls = []
    monkeypatch.setattr(runner_module, "MetaSyncService", FakeSyncService)
    database = make_database()
    runner = MetaSyncRunner(  # type: ignore[arg-type]
        FakeSupabase(database), object(), now=lambda: NOW, sleep=lambda _delay: None
    )

    result = runner.run(lookback_days=3)

    assert result["status"] == "SUCCESS"
    assert result["accounts_total"] == 1
    assert result["entity_changes"]["campaigns"] == {
        "imported": 1, "updated": 1, "archived": 0
    }
    assert FakeSyncService.calls == [
        ("entities", "c1", "123"),
        ("metrics", "123", date(2026, 8, 14), date(2026, 8, 16)),
        ("breakdowns", "123", date(2026, 8, 14), date(2026, 8, 16)),
    ]
    saved = database["sync_runs"][0]
    assert saved["status"] == "SUCCESS"
    assert saved["duration_ms"] == 0


def test_runner_accepts_180_day_historical_backfill(monkeypatch) -> None:
    FakeSyncService.calls = []
    monkeypatch.setattr(runner_module, "MetaSyncService", FakeSyncService)
    result = MetaSyncRunner(  # type: ignore[arg-type]
        FakeSupabase(make_database()), object(), now=lambda: NOW, sleep=lambda _delay: None
    ).run(lookback_days=180)

    assert result["status"] == "SUCCESS"
    assert result["lookback_days"] == 180
    assert ("metrics", "123", date(2026, 2, 18), date(2026, 8, 16)) in FakeSyncService.calls


def test_runner_rejects_more_than_180_days() -> None:
    runner = MetaSyncRunner(FakeSupabase(make_database()), object(), now=lambda: NOW)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="entre 1 e 180"):
        runner.run(181)


def test_runner_marks_partial_when_one_account_fails(monkeypatch) -> None:
    FakeSyncService.calls = []
    monkeypatch.setattr(runner_module, "MetaSyncService", FakeSyncService)
    database = make_database()
    database["meta_accounts"].append(
        {"id": "a3", "client_id": "c1", "meta_account_id": "failed", "name": "Falha", "status": "ACTIVE"}
    )
    result = MetaSyncRunner(  # type: ignore[arg-type]
        FakeSupabase(database), object(), now=lambda: NOW, sleep=lambda _delay: None
    ).run(3)

    assert result["status"] == "PARTIAL"
    assert result["accounts_success"] == 1
    assert result["accounts_failed"] == 1
    assert result["accounts"][1]["error_stage"] == "entities"


def test_runner_reports_breakdown_failure_stage(monkeypatch) -> None:
    FakeSyncService.calls = []
    monkeypatch.setattr(runner_module, "MetaSyncService", FakeSyncService)
    database = make_database()
    database["meta_accounts"][0]["meta_account_id"] = "breakdown-failed"

    result = MetaSyncRunner(  # type: ignore[arg-type]
        FakeSupabase(database), object(), now=lambda: NOW, sleep=lambda _delay: None
    ).run(3)

    assert result["status"] == "FAILED"
    assert result["accounts"][0]["error_stage"] == "breakdowns"
    assert result["accounts"][0]["error_code"] == 100


def test_running_lock_prevents_concurrent_sync() -> None:
    database = make_database()
    database["sync_runs"].append(
        {
            "id": "run-active", "scope": "META_ALL", "status": "RUNNING",
            "started_at": NOW.isoformat(), "lock_expires_at": "2026-08-16T13:00:00+00:00",
        }
    )
    runner = MetaSyncRunner(FakeSupabase(database), object(), now=lambda: NOW)  # type: ignore[arg-type]

    with pytest.raises(SyncAlreadyRunningError):
        runner.run(3)


def test_runner_creates_token_expired_alert(monkeypatch) -> None:
    FakeSyncService.calls = []
    monkeypatch.setattr(runner_module, "MetaSyncService", FakeSyncService)
    database = make_database()
    database["meta_accounts"][0]["meta_account_id"] = "expired"

    result = MetaSyncRunner(  # type: ignore[arg-type]
        FakeSupabase(database), object(), now=lambda: NOW, sleep=lambda _delay: None
    ).run(3)

    assert result["status"] == "FAILED"
    alert = database["integration_alerts"][0]
    assert alert["alert_type"] == "TOKEN_EXPIRED"
    assert alert["status"] == "OPEN"


def test_retry_uses_exponential_delay_for_transient_errors() -> None:
    calls = 0
    delays: list[float] = []

    def operation() -> str:
        nonlocal calls
        calls += 1
        if calls < 3:
            raise MetaGraphError("temporário", status_code=503)
        return "ok"

    result, attempts = retry_transient(operation, 3, 1, delays.append)

    assert (result, attempts) == ("ok", 3)
    assert delays == [1, 2]


def test_retry_does_not_repeat_permanent_error() -> None:
    calls = 0

    def operation() -> None:
        nonlocal calls
        calls += 1
        raise MetaGraphError("token expirado", code=190, status_code=400)

    with pytest.raises(MetaGraphError):
        retry_transient(operation, 3, 1, lambda _delay: None)
    assert calls == 1


def test_error_log_redacts_credentials() -> None:
    message = safe_error(RuntimeError("access_token=secret Bearer abc.def app_secret=hidden"))
    assert "=secret" not in message
    assert "abc.def" not in message
    assert "=hidden" not in message
    assert message.count("[REDACTED]") == 3
