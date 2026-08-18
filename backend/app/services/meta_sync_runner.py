import re
import time
from collections.abc import Callable
from datetime import UTC, date, datetime, timedelta
from typing import Any, TypeVar

from supabase import Client

from app.services.meta_graph_client import MetaGraphClient, MetaGraphError
from app.services.meta_sync_service import MetaSyncService


T = TypeVar("T")
RUN_SCOPE = "META_ALL"


class SyncAlreadyRunningError(RuntimeError):
    pass


class MetaSyncRunner:
    """Executa todas as contas ativas com protocolo, retry e exclusão mútua."""

    def __init__(
        self,
        supabase: Client,
        meta: MetaGraphClient,
        *,
        max_attempts: int = 3,
        retry_delay_seconds: float = 2.0,
        lock_minutes: int = 120,
        sleep: Callable[[float], None] = time.sleep,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        if max_attempts < 1:
            raise ValueError("max_attempts deve ser maior ou igual a 1")
        if lock_minutes < 1:
            raise ValueError("lock_minutes deve ser maior ou igual a 1")
        self.supabase = supabase
        self.meta = meta
        self.max_attempts = max_attempts
        self.retry_delay_seconds = retry_delay_seconds
        self.lock_minutes = lock_minutes
        self.sleep = sleep
        self.now = now

    def run(self, lookback_days: int = 3) -> dict[str, Any]:
        if not 1 <= lookback_days <= 120:
            raise ValueError("lookback_days deve estar entre 1 e 120")

        run = self._acquire(lookback_days)
        started_at = datetime.fromisoformat(run["started_at"])
        try:
            accounts = self._active_accounts()
            results = [self._sync_account(account, lookback_days) for account in accounts]
            successful = sum(result["status"] == "SUCCESS" for result in results)
            failed = len(results) - successful
            status = "SUCCESS" if failed == 0 else "FAILED" if successful == 0 else "PARTIAL"
            entity_changes = aggregate_entity_changes(results)
            summary = {
                "run_id": run["id"],
                "status": status,
                "lookback_days": lookback_days,
                "accounts_total": len(accounts),
                "accounts_success": successful,
                "accounts_failed": failed,
                "entity_changes": entity_changes,
                "accounts": results,
            }
            self._update_token_alert(results, successful > 0)
            self._finish(run["id"], started_at, summary)
            return summary
        except Exception as exc:
            summary = {
                "run_id": run["id"],
                "status": "FAILED",
                "lookback_days": lookback_days,
                "accounts_total": 0,
                "accounts_success": 0,
                "accounts_failed": 0,
                "accounts": [],
                "error": safe_error(exc),
            }
            self._finish(run["id"], started_at, summary)
            raise

    def _active_accounts(self) -> list[dict[str, Any]]:
        response = (
            self.supabase.table("meta_accounts")
            .select("id,client_id,meta_account_id,name")
            .eq("status", "ACTIVE")
            .order("name")
            .execute()
        )
        return response.data or []

    def _sync_account(self, account: dict[str, Any], lookback_days: int) -> dict[str, Any]:
        account_id = str(account["meta_account_id"])
        today = self.now().date()
        since = today - timedelta(days=lookback_days - 1)
        sync = MetaSyncService(self.supabase, self.meta)
        try:
            entities, entity_attempts = retry_transient(
                lambda: sync.sync_account(account["client_id"], account_id),
                self.max_attempts,
                self.retry_delay_seconds,
                self.sleep,
            )
            metrics, metric_attempts = retry_transient(
                lambda: sync.sync_daily_metrics(account_id, since, today),
                self.max_attempts,
                self.retry_delay_seconds,
                self.sleep,
            )
            breakdowns, breakdown_attempts = retry_transient(
                lambda: sync.sync_breakdown_metrics(account_id, since, today),
                self.max_attempts,
                self.retry_delay_seconds,
                self.sleep,
            )
            return {
                "meta_account_id": account_id,
                "name": account.get("name"),
                "status": "SUCCESS",
                "period": {"date_from": since.isoformat(), "date_to": today.isoformat()},
                "attempts": {"entities": entity_attempts, "metrics": metric_attempts,
                             "breakdowns": breakdown_attempts},
                "entities": entities,
                "metrics": metrics,
                "breakdowns": breakdowns,
            }
        except Exception as exc:
            result = {
                "meta_account_id": account_id,
                "name": account.get("name"),
                "status": "FAILED",
                "period": {"date_from": since.isoformat(), "date_to": today.isoformat()},
                "error": safe_error(exc),
            }
            if isinstance(exc, MetaGraphError):
                result["error_code"] = exc.code
                result["http_status"] = exc.status_code
            return result

    def _update_token_alert(self, results: list[dict[str, Any]], has_success: bool) -> None:
        token_errors = [result for result in results if result.get("error_code") == 190]
        query = (
            self.supabase.table("integration_alerts")
            .select("id")
            .eq("alert_type", "TOKEN_EXPIRED")
            .eq("scope_key", "GLOBAL")
            .eq("status", "OPEN")
            .limit(1)
            .execute()
        )
        open_rows = query.data or []
        if token_errors and not open_rows:
            (
                self.supabase.table("integration_alerts")
                .insert(
                    {
                        "scope_key": "GLOBAL",
                        "alert_type": "TOKEN_EXPIRED",
                        "severity": "CRITICAL",
                        "title": "Token da Meta expirado ou inválido",
                        "message": "A Meta rejeitou a credencial. Gere ou renove o token do backend.",
                        "status": "OPEN",
                    }
                )
                .execute()
            )
        elif has_success and not token_errors and open_rows:
            (
                self.supabase.table("integration_alerts")
                .update(
                    {
                        "status": "RESOLVED",
                        "resolved_at": self.now().isoformat(),
                        "updated_at": self.now().isoformat(),
                    }
                )
                .eq("id", open_rows[0]["id"])
                .execute()
            )

    def _acquire(self, lookback_days: int) -> dict[str, Any]:
        now = self.now()
        # Libera uma execução abandonada somente depois do vencimento da trava.
        (
            self.supabase.table("sync_runs")
            .update(
                {
                    "status": "FAILED",
                    "finished_at": now.isoformat(),
                    "error_summary": "Execução interrompida; trava expirada.",
                }
            )
            .eq("scope", RUN_SCOPE)
            .eq("status", "RUNNING")
            .lt("lock_expires_at", now.isoformat())
            .execute()
        )
        try:
            response = (
                self.supabase.table("sync_runs")
                .insert(
                    {
                        "scope": RUN_SCOPE,
                        "status": "RUNNING",
                        "started_at": now.isoformat(),
                        "lock_expires_at": (now + timedelta(minutes=self.lock_minutes)).isoformat(),
                        "lookback_days": lookback_days,
                    }
                )
                .execute()
            )
        except Exception as exc:
            running = (
                self.supabase.table("sync_runs")
                .select("id")
                .eq("scope", RUN_SCOPE)
                .eq("status", "RUNNING")
                .limit(1)
                .execute()
            )
            if running.data:
                raise SyncAlreadyRunningError(
                    "Já existe uma sincronização Meta em andamento."
                ) from exc
            raise
        rows = response.data or []
        if not rows:
            raise RuntimeError("Supabase não retornou o registro da execução.")
        return rows[0]

    def _finish(self, run_id: str, started_at: datetime, summary: dict[str, Any]) -> None:
        finished_at = self.now()
        duration_ms = max(0, int((finished_at - started_at).total_seconds() * 1000))
        error = summary.get("error")
        if not error:
            errors = [row.get("error") for row in summary["accounts"] if row.get("error")]
            error = "; ".join(errors)[:2000] if errors else None
        (
            self.supabase.table("sync_runs")
            .update(
                {
                    "status": summary["status"],
                    "finished_at": finished_at.isoformat(),
                    "duration_ms": duration_ms,
                    "accounts_total": summary["accounts_total"],
                    "accounts_success": summary["accounts_success"],
                    "accounts_failed": summary["accounts_failed"],
                    "result": summary,
                    "error_summary": error,
                }
            )
            .eq("id", run_id)
            .execute()
        )


def retry_transient(
    operation: Callable[[], T],
    max_attempts: int,
    delay_seconds: float,
    sleep: Callable[[float], None] = time.sleep,
) -> tuple[T, int]:
    for attempt in range(1, max_attempts + 1):
        try:
            return operation(), attempt
        except MetaGraphError as exc:
            if attempt == max_attempts or not is_transient_meta_error(exc):
                raise
            sleep(delay_seconds * (2 ** (attempt - 1)))
    raise AssertionError("loop de retry terminou sem resultado")


def is_transient_meta_error(exc: MetaGraphError) -> bool:
    return exc.status_code is None or exc.status_code in {408, 425, 429} or (
        exc.status_code >= 500
    )


def safe_error(exc: Exception) -> str:
    message = str(exc) or exc.__class__.__name__
    message = re.sub(r"(?i)(access[_ -]?token|app[_ -]?secret)=?[^\s&,]+", r"\1=[REDACTED]", message)
    message = re.sub(r"(?i)bearer\s+[A-Za-z0-9._-]+", "Bearer [REDACTED]", message)
    return message[:2000]


def aggregate_entity_changes(results: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    totals = {
        entity: {"imported": 0, "updated": 0, "archived": 0}
        for entity in ("meta_accounts", "campaigns", "adsets", "ads")
    }
    for result in results:
        changes = (result.get("entities") or {}).get("changes") or {}
        for entity, values in changes.items():
            if entity not in totals:
                continue
            for action in totals[entity]:
                totals[entity][action] += int(values.get(action, 0))
    return totals
