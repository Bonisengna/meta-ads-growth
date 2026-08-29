from datetime import UTC, datetime
from types import SimpleNamespace

from app.services.meta_health_service import MetaHealthService


NOW = datetime(2026, 8, 16, 12, tzinfo=UTC)


class FakeQuery:
    def __init__(self, rows: list[dict]) -> None:
        self.rows = rows
        self.filters: list[tuple[str, object]] = []
        self.limit_value: int | None = None

    def select(self, _columns: str):
        return self

    def eq(self, column: str, value: object):
        self.filters.append((column, value))
        return self

    def order(self, column: str, desc=False):
        self.rows = sorted(self.rows, key=lambda row: row.get(column) or "", reverse=desc)
        return self

    def limit(self, limit: int):
        self.limit_value = limit
        return self

    def execute(self):
        rows = [
            row for row in self.rows
            if all(row.get(column) == value for column, value in self.filters)
        ]
        return SimpleNamespace(data=rows[:self.limit_value] if self.limit_value else rows)


class FakeSupabase:
    def __init__(self, tables: dict[str, list[dict]]) -> None:
        self.tables = tables

    def table(self, table: str) -> FakeQuery:
        return FakeQuery(list(self.tables.get(table, [])))


def healthy_tables() -> dict[str, list[dict]]:
    return {
        "sync_runs": [{
            "id": "run-1", "status": "SUCCESS", "started_at": "2026-08-16T10:00:00+00:00",
            "finished_at": "2026-08-16T10:01:00+00:00", "duration_ms": 60000,
            "accounts_total": 1, "accounts_success": 1, "accounts_partial": 0,
            "accounts_failed": 0,
        }],
        "meta_accounts": [{
            "id": "account-1", "meta_account_id": "123", "name": "Conta",
            "status": "ACTIVE", "last_synced_at": "2026-08-16T10:01:00+00:00",
            "last_entities_synced_at": "2026-08-16T10:01:00+00:00",
            "last_metrics_synced_at": "2026-08-16T10:01:00+00:00",
            "last_successful_sync_at": "2026-08-16T10:01:00+00:00",
        }],
        "integration_alerts": [],
    }


def test_meta_health_is_healthy_after_recent_success() -> None:
    result = MetaHealthService(  # type: ignore[arg-type]
        FakeSupabase(healthy_tables()), now=lambda: NOW
    ).check()
    assert result["status"] == "HEALTHY"
    assert result["stale_accounts"] == []
    assert result["token"] == {"status": "OK"}


def test_meta_health_is_degraded_for_stale_account() -> None:
    tables = healthy_tables()
    tables["meta_accounts"][0]["last_metrics_synced_at"] = "2026-08-14T09:00:00+00:00"
    result = MetaHealthService(  # type: ignore[arg-type]
        FakeSupabase(tables), stale_hours=26, now=lambda: NOW
    ).check()
    assert result["status"] == "DEGRADED"
    assert result["stale_accounts"][0]["meta_account_id"] == "123"


def test_meta_health_is_unhealthy_for_expired_token() -> None:
    tables = healthy_tables()
    tables["integration_alerts"] = [{
        "id": "alert-1", "alert_type": "TOKEN_EXPIRED", "severity": "CRITICAL",
        "title": "Token expirado", "message": "Renove", "status": "OPEN",
        "detected_at": "2026-08-16T11:00:00+00:00",
    }]
    result = MetaHealthService(  # type: ignore[arg-type]
        FakeSupabase(tables), now=lambda: NOW
    ).check()
    assert result["status"] == "UNHEALTHY"
    assert result["token"] == {"status": "EXPIRED"}


def test_meta_health_does_not_hide_failed_latest_run_with_fresh_entities() -> None:
    tables = healthy_tables()
    tables["sync_runs"].append({
        "id": "run-2", "status": "FAILED", "started_at": "2026-08-16T11:00:00+00:00",
        "finished_at": "2026-08-16T11:01:00+00:00", "duration_ms": 60000,
        "accounts_total": 1, "accounts_success": 0, "accounts_partial": 0,
        "accounts_failed": 1,
    })
    tables["meta_accounts"][0]["last_entities_synced_at"] = "2026-08-16T11:01:00+00:00"

    result = MetaHealthService(  # type: ignore[arg-type]
        FakeSupabase(tables), now=lambda: NOW
    ).check()

    assert result["status"] == "UNHEALTHY"
    assert result["latest_run"]["id"] == "run-2"
    assert result["latest_successful_run"]["id"] == "run-1"
