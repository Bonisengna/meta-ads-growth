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
        analytics = self._analytics(
            current[0], current[1], scope
        )
        breakdowns = self._breakdown_analytics(
            current[0], current[1], scope["campaign_ids"]
        )

        recommendations = build_recommendations(
            analytics["adset_ranking"], analytics["ad_ranking"]
        )
        decided = self._decision_statuses([str(item["key"]) for item in recommendations])
        for item in recommendations:
            item["status"] = decided.get(str(item["key"]), "PENDING")

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
            "daily_series": analytics["daily_series"],
            "campaign_ranking": analytics["campaign_ranking"],
            "adset_ranking": analytics["adset_ranking"],
            "ad_ranking": analytics["ad_ranking"],
            "insights": build_insights(current_metrics, previous_metrics),
            "recommendations": recommendations,
            "breakdowns": breakdowns,
        }

    def _breakdown_analytics(
        self, date_from: date, date_to: date, campaign_ids: list[str]
    ) -> dict[str, list[dict[str, object]]]:
        result = {key: [] for key in (
            "age", "gender", "platform", "placement", "device", "region", "hour"
        )}
        if not campaign_ids:
            return result
        rows: list[dict[str, object]] = []
        offset = 0
        while True:
            response = (
                self.client.table("breakdown_metrics")
                .select(
                    "metric_date,dimension_type,dimension_value,spend,impressions,"
                    "reach,link_clicks,leads,conversations"
                )
                .gte("metric_date", date_from.isoformat())
                .lte("metric_date", date_to.isoformat())
                .in_("campaign_id", campaign_ids)
                .range(offset, offset + 999)
                .execute()
            )
            batch = response.data or []
            rows.extend(batch)
            if len(batch) < 1000:
                break
            offset += 1000

        grouped: dict[tuple[str, str], list[dict[str, object]]] = {}
        for row in rows:
            dimension_type = str(row["dimension_type"]).lower()
            value = str(row["dimension_value"])
            if dimension_type == "hour":
                metric_day = date.fromisoformat(str(row["metric_date"])).weekday()
                value = f"{metric_day}|{value[:2]}"
            grouped.setdefault((dimension_type, value), []).append(row)

        for (dimension_type, value), metric_rows in grouped.items():
            if dimension_type not in result:
                continue
            metrics = aggregate_metrics(metric_rows)
            conversions = int(metrics["leads"]) + int(metrics["conversations"])
            point = {
                "value": value,
                **{key: metrics[key] for key in (
                    "spend", "impressions", "reach", "link_clicks", "leads", "conversations"
                )},
                "cpa": safe_divide(Decimal(str(metrics["spend"])), Decimal(conversions)),
                "conversion_rate": safe_divide(
                    Decimal(conversions) * 100, Decimal(str(metrics["link_clicks"]))
                ),
                "ctr": metrics["link_ctr"],
                "cpm": metrics["cpm"],
            }
            result[dimension_type].append(point)
        for points in result.values():
            points.sort(key=lambda item: Decimal(str(item["spend"])), reverse=True)
        return result

    def _decision_statuses(self, keys: list[str]) -> dict[str, str]:
        if not keys:
            return {}
        response = (
            self.client.table("recommendations")
            .select("recommendation_key,status,decided_at")
            .in_("recommendation_key", keys)
            .order("decided_at", desc=True)
            .execute()
        )
        statuses: dict[str, str] = {}
        for row in response.data or []:
            key = str(row.get("recommendation_key") or "")
            if key and key not in statuses:
                statuses[key] = str(row["status"])
        return statuses

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

        campaign_query = self.client.table("campaigns").select(
            "id,meta_account_id,name,status"
        )
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

        adset_query = self.client.table("adsets").select("id,campaign_id,name,status")
        if campaign_ids:
            adset_rows = adset_query.in_("campaign_id", campaign_ids).execute().data or []
            adset_ids = row_ids(adset_rows)
        else:
            adset_rows = []
            adset_ids = []
        ads = 0
        ad_rows: list[dict[str, object]] = []
        if adset_ids:
            response = (
                self.client.table("ads")
                .select("id,adset_id,name,status", count="exact")
                .in_("adset_id", adset_ids)
                .execute()
            )
            ads = response.count or 0
            ad_rows = response.data or []

        return {
            "clients": len(client_ids),
            "account_ids": account_ids,
            "campaign_ids": campaign_ids,
            "campaign_rows": campaign_rows,
            "adset_ids": adset_ids,
            "adset_rows": adset_rows,
            "ad_rows": ad_rows,
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
                .select("spend,impressions,reach,clicks,link_clicks,leads,conversations")
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

    def _analytics(
        self,
        date_from: date,
        date_to: date,
        scope: dict[str, object],
    ) -> dict[str, object]:
        campaign_ids = scope["campaign_ids"]
        campaign_rows = scope["campaign_rows"]
        rows: list[dict[str, object]] = []
        if campaign_ids:
            offset = 0
            while True:
                response = (
                    self.client.table("campaign_metrics")
                    .select(
                        "campaign_id,metric_date,spend,impressions,reach,clicks,link_clicks,leads,conversations"
                    )
                    .gte("metric_date", date_from.isoformat())
                    .lte("metric_date", date_to.isoformat())
                    .in_("campaign_id", campaign_ids)
                    .range(offset, offset + 999)
                    .execute()
                )
                batch = response.data or []
                rows.extend(batch)
                if len(batch) < 1000:
                    break
                offset += 1000

        by_date: dict[str, list[dict[str, object]]] = {}
        by_campaign: dict[str, list[dict[str, object]]] = {}
        for row in rows:
            by_date.setdefault(str(row["metric_date"]), []).append(row)
            by_campaign.setdefault(str(row["campaign_id"]), []).append(row)

        daily_series = []
        current_date = date_from
        while current_date <= date_to:
            metrics = aggregate_metrics(by_date.get(current_date.isoformat(), []))
            daily_series.append(
                {
                    "metric_date": current_date,
                    **{key: metrics[key] for key in ("spend", "impressions", "clicks", "leads", "conversations")},
                }
            )
            current_date += timedelta(days=1)

        campaigns = {str(row["id"]): row for row in campaign_rows}
        ranking = []
        for campaign_id, metric_rows in by_campaign.items():
            metrics = aggregate_metrics(metric_rows)
            campaign = campaigns.get(campaign_id, {})
            ranking.append(
                {
                    "campaign_id": campaign_id,
                    "name": campaign.get("name") or "Campanha sem nome",
                    "status": campaign.get("status") or "ARCHIVED",
                    **metrics,
                    "cost_per_conversation": safe_divide(
                        Decimal(str(metrics["spend"])),
                        Decimal(str(metrics["conversations"])),
                    ),
                }
            )
        ranking.sort(key=lambda row: Decimal(str(row["spend"])), reverse=True)
        adset_ranking = self._entity_ranking(
            "adset_metrics", "adset_id", "ADSET", date_from, date_to,
            scope["adset_ids"], scope["adset_rows"]
        )
        ad_ids = row_ids(scope["ad_rows"])
        ad_ranking = self._entity_ranking(
            "ad_metrics", "ad_id", "AD", date_from, date_to, ad_ids, scope["ad_rows"]
        )
        return {
            "daily_series": daily_series,
            "campaign_ranking": ranking,
            "adset_ranking": adset_ranking,
            "ad_ranking": ad_ranking,
        }

    def _entity_ranking(
        self, table: str, id_column: str, entity_type: str, date_from: date,
        date_to: date, entity_ids: list[str], entity_rows: list[dict[str, object]],
    ) -> list[dict[str, object]]:
        if not entity_ids:
            return []
        response = (
            self.client.table(table)
            .select(f"{id_column},spend,impressions,clicks,leads,conversations")
            .gte("metric_date", date_from.isoformat())
            .lte("metric_date", date_to.isoformat())
            .in_(id_column, entity_ids)
            .execute()
        )
        grouped: dict[str, list[dict[str, object]]] = {}
        for row in response.data or []:
            grouped.setdefault(str(row[id_column]), []).append(row)
        entities = {str(row["id"]): row for row in entity_rows}
        ranking = []
        for entity_id, rows in grouped.items():
            metrics = aggregate_metrics(rows)
            entity = entities.get(entity_id, {})
            ranking.append({
                "entity_type": entity_type,
                "entity_id": entity_id,
                "name": entity.get("name") or "Entidade sem nome",
                "status": entity.get("status") or "ARCHIVED",
                **metrics,
                "cost_per_conversation": safe_divide(
                    Decimal(str(metrics["spend"])), Decimal(str(metrics["conversations"]))
                ),
            })
        ranking.sort(key=lambda row: (
            int(row["conversations"]), Decimal(str(row["spend"]))
        ), reverse=True)
        return ranking[:10]


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
    reach = sum(int(row.get("reach") or 0) for row in rows)
    clicks = sum(int(row.get("clicks") or 0) for row in rows)
    link_clicks = sum(int(row.get("link_clicks") or 0) for row in rows)
    leads = sum(int(row.get("leads") or 0) for row in rows)
    conversations = sum(int(row.get("conversations") or 0) for row in rows)
    return {
        "spend": spend,
        "impressions": impressions,
        "reach": reach,
        "clicks": clicks,
        "link_clicks": link_clicks,
        "leads": leads,
        "conversations": conversations,
        "cpl": safe_divide(spend, Decimal(leads)),
        "ctr": safe_divide(Decimal(clicks) * 100, Decimal(impressions)),
        "cpc": safe_divide(spend, Decimal(clicks)),
        "cpm": safe_divide(spend * 1000, Decimal(impressions)),
        "link_ctr": safe_divide(Decimal(link_clicks) * 100, Decimal(impressions)),
        "frequency": safe_divide(Decimal(impressions), Decimal(reach)),
    }


def compare_metrics(
    current: dict[str, object], previous: dict[str, object]
) -> dict[str, Decimal | None]:
    return {
        key: percent_change(current.get(key), previous.get(key))
        for key in (
            "spend",
            "impressions",
            "reach",
            "clicks",
            "link_clicks",
            "leads",
            "conversations",
            "cpl",
            "ctr",
            "cpc",
            "cpm",
            "link_ctr",
            "frequency",
        )
    }


def build_insights(
    current: dict[str, object], previous: dict[str, object]
) -> list[dict[str, str]]:
    spend = Decimal(str(current.get("spend") or 0))
    impressions = int(current.get("impressions") or 0)
    conversions = int(current.get("leads") or 0) + int(current.get("conversations") or 0)
    ctr = current.get("ctr")
    insights: list[dict[str, str]] = []

    if spend == 0:
        insights.append(
            {
                "code": "NO_DELIVERY",
                "severity": "INFO",
                "title": "Sem investimento no período",
                "message": "Não há gasto registrado para produzir um diagnóstico de desempenho.",
            }
        )
        return insights
    if spend >= Decimal("20") and conversions == 0:
        insights.append(
            {
                "code": "SPEND_WITHOUT_CONVERSION",
                "severity": "WARNING",
                "title": "Investimento sem conversões",
                "message": "Há pelo menos R$ 20 de investimento e nenhum lead ou conversa registrado.",
            }
        )
    if impressions >= 1000 and ctr is not None and Decimal(str(ctr)) < Decimal("1"):
        insights.append(
            {
                "code": "LOW_CTR",
                "severity": "WARNING",
                "title": "CTR abaixo de 1%",
                "message": "Com pelo menos mil impressões, a taxa de cliques indica atenção para criativo e mensagem.",
            }
        )

    current_conversations = int(current.get("conversations") or 0)
    previous_conversations = int(previous.get("conversations") or 0)
    if current_conversations >= 5 and previous_conversations >= 5:
        current_cost = safe_divide(spend, Decimal(current_conversations))
        previous_cost = safe_divide(
            Decimal(str(previous.get("spend") or 0)), Decimal(previous_conversations)
        )
        if current_cost is not None and previous_cost is not None and current_cost <= previous_cost * Decimal("0.85"):
            insights.append(
                {
                    "code": "CONVERSATION_COST_IMPROVED",
                    "severity": "OPPORTUNITY",
                    "title": "Custo por conversa melhorou",
                    "message": "O custo por conversa caiu pelo menos 15% com volume mínimo comparável.",
                }
            )
    if not insights:
        insights.append(
            {
                "code": "NO_STRONG_SIGNAL",
                "severity": "INFO",
                "title": "Sem sinal forte no período",
                "message": "Os limites mínimos das regras não foram atingidos; continue acompanhando a coleta.",
            }
        )
    return insights


def build_recommendations(
    adsets: list[dict[str, object]], ads: list[dict[str, object]]
) -> list[dict[str, object]]:
    recommendations: list[dict[str, object]] = []
    for row in [*adsets, *ads]:
        spend = Decimal(str(row.get("spend") or 0))
        impressions = int(row.get("impressions") or 0)
        conversations = int(row.get("conversations") or 0)
        ctr = row.get("ctr")
        rules: list[tuple[str, str, str, str, str]] = []
        if spend >= Decimal("20") and conversations == 0:
            rules.append((
                "SPEND_WITHOUT_CONVERSATION", "HIGH", "Revisar entrega sem conversas",
                f"Houve {spend:.2f} de investimento sem conversas atribuídas.",
                "Reduzir desperdício após revisão humana de criativo, público e rastreamento.",
            ))
        if impressions >= 1000 and ctr is not None and Decimal(str(ctr)) < Decimal("1"):
            rules.append((
                "LOW_CTR", "MEDIUM", "Testar nova abordagem criativa",
                f"O CTR foi {Decimal(str(ctr)):.2f}% em {impressions} impressões.",
                "Aumentar a taxa de cliques com uma nova hipótese de mensagem ou criativo.",
            ))
        for rule_code, priority, title, evidence, impact in rules:
            entity_type = str(row["entity_type"])
            entity_id = str(row["entity_id"])
            recommendations.append({
                "key": f"{entity_type.lower()}:{entity_id}:{rule_code.lower()}",
                "entity_type": entity_type,
                "entity_id": entity_id,
                "entity_name": row["name"],
                "rule_code": rule_code,
                "priority": priority,
                "title": title,
                "explanation": "A regra compara volume, investimento e resultado do período selecionado.",
                "evidence": evidence,
                "expected_impact": impact,
                "status": "PENDING",
            })
    priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    recommendations.sort(key=lambda row: priority_order[str(row["priority"])])
    return recommendations[:12]


class RecommendationService:
    def __init__(self, client: Client) -> None:
        self.client = client

    def decide(self, payload: dict[str, object]) -> dict[str, object]:
        if payload["period_from"] > payload["period_to"]:
            raise ValueError("period_from não pode ser posterior a period_to")
        entity_type = str(payload["entity_type"])
        if payload["rule_code"] not in {"SPEND_WITHOUT_CONVERSATION", "LOW_CTR"}:
            raise ValueError("Regra de recomendação desconhecida")
        expected_key = (
            f"{entity_type.lower()}:{payload['entity_id']}:{str(payload['rule_code']).lower()}"
        )
        if payload["key"] != expected_key:
            raise ValueError("Chave da recomendação não corresponde à entidade e à regra")
        entity_column = "adset_id" if entity_type == "ADSET" else "ad_id"
        analysis = {
            entity_column: str(payload["entity_id"]),
            "period_start": str(payload["period_from"]),
            "period_end": str(payload["period_to"]),
            "analysis_type": "RULE_BASED",
            "problem": payload["title"],
            "possible_causes": payload["evidence"],
            "summary": payload["explanation"],
            "priority": payload["priority"],
            "rating": 1,
            "model": "deterministic-rules-v1",
            "prompt_version": "rules-v1",
        }
        analysis_response = self.client.table("ai_analyses").insert(analysis).execute()
        analysis_id = analysis_response.data[0]["id"]
        recommendation = {
            "analysis_id": analysis_id,
            "recommendation_key": payload["key"],
            "rule_code": payload["rule_code"],
            "title": payload["title"],
            "description": payload["explanation"],
            "action_type": "REVIEW",
            "priority": payload["priority"],
            "expected_impact": payload["expected_impact"],
            "status": payload["status"],
            "decision_note": payload.get("note"),
        }
        response = self.client.table("recommendations").insert(recommendation).execute()
        row = response.data[0]
        if payload["status"] == "ACCEPTED":
            self.client.table("improvements").insert({
                "recommendation_id": row["id"],
                entity_column: str(payload["entity_id"]),
                "title": payload["title"],
                "hypothesis": payload["expected_impact"],
                "description": "Acompanhamento aprovado; nenhuma alteração foi enviada à Meta.",
                "status": "PLANNED",
            }).execute()
        return {
            "id": row["id"], "key": payload["key"], "status": payload["status"],
            "decided_at": row["decided_at"],
        }

    def list_improvements(self, page: int, page_size: int) -> dict[str, object]:
        response = (
            self.client.table("improvements")
            .select(
                "id,recommendation_id,campaign_id,adset_id,ad_id,title,hypothesis,status,"
                "metric_name,before_value,after_value,result,conclusion,created_at",
                count="exact",
            )
            .order("created_at", desc=True)
            .range(*page_range(page, page_size))
            .execute()
        )
        return page_result(response.data, response.count, page, page_size)


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
