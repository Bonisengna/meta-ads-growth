from decimal import Decimal
from uuid import UUID

from supabase import Client

from app.models.entities import EntityStatus


CLIENT_COLUMNS = "id,name,slug,status,created_at,updated_at"
META_ACCOUNT_COLUMNS = (
    "id,client_id,meta_account_id,name,currency,timezone,status,last_synced_at,"
    "created_at,updated_at"
)
CAMPAIGN_COLUMNS = (
    "id,meta_account_id,meta_campaign_id,name,objective,status,meta_created_at,"
    "meta_updated_at,created_at,updated_at"
)


class EntityNotFoundError(LookupError):
    def __init__(self, entity: str, entity_id: UUID) -> None:
        self.entity = entity
        self.entity_id = entity_id
        super().__init__(f"{entity} {entity_id} não encontrado")


class ClientService:
    def __init__(self, client: Client) -> None:
        self.client = client

    def list_clients(
        self, page: int, page_size: int, entity_status: EntityStatus | None = None
    ) -> dict[str, object]:
        query = self.client.table("clients").select(CLIENT_COLUMNS, count="exact")
        if entity_status:
            query = query.eq("status", entity_status)
        response = query.order("name").range(*page_range(page, page_size)).execute()
        return page_result(response.data, response.count, page, page_size)

    def get_client(self, client_id: UUID) -> dict[str, object]:
        response = (
            self.client.table("clients")
            .select(CLIENT_COLUMNS)
            .eq("id", str(client_id))
            .limit(1)
            .execute()
        )
        rows = response.data or []
        if not rows:
            raise EntityNotFoundError("Cliente", client_id)
        return rows[0]


class MetaAccountService:
    def __init__(self, client: Client) -> None:
        self.client = client

    def list_meta_accounts(
        self,
        page: int,
        page_size: int,
        entity_status: EntityStatus | None = None,
        client_id: UUID | None = None,
    ) -> dict[str, object]:
        query = self.client.table("meta_accounts").select(
            META_ACCOUNT_COLUMNS, count="exact"
        )
        if entity_status:
            query = query.eq("status", entity_status)
        if client_id:
            query = query.eq("client_id", str(client_id))
        response = query.order("name").range(*page_range(page, page_size)).execute()
        return page_result(response.data, response.count, page, page_size)


class CampaignService:
    def __init__(self, client: Client) -> None:
        self.client = client

    def list_campaigns(
        self,
        page: int,
        page_size: int,
        entity_status: EntityStatus | None = None,
        meta_account_id: UUID | None = None,
    ) -> dict[str, object]:
        query = self.client.table("campaigns").select(CAMPAIGN_COLUMNS, count="exact")
        if entity_status:
            query = query.eq("status", entity_status)
        if meta_account_id:
            query = query.eq("meta_account_id", str(meta_account_id))
        response = query.order("name").range(*page_range(page, page_size)).execute()
        return page_result(response.data, response.count, page, page_size)

    def get_campaign(self, campaign_id: UUID) -> dict[str, object]:
        response = (
            self.client.table("campaigns")
            .select(CAMPAIGN_COLUMNS)
            .eq("id", str(campaign_id))
            .limit(1)
            .execute()
        )
        rows = response.data or []
        if not rows:
            raise EntityNotFoundError("Campanha", campaign_id)
        return rows[0]


class DashboardService:
    ENTITY_TABLES = ("clients", "meta_accounts", "campaigns", "adsets", "ads")

    def __init__(self, client: Client) -> None:
        self.client = client

    def get_dashboard(self) -> dict[str, object]:
        counts = {table: self._count(table) for table in self.ENTITY_TABLES}
        metrics_response = self.client.table("campaign_metrics").select("spend,leads").execute()
        metrics = metrics_response.data or []
        spend = sum((Decimal(str(row.get("spend") or 0)) for row in metrics), Decimal("0"))
        leads = sum(int(row.get("leads") or 0) for row in metrics)

        return {
            **counts,
            "metrics": {
                "spend": spend,
                "leads": leads,
                "cpl": spend / leads if leads else None,
            },
        }

    def _count(self, table: str) -> int:
        response = self.client.table(table).select("id", count="exact", head=True).execute()
        return response.count or 0


def page_range(page: int, page_size: int) -> tuple[int, int]:
    start = (page - 1) * page_size
    return start, start + page_size - 1


def page_result(data: object, count: int | None, page: int, page_size: int) -> dict[str, object]:
    total = count or 0
    return {
        "items": data or [],
        "page": page,
        "page_size": page_size,
        "total": total,
        "pages": (total + page_size - 1) // page_size,
    }
