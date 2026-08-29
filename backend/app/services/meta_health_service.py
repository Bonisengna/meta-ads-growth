from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

from supabase import Client


class MetaHealthService:
    def __init__(
        self,
        client: Client,
        *,
        stale_hours: int = 26,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self.client = client
        self.stale_hours = stale_hours
        self.now = now

    def check(self) -> dict[str, Any]:
        latest_rows = (
            self.client.table("sync_runs")
            .select(
                "id,status,started_at,finished_at,duration_ms,accounts_total,"
                "accounts_success,accounts_partial,accounts_failed"
            )
            .order("started_at", desc=True)
            .limit(1)
            .execute()
            .data
            or []
        )
        successful_rows = (
            self.client.table("sync_runs")
            .select(
                "id,status,started_at,finished_at,duration_ms,accounts_total,"
                "accounts_success,accounts_partial,accounts_failed"
            )
            .eq("status", "SUCCESS")
            .order("started_at", desc=True)
            .limit(1)
            .execute()
            .data
            or []
        )
        accounts = (
            self.client.table("meta_accounts")
            .select(
                "id,meta_account_id,name,last_synced_at,last_entities_synced_at,"
                "last_metrics_synced_at,last_successful_sync_at"
            )
            .eq("status", "ACTIVE")
            .order("name")
            .execute()
            .data
            or []
        )
        alerts = (
            self.client.table("integration_alerts")
            .select("id,alert_type,severity,title,message,detected_at")
            .eq("status", "OPEN")
            .order("detected_at", desc=True)
            .execute()
            .data
            or []
        )
        cutoff = self.now() - timedelta(hours=self.stale_hours)
        stale_accounts = [
            {
                "id": row["id"],
                "meta_account_id": row["meta_account_id"],
                "name": row["name"],
                "last_entities_synced_at": row.get("last_entities_synced_at"),
                "last_metrics_synced_at": row.get("last_metrics_synced_at"),
                "last_successful_sync_at": row.get("last_successful_sync_at"),
            }
            for row in accounts
            if not row.get("last_metrics_synced_at")
            or parse_datetime(row["last_metrics_synced_at"]) < cutoff
        ]
        latest = latest_rows[0] if latest_rows else None
        token_expired = any(row["alert_type"] == "TOKEN_EXPIRED" for row in alerts)
        if token_expired or (latest and latest["status"] == "FAILED") or not latest:
            health_status = "UNHEALTHY"
        elif stale_accounts or latest["status"] in {"PARTIAL", "RUNNING"}:
            health_status = "DEGRADED"
        else:
            health_status = "HEALTHY"
        return {
            "status": health_status,
            "service": "meta",
            "checked_at": self.now().isoformat(),
            "stale_after_hours": self.stale_hours,
            "latest_run": latest,
            "latest_successful_run": successful_rows[0] if successful_rows else None,
            "active_accounts": len(accounts),
            "stale_accounts": stale_accounts,
            "open_alerts": alerts,
            "token": {"status": "EXPIRED" if token_expired else "OK"},
        }


def parse_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
