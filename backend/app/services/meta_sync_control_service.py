from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from supabase import Client

from app.services.meta_sync_runner import safe_error


REQUEST_FIELDS = (
    "id,client_id,requested_by,lookback_days,status,recovery_of,sync_run_id,created_at,"
    "started_at,finished_at,error_summary"
)
RUN_FIELDS = (
    "id,status,trigger_source,client_id,recovery_of,lookback_days,started_at,"
    "finished_at,duration_ms,accounts_total,accounts_success,accounts_partial,"
    "accounts_failed,current_stage,current_account_name,progress_current,"
    "progress_total,result,error_summary"
)


class MetaSyncControlService:
    def __init__(self, user_client: Client, service_client: Client) -> None:
        self.user_client = user_client
        self.service_client = service_client

    def create_request(
        self, client_id: UUID, lookback_days: int, recovery_of: UUID | None = None
    ) -> dict[str, object]:
        user_id = self._require_client_manager(client_id)
        values = {
            "client_id": str(client_id),
            "requested_by": user_id,
            "lookback_days": lookback_days,
            "recovery_of": str(recovery_of) if recovery_of else None,
            "status": "PENDING",
        }
        try:
            response = self.service_client.table("sync_requests").insert(values).execute()
        except Exception as exc:
            if "sync_requests_one_open_client" in str(exc) or "duplicate key" in str(exc):
                raise HTTPException(
                    status.HTTP_409_CONFLICT,
                    "Já existe uma sincronização aguardando ou em andamento para este cliente.",
                ) from exc
            raise
        return (response.data or [])[0]

    def recover(self, run_id: UUID, selected_client_id: UUID | None = None) -> dict[str, object]:
        rows = (
            self.service_client.table("sync_runs")
            .select("id,status,client_id,lookback_days")
            .eq("id", str(run_id)).limit(1).execute().data or []
        )
        if not rows:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Execução não encontrada.")
        run = rows[0]
        if run["status"] not in {"FAILED", "PARTIAL"}:
            raise HTTPException(status.HTTP_409_CONFLICT, "Somente uma execução com falha ou parcial pode ser reprocessada.")
        run_client_id = UUID(str(run["client_id"])) if run.get("client_id") else None
        if run_client_id and selected_client_id and run_client_id != selected_client_id:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "A execução não pertence ao cliente selecionado.")
        target_client_id = run_client_id or selected_client_id
        if not target_client_id:
            if not self._is_system_admin():
                raise HTTPException(status.HTTP_403_FORBIDDEN, "Somente Superadmin pode reprocessar uma execução global.")
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Selecione um cliente para reprocessar esta execução global.")
        if not run_client_id and not self._is_system_admin():
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Somente Superadmin pode reprocessar uma execução global.")
        return self.create_request(target_client_id, int(run["lookback_days"]), run_id)

    def list_requests(self, limit: int = 10) -> list[dict[str, object]]:
        client_ids = self._visible_client_ids()
        if not client_ids:
            return []
        return (
            self.service_client.table("sync_requests").select(REQUEST_FIELDS)
            .in_("client_id", client_ids).order("created_at", desc=True)
            .limit(limit).execute().data or []
        )

    def list_runs(self, limit: int = 10) -> list[dict[str, object]]:
        client_ids = self._visible_client_ids()
        query = self.service_client.table("sync_runs").select(RUN_FIELDS)
        if not self._is_system_admin():
            if not client_ids:
                return []
            query = query.in_("client_id", client_ids)
        return query.order("started_at", desc=True).limit(limit).execute().data or []

    def _visible_client_ids(self) -> list[str]:
        if self._is_system_admin():
            rows = self.service_client.table("clients").select("id").execute().data or []
            return [str(row["id"]) for row in rows]
        rows = (
            self.user_client.table("user_client_access").select("client_id")
            .eq("active", True).execute().data or []
        )
        return [str(row["client_id"]) for row in rows]

    def _is_system_admin(self) -> bool:
        return bool(self.user_client.table("system_admins").select("user_id").limit(1).execute().data)

    def _require_client_manager(self, client_id: UUID) -> str | None:
        admin = self.user_client.table("system_admins").select("user_id").limit(1).execute().data or []
        if admin:
            return str(admin[0]["user_id"])
        access = (
            self.user_client.table("user_client_access").select("user_id,role")
            .eq("client_id", str(client_id)).eq("active", True).limit(1).execute().data or []
        )
        if not access or access[0]["role"] not in {"OWNER", "ADMIN"}:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Apenas OWNER ou ADMIN pode iniciar a sincronização.")
        return str(access[0]["user_id"])


def claim_next_request(service_client: Client) -> dict[str, object] | None:
    rows = (
        service_client.table("sync_requests").select(REQUEST_FIELDS)
        .eq("status", "PENDING").order("created_at").limit(1).execute().data or []
    )
    if not rows:
        return None
    request = rows[0]
    now = datetime.now(UTC).isoformat()
    claimed = (
        service_client.table("sync_requests").update({"status": "RUNNING", "started_at": now})
        .eq("id", request["id"]).eq("status", "PENDING").execute().data or []
    )
    return claimed[0] if claimed else None


def finish_request(service_client: Client, request_id: str, result: dict[str, object] | None, error: Exception | None = None) -> None:
    now = datetime.now(UTC).isoformat()
    values: dict[str, object] = {"finished_at": now}
    if result is not None:
        values.update({"status": result["status"], "sync_run_id": result["run_id"], "error_summary": result.get("error")})
    else:
        values.update({"status": "FAILED", "error_summary": safe_error(error or RuntimeError("Falha desconhecida"))})
    service_client.table("sync_requests").update(values).eq("id", request_id).execute()
