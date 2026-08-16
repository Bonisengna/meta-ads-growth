from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
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
ADSET_COLUMNS = (
    "id,campaign_id,meta_adset_id,name,status,optimization_goal,billing_event,"
    "daily_budget,lifetime_budget,meta_created_at,meta_updated_at,created_at,updated_at"
)
AD_COLUMNS = (
    "id,adset_id,meta_ad_id,name,status,creative_id,meta_created_at,meta_updated_at,"
    "created_at,updated_at"
)
METRIC_COLUMNS = (
    "id,{entity_column},metric_date,spend,impressions,reach,clicks,link_clicks,ctr,cpc,"
    "cpm,frequency,leads,cpl,conversations,cost_per_conversation,created_at,updated_at"
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


class AdsetService:
    def __init__(self, client: Client) -> None:
        self.client = client

    def list_adsets(
        self,
        page: int,
        page_size: int,
        entity_status: EntityStatus | None = None,
        campaign_id: UUID | None = None,
    ) -> dict[str, object]:
        query = self.client.table("adsets").select(ADSET_COLUMNS, count="exact")
        if entity_status:
            query = query.eq("status", entity_status)
        if campaign_id:
            query = query.eq("campaign_id", str(campaign_id))
        response = query.order("name").range(*page_range(page, page_size)).execute()
        return page_result(response.data, response.count, page, page_size)

    def get_adset(self, adset_id: UUID) -> dict[str, object]:
        response = (
            self.client.table("adsets")
            .select(ADSET_COLUMNS)
            .eq("id", str(adset_id))
            .limit(1)
            .execute()
        )
        rows = response.data or []
        if not rows:
            raise EntityNotFoundError("Conjunto", adset_id)
        return rows[0]


class AdService:
    def __init__(self, client: Client) -> None:
        self.client = client

    def list_ads(
        self,
        page: int,
        page_size: int,
        entity_status: EntityStatus | None = None,
        adset_id: UUID | None = None,
    ) -> dict[str, object]:
        query = self.client.table("ads").select(AD_COLUMNS, count="exact")
        if entity_status:
            query = query.eq("status", entity_status)
        if adset_id:
            query = query.eq("adset_id", str(adset_id))
        response = query.order("name").range(*page_range(page, page_size)).execute()
        return page_result(response.data, response.count, page, page_size)

    def get_ad(self, ad_id: UUID) -> dict[str, object]:
        response = (
            self.client.table("ads").select(AD_COLUMNS).eq("id", str(ad_id)).limit(1).execute()
        )
        rows = response.data or []
        if not rows:
            raise EntityNotFoundError("Anúncio", ad_id)
        return rows[0]


class MetricService:
    LEVELS = {
        "campaigns": ("campaign_metrics", "campaign_id"),
        "adsets": ("adset_metrics", "adset_id"),
        "ads": ("ad_metrics", "ad_id"),
    }

    def __init__(self, client: Client) -> None:
        self.client = client

    def list_metrics(
        self,
        level: str,
        date_from: date,
        date_to: date,
        page: int,
        page_size: int,
        entity_id: UUID | None = None,
    ) -> dict[str, object]:
        table, entity_column = self.LEVELS[level]
        query = (
            self.client.table(table)
            .select(METRIC_COLUMNS.format(entity_column=entity_column), count="exact")
            .gte("metric_date", date_from.isoformat())
            .lte("metric_date", date_to.isoformat())
        )
        if entity_id:
            query = query.eq(entity_column, str(entity_id))
        response = (
            query.order("metric_date", desc=True)
            .range(*page_range(page, page_size))
            .execute()
        )
        return page_result(response.data, response.count, page, page_size)


class DashboardService:
    ENTITY_TABLES = ("clients", "meta_accounts", "campaigns", "adsets", "ads")

    def __init__(self, client: Client) -> None:
        self.client = client

    def get_dashboard(
        self,
        *,
        days: int = 30,
        date_from: date | None = None,
        date_to: date | None = None,
        client_id: UUID | None = None,
        meta_account_id: UUID | None = None,
        campaign_id: UUID | None = None,
    ) -> dict[str, object]:
        current, previous = resolve_periods(days, date_from, date_to)
        scope = self._scope(client_id, meta_account_id, campaign_id)
        current_metrics = self._aggregate(current[0], current[1], scope["campaign_ids"])
        previous_metrics = self._aggregate(previous[0], previous[1], scope["campaign_ids"])

        return {
            "clients": scope["clients"],
            "meta_accounts": len(scope["account_ids"]),
            "campaigns": len(scope["campaign_ids"]),
            "adsets": len(scope["adset_ids"]),
            "ads": scope["ads"],
            "period": period_payload(*current),
            "previous_period": period_payload(*previous),
            "metrics": current_metrics,
            "previous_metrics": previous_metrics,
            "change_percent": compare_metrics(current_metrics, previous_metrics),
        }

    def _scope(
        self,
        client_id: UUID | None,
        meta_account_id: UUID | None,
        campaign_id: UUID | None,
    ) -> dict[str, object]:
        client_query = self.client.table("clients").select("id")
        if client_id:
            client_query = client_query.eq("id", str(client_id))
        client_ids = row_ids(client_query.execute().data)

        account_query = self.client.table("meta_accounts").select("id,client_id")
        if client_id:
            account_query = account_query.eq("client_id", str(client_id))
        if meta_account_id:
            account_query = account_query.eq("id", str(meta_account_id))
        account_rows = account_query.execute().data or []
        account_ids = row_ids(account_rows)

        campaign_query = self.client.table("campaigns").select("id,meta_account_id")
        campaign_rows: list[dict[str, object]] = []
        if account_ids or client_id or meta_account_id:
            if not account_ids:
                campaign_ids: list[str] = []
            else:
                campaign_query = campaign_query.in_("meta_account_id", account_ids)
                if campaign_id:
                    campaign_query = campaign_query.eq("id", str(campaign_id))
                campaign_rows = campaign_query.execute().data or []
                campaign_ids = row_ids(campaign_rows)
        else:
            if campaign_id:
                campaign_query = campaign_query.eq("id", str(campaign_id))
            campaign_rows = campaign_query.execute().data or []
            campaign_ids = row_ids(campaign_rows)

        if campaign_id:
            scoped_account_ids = {
                str(row["meta_account_id"])
                for row in campaign_rows
                if row.get("meta_account_id") is not None
            }
            account_rows = [
                row for row in account_rows if str(row.get("id")) in scoped_account_ids
            ]
            account_ids = row_ids(account_rows)

        if meta_account_id or campaign_id:
            scoped_client_ids = {
                str(row["client_id"])
                for row in account_rows
                if row.get("client_id") is not None
            }
            client_ids = [value for value in client_ids if value in scoped_client_ids]

        adset_query = self.client.table("adsets").select("id,campaign_id")
        if campaign_ids:
            adset_ids = row_ids(adset_query.in_("campaign_id", campaign_ids).execute().data)
        else:
            adset_ids = []
        ads = 0
        if adset_ids:
            response = (
                self.client.table("ads")
                .select("id", count="exact", head=True)
                .in_("adset_id", adset_ids)
                .execute()
            )
            ads = response.count or 0

        return {
            "clients": len(client_ids),
            "account_ids": account_ids,
            "campaign_ids": campaign_ids,
            "adset_ids": adset_ids,
            "ads": ads,
        }

    def _aggregate(
        self, date_from: date, date_to: date, campaign_ids: list[str]
    ) -> dict[str, object]:
        if not campaign_ids:
            return aggregate_metrics([])
        rows: list[dict[str, object]] = []
        batch_size = 1000
        offset = 0
        while True:
            response = (
                self.client.table("campaign_metrics")
                .select("spend,impressions,clicks,leads,conversations")
                .gte("metric_date", date_from.isoformat())
                .lte("metric_date", date_to.isoformat())
                .in_("campaign_id", campaign_ids)
                .range(offset, offset + batch_size - 1)
                .execute()
            )
            batch = response.data or []
            rows.extend(batch)
            if len(batch) < batch_size:
                break
            offset += batch_size
        return aggregate_metrics(rows)


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


def resolve_periods(
    days: int, date_from: date | None = None, date_to: date | None = None
) -> tuple[tuple[date, date], tuple[date, date]]:
    if (date_from is None) != (date_to is None):
        raise ValueError("date_from e date_to devem ser informados juntos")
    if date_from and date_to:
        if date_from > date_to:
            raise ValueError("date_from não pode ser posterior a date_to")
        current = (date_from, date_to)
    else:
        end = date.today()
        current = (end - timedelta(days=days - 1), end)
    duration = (current[1] - current[0]).days + 1
    previous_end = current[0] - timedelta(days=1)
    previous = (previous_end - timedelta(days=duration - 1), previous_end)
    return current, previous


def period_payload(date_from: date, date_to: date) -> dict[str, object]:
    return {
        "date_from": date_from,
        "date_to": date_to,
        "days": (date_to - date_from).days + 1,
    }


def aggregate_metrics(rows: list[dict[str, object]]) -> dict[str, object]:
    spend = sum((Decimal(str(row.get("spend") or 0)) for row in rows), Decimal("0"))
    impressions = sum(int(row.get("impressions") or 0) for row in rows)
    clicks = sum(int(row.get("clicks") or 0) for row in rows)
    leads = sum(int(row.get("leads") or 0) for row in rows)
    conversations = sum(int(row.get("conversations") or 0) for row in rows)
    return {
        "spend": spend,
        "impressions": impressions,
        "clicks": clicks,
        "leads": leads,
        "conversations": conversations,
        "cpl": safe_divide(spend, Decimal(leads)),
        "ctr": safe_divide(Decimal(clicks) * 100, Decimal(impressions)),
        "cpc": safe_divide(spend, Decimal(clicks)),
        "cpm": safe_divide(spend * 1000, Decimal(impressions)),
    }


def compare_metrics(
    current: dict[str, object], previous: dict[str, object]
) -> dict[str, Decimal | None]:
    return {
        key: percent_change(current.get(key), previous.get(key))
        for key in (
            "spend",
            "impressions",
            "clicks",
            "leads",
            "conversations",
            "cpl",
            "ctr",
            "cpc",
            "cpm",
        )
    }


def percent_change(current: object, previous: object) -> Decimal | None:
    if previous is None or Decimal(str(previous)) == 0:
        return None
    value = (Decimal(str(current or 0)) - Decimal(str(previous))) / Decimal(str(previous)) * 100
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def safe_divide(numerator: Decimal, denominator: Decimal) -> Decimal | None:
    if denominator == 0:
        return None
    return (numerator / denominator).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)


def row_ids(rows: object) -> list[str]:
    return [str(row["id"]) for row in rows or []]
