from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from supabase import Client

from app.models.settings import MetaIntegrationWrite, SystemCredentialsWrite
from app.services.meta_graph_client import MetaGraphClient


class SettingsService:
    def __init__(self, user_client: Client, service_client: Client) -> None:
        self.user_client = user_client
        self.service_client = service_client

    def read(self) -> dict[str, object]:
        admin = self._is_system_admin()
        access = self.user_client.table("user_client_access").select("client_id").eq("active", True).execute()
        client_ids = [str(row["client_id"]) for row in access.data or []]
        rows: list[dict[str, object]] = []
        if client_ids:
            rows.extend(
                self.service_client.table("integration_credentials")
                .select("client_id,provider,connection_name,status,config,last_validated_at,updated_at")
                .eq("provider", "META_CLIENT").in_("client_id", client_ids).execute().data or []
            )
        if admin:
            rows.extend(
                self.service_client.table("integration_credentials")
                .select("client_id,provider,connection_name,status,config,last_validated_at,updated_at")
                .in_("provider", ["META_SYSTEM", "OPENAI"]).execute().data or []
            )
        return {"system_admin": admin, "credentials": [self._safe_status(row) for row in rows]}

    def save_meta(self, payload: MetaIntegrationWrite) -> dict[str, object]:
        self._require_client_admin(payload.client_id)
        token = payload.access_token.get_secret_value()
        normalized = payload.ad_account_id.removeprefix("act_")
        with MetaGraphClient(token) as meta:
            accounts = meta.list_ad_accounts()
        account = next((item for item in accounts if str(item.get("account_id")) == normalized), None)
        if account is None:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Token sem acesso à conta informada.")
        config = {
            "ad_account_id": normalized,
            "business_id": payload.business_id,
            "account_name": account.get("name"),
            "currency": account.get("currency"),
            "timezone": account.get("timezone_name"),
            "permissions": ["ads_read"],
        }
        row = self._upsert("META_CLIENT", payload.connection_name, token, config, payload.client_id)
        return self._safe_status(row)

    def save_system(self, payload: SystemCredentialsWrite) -> list[dict[str, object]]:
        self._require_system_admin()
        saved = []
        if payload.meta_app_secret is not None:
            if not payload.meta_app_id:
                raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Meta App ID é obrigatório.")
            saved.append(self._safe_status(self._upsert(
                "META_SYSTEM", "Meta Application", payload.meta_app_secret.get_secret_value(),
                {"meta_app_id": payload.meta_app_id, "system_user_id": payload.system_user_id,
                 "graph_version": payload.graph_version}, None,
            )))
        if payload.openai_api_key is not None:
            saved.append(self._safe_status(self._upsert(
                "OPENAI", "OpenAI", payload.openai_api_key.get_secret_value(),
                {"credential_scope": "SYSTEM"}, None,
            )))
        if not saved:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Informe ao menos um segredo para substituir.")
        return saved

    def _upsert(self, provider: str, name: str, secret: str, config: dict[str, object], client_id: UUID | None) -> dict[str, object]:
        query = self.service_client.table("integration_credentials").select("id,secret_id")
        query = query.eq("provider", provider)
        query = query.eq("client_id", str(client_id)) if client_id else query.is_("client_id", "null")
        existing = query.limit(1).execute().data or []
        secret_id = existing[0]["secret_id"] if existing else None
        stored = self.service_client.rpc("store_vault_secret", {
            "p_secret_value": secret, "p_secret_name": f"descompliads-{provider.lower()}-{uuid4()}",
            "p_existing_secret_id": secret_id,
        }).execute().data
        now = datetime.now(UTC).isoformat()
        values = {"provider": provider, "client_id": str(client_id) if client_id else None,
                  "connection_name": name, "secret_id": stored, "config": config,
                  "status": "VALID" if provider == "META_CLIENT" else "CONFIGURED",
                  "last_validated_at": now if provider == "META_CLIENT" else None,
                  "updated_by": self._current_user_id(), "updated_at": now}
        if existing:
            response = self.service_client.table("integration_credentials").update(values).eq("id", existing[0]["id"]).execute()
        else:
            response = self.service_client.table("integration_credentials").insert(values).execute()
        return response.data[0]

    def _is_system_admin(self) -> bool:
        response = self.user_client.table("system_admins").select("user_id").limit(1).execute()
        return bool(response.data)

    def _current_user_id(self) -> str | None:
        admin = self.user_client.table("system_admins").select("user_id").limit(1).execute().data or []
        if admin:
            return str(admin[0]["user_id"])
        access = self.user_client.table("user_client_access").select("user_id").eq("active", True).limit(1).execute().data or []
        return str(access[0]["user_id"]) if access else None

    def _require_system_admin(self) -> None:
        if not self._is_system_admin():
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Apenas Superadmin pode alterar credenciais do sistema.")

    def _require_client_admin(self, client_id: UUID) -> None:
        response = (self.user_client.table("user_client_access").select("role")
                    .eq("client_id", str(client_id)).eq("active", True).limit(1).execute())
        if not response.data or response.data[0]["role"] not in {"OWNER", "ADMIN"}:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Apenas OWNER ou ADMIN pode alterar a integração Meta.")

    @staticmethod
    def _safe_status(row: dict[str, object]) -> dict[str, object]:
        return {"provider": row["provider"], "configured": True, "status": row.get("status"),
                "connection_name": row.get("connection_name"), "client_id": row.get("client_id"),
                "config": row.get("config") or {}, "last_validated_at": row.get("last_validated_at"),
                "updated_at": row.get("updated_at")}
