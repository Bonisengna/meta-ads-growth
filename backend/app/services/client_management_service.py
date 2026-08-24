import re
import unicodedata
from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from supabase import Client

from app.models.settings import ClientCreate, ClientUpdate


CLIENT_PROFILE_COLUMNS = (
    "id,name,slug,status,legal_name,tax_id_type,tax_id,segment,niche,business_model,"
    "primary_audience,website,contact_name,contact_email,contact_phone,city,state,"
    "country_code,timezone,currency,primary_goal,monthly_media_budget,onboarding_status,"
    "notes,created_at,updated_at"
)


class ClientManagementService:
    def __init__(self, user_client: Client, service_client: Client) -> None:
        self.user_client = user_client
        self.service_client = service_client

    def list_clients(self) -> list[dict[str, object]]:
        admin_id = self._system_admin_id()
        access_rows = (
            self.user_client.table("user_client_access")
            .select("client_id,role")
            .eq("active", True)
            .execute()
            .data
            or []
        )
        roles = {str(row["client_id"]): str(row["role"]) for row in access_rows}
        source = self.service_client if admin_id else self.user_client
        rows = source.table("clients").select(CLIENT_PROFILE_COLUMNS).order("name").execute().data or []
        return [
            self._read_row(row, bool(admin_id) or roles.get(str(row["id"])) in {"OWNER", "ADMIN"})
            for row in rows
        ]

    def create(self, payload: ClientCreate) -> dict[str, object]:
        owner_id = self._require_system_admin()
        values = payload.model_dump(mode="json")
        values["slug"] = self._available_slug(payload.name)
        response = self.service_client.table("clients").insert(values).execute()
        row = response.data[0]
        try:
            self.service_client.table("user_client_access").insert(
                {"user_id": owner_id, "client_id": row["id"], "role": "OWNER", "active": True}
            ).execute()
        except Exception:
            # Desfaz somente uma criação incompleta, antes de existir histórico.
            self.service_client.table("clients").delete().eq("id", row["id"]).execute()
            raise
        return self._read_row(row, True)

    def update(self, client_id: UUID, payload: ClientUpdate) -> dict[str, object]:
        self._require_client_manager(client_id)
        values = payload.model_dump(mode="json", exclude_unset=True)
        if values:
            values["updated_at"] = datetime.now(UTC).isoformat()
            response = self.service_client.table("clients").update(values).eq("id", str(client_id)).execute()
            if not response.data:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Cliente não encontrado.")
            return self._read_row(response.data[0], True)
        return self._get(client_id, True)

    def _get(self, client_id: UUID, can_manage: bool) -> dict[str, object]:
        rows = self.service_client.table("clients").select(CLIENT_PROFILE_COLUMNS).eq("id", str(client_id)).limit(1).execute().data or []
        if not rows:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Cliente não encontrado.")
        return self._read_row(rows[0], can_manage)

    def _require_client_manager(self, client_id: UUID) -> None:
        if self._system_admin_id():
            return
        rows = self.user_client.table("user_client_access").select("role").eq("client_id", str(client_id)).eq("active", True).limit(1).execute().data or []
        if not rows or rows[0]["role"] not in {"OWNER", "ADMIN"}:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Apenas OWNER ou ADMIN pode alterar este cliente.")

    def _require_system_admin(self) -> str:
        admin_id = self._system_admin_id()
        if not admin_id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Apenas o administrador do sistema pode cadastrar um novo cliente.")
        return admin_id

    def _system_admin_id(self) -> str | None:
        rows = self.user_client.table("system_admins").select("user_id").limit(1).execute().data or []
        return str(rows[0]["user_id"]) if rows else None

    def _available_slug(self, name: str) -> str:
        base = self.slugify(name)
        rows = self.service_client.table("clients").select("id").eq("slug", base).limit(1).execute().data or []
        return f"{base}-{uuid4().hex[:6]}" if rows else base

    @staticmethod
    def slugify(value: str) -> str:
        normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
        slug = re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-")
        return slug[:100] or f"cliente-{uuid4().hex[:8]}"

    @staticmethod
    def _read_row(row: dict[str, object], can_manage: bool) -> dict[str, object]:
        defaults: dict[str, object] = {
            "legal_name": None, "tax_id_type": "CNPJ", "tax_id": None,
            "segment": "Não informado", "niche": "Não informado", "business_model": "B2C",
            "primary_audience": None, "website": None, "contact_name": None,
            "contact_email": None, "contact_phone": None, "city": None, "state": None,
            "country_code": "BR", "timezone": "America/Sao_Paulo", "currency": "BRL",
            "primary_goal": None, "monthly_media_budget": None, "onboarding_status": "NEW",
            "notes": None,
        }
        return {**defaults, **row, "can_manage": can_manage}
