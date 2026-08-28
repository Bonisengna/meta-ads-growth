from calendar import monthrange
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
    "id,meta_account_id,meta_campaign_id,name,objective,buying_type,daily_budget,"
    "lifetime_budget,budget_remaining,start_time,stop_time,status,meta_created_at,"
    "meta_updated_at,created_at,updated_at"
)
ADSET_COLUMNS = (
    "id,campaign_id,meta_adset_id,name,status,optimization_goal,billing_event,"
    "daily_budget,lifetime_budget,budget_remaining,start_time,end_time,meta_created_at,"
    "meta_updated_at,created_at,updated_at"
)
AD_COLUMNS = (
    "id,adset_id,meta_ad_id,name,status,creative_id,creative_name,creative_type,"
    "thumbnail_url,image_url,video_id,video_duration_seconds,primary_text,headline,"
    "call_to_action_type,destination_url,meta_created_at,meta_updated_at,created_at,updated_at"
)
METRIC_COLUMNS = (
    "id,{entity_column},metric_date,spend,impressions,reach,clicks,link_clicks,ctr,cpc,"
    "cpm,frequency,leads,cpl,conversations,cost_per_conversation,landing_page_views,"
    "video_views_3s,video_plays,video_p25,video_p50,video_p75,video_p95,thruplays,"
    "created_at,updated_at"
)

AGGREGATE_METRIC_COLUMNS = (
    "spend,impressions,reach,clicks,link_clicks,frequency,leads,conversations,landing_page_views,"
    "video_views_3s,video_plays,video_p25,video_p50,video_p75,video_p95,thruplays"
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
        campaign_operations = self._operations(current[0], current[1], scope)
        investment_pacing = self._investment_pacing(scope)
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
            "investment_pacing": investment_pacing,
            "campaign_operations": campaign_operations,
            "daily_series": analytics["daily_series"],
            "campaign_ranking": analytics["campaign_ranking"],
            "adset_ranking": analytics["adset_ranking"],
            "ad_ranking": analytics["ad_ranking"],
            "insights": build_insights(current_metrics, previous_metrics),
            "recommendations": recommendations,
            "breakdowns": breakdowns,
        }

    def _investment_pacing(self, scope: dict[str, object]) -> dict[str, object]:
        today = date.today()
        month_start = today.replace(day=1)
        month_metrics = self._aggregate(month_start, today, scope["campaign_ids"])
        budgets = [
            Decimal(str(row["monthly_media_budget"]))
            for row in scope["client_rows"]
            if row.get("monthly_media_budget") not in (None, "")
        ]
        monthly_budget = sum(budgets, Decimal("0")) if budgets else None
        currencies = {
            str(row["currency"])
            for row in scope["account_rows"]
            if row.get("currency")
        }
        currency = next(iter(currencies)) if len(currencies) == 1 else None
        return build_investment_pacing(
            monthly_budget=monthly_budget,
            spent=Decimal(str(month_metrics["spend"])),
            currency=currency,
            today=today,
        )

    def _operations(
        self, date_from: date, date_to: date, scope: dict[str, object]
    ) -> list[dict[str, object]]:
        duration = (date_to - date_from).days + 1
        campaign_metrics = self._metrics_by_entity(
            "campaign_metrics", "campaign_id", scope["campaign_ids"], date_from, date_to
        )
        adset_metrics = self._metrics_by_entity(
            "adset_metrics", "adset_id", scope["adset_ids"], date_from, date_to
        )
        ad_ids = row_ids(scope["ad_rows"])
        ad_metrics = self._metrics_by_entity(
            "ad_metrics", "ad_id", ad_ids, date_from, date_to
        )

        ads_by_adset: dict[str, list[dict[str, object]]] = {}
        for ad in scope["ad_rows"]:
            ad_id = str(ad["id"])
            ads_by_adset.setdefault(str(ad["adset_id"]), []).append({
                "id": ad_id,
                "adset_id": ad["adset_id"],
                "name": ad.get("name") or "Anúncio sem nome",
                "status": ad.get("status") or "ARCHIVED",
                **{key: ad.get(key) for key in (
                    "creative_type", "thumbnail_url", "image_url",
                    "video_duration_seconds", "primary_text", "headline",
                    "call_to_action_type", "destination_url",
                )},
                "metrics": ad_metrics.get(ad_id, aggregate_metrics([])),
            })

        adsets_by_campaign: dict[str, list[dict[str, object]]] = {}
        for adset in scope["adset_rows"]:
            adset_id = str(adset["id"])
            metrics = adset_metrics.get(adset_id, aggregate_metrics([]))
            budget, budget_type = configured_budget(adset, duration)
            adsets_by_campaign.setdefault(str(adset["campaign_id"]), []).append({
                "id": adset_id,
                "campaign_id": adset["campaign_id"],
                "name": adset.get("name") or "Conjunto sem nome",
                "status": adset.get("status") or "ARCHIVED",
                "optimization_goal": adset.get("optimization_goal"),
                "daily_budget": adset.get("daily_budget"),
                "lifetime_budget": adset.get("lifetime_budget"),
                "configured_budget": budget,
                "budget_type": budget_type,
                "budget_utilization": budget_percent(metrics["spend"], budget),
                "metrics": metrics,
                "ads": sorted(
                    ads_by_adset.get(adset_id, []),
                    key=lambda row: Decimal(str(row["metrics"]["spend"])),
                    reverse=True,
                ),
            })

        operations: list[dict[str, object]] = []
        for campaign in scope["campaign_rows"]:
            campaign_id = str(campaign["id"])
            metrics = campaign_metrics.get(campaign_id, aggregate_metrics([]))
            budget, budget_type = configured_budget(campaign, duration)
            operations.append({
                "id": campaign_id,
                "meta_account_id": campaign["meta_account_id"],
                "name": campaign.get("name") or "Campanha sem nome",
                "objective": campaign.get("objective"),
                "status": campaign.get("status") or "ARCHIVED",
                "daily_budget": campaign.get("daily_budget"),
                "lifetime_budget": campaign.get("lifetime_budget"),
                "configured_budget": budget,
                "budget_type": budget_type,
                "budget_utilization": budget_percent(metrics["spend"], budget),
                "has_delivery": Decimal(str(metrics["spend"])) > 0,
                "metrics": metrics,
                "adsets": sorted(
                    adsets_by_campaign.get(campaign_id, []),
                    key=lambda row: Decimal(str(row["metrics"]["spend"])),
                    reverse=True,
                ),
            })
        operations.sort(
            key=lambda row: Decimal(str(row["metrics"]["spend"])), reverse=True
        )
        return operations

    def _metrics_by_entity(
        self,
        table: str,
        id_column: str,
        entity_ids: list[str],
        date_from: date,
        date_to: date,
    ) -> dict[str, dict[str, object]]:
        if not entity_ids:
            return {}
        rows: list[dict[str, object]] = []
        offset = 0
        while True:
            response = (
                self.client.table(table)
                .select(f"{id_column},{AGGREGATE_METRIC_COLUMNS}")
                .gte("metric_date", date_from.isoformat())
                .lte("metric_date", date_to.isoformat())
                .in_(id_column, entity_ids)
                .range(offset, offset + 999)
                .execute()
            )
            batch = response.data or []
            rows.extend(batch)
            if len(batch) < 1000:
                break
            offset += 1000
        grouped: dict[str, list[dict[str, object]]] = {}
        for row in rows:
            grouped.setdefault(str(row[id_column]), []).append(row)
        return {entity_id: aggregate_metrics(items) for entity_id, items in grouped.items()}

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
        client_query = self.client.table("clients").select("id,monthly_media_budget")
        if client_id:
            client_query = client_query.eq("id", str(client_id))
        client_rows = client_query.execute().data or []
        client_ids = row_ids(client_rows)

        account_query = self.client.table("meta_accounts").select(
            "id,client_id,currency,timezone,last_synced_at"
        )
        if client_id:
            account_query = account_query.eq("client_id", str(client_id))
        if meta_account_id:
            account_query = account_query.eq("id", str(meta_account_id))
        account_rows = account_query.execute().data or []
        account_ids = row_ids(account_rows)

        campaign_query = self.client.table("campaigns").select(
            "id,meta_account_id,name,objective,status,daily_budget,lifetime_budget,"
            "budget_remaining,start_time,stop_time"
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
            client_rows = [
                row for row in client_rows if str(row.get("id")) in scoped_client_ids
            ]

        adset_query = self.client.table("adsets").select(
            "id,campaign_id,name,status,optimization_goal,daily_budget,lifetime_budget,"
            "budget_remaining,start_time,end_time"
        )
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
                .select(
                    "id,adset_id,name,status,creative_type,thumbnail_url,image_url,"
                    "video_duration_seconds,primary_text,headline,call_to_action_type,"
                    "destination_url",
                    count="exact",
                )
                .in_("adset_id", adset_ids)
                .execute()
            )
            ads = response.count or 0
            ad_rows = response.data or []

        return {
            "clients": len(client_ids),
            "client_rows": client_rows,
            "account_ids": account_ids,
            "account_rows": account_rows,
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
                .select(AGGREGATE_METRIC_COLUMNS)
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
                        f"campaign_id,metric_date,{AGGREGATE_METRIC_COLUMNS}"
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
        rows: list[dict[str, object]] = []
        offset = 0
        while True:
            response = (
                self.client.table(table)
                .select(f"{id_column},{AGGREGATE_METRIC_COLUMNS}")
                .gte("metric_date", date_from.isoformat())
                .lte("metric_date", date_to.isoformat())
                .in_(id_column, entity_ids)
                .range(offset, offset + 999)
                .execute()
            )
            batch = response.data or []
            rows.extend(batch)
            if len(batch) < 1000:
                break
            offset += 1000
        grouped: dict[str, list[dict[str, object]]] = {}
        for row in rows:
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
        return ranking


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
    landing_page_views = sum(int(row.get("landing_page_views") or 0) for row in rows)
    video_views_3s = sum(int(row.get("video_views_3s") or 0) for row in rows)
    video_plays = sum(int(row.get("video_plays") or 0) for row in rows)
    video_p25 = sum(int(row.get("video_p25") or 0) for row in rows)
    video_p50 = sum(int(row.get("video_p50") or 0) for row in rows)
    video_p75 = sum(int(row.get("video_p75") or 0) for row in rows)
    video_p95 = sum(int(row.get("video_p95") or 0) for row in rows)
    thruplays = sum(int(row.get("thruplays") or 0) for row in rows)
    frequency_weight = sum(
        Decimal(str(row.get("frequency") or 0)) * Decimal(int(row.get("impressions") or 0))
        for row in rows
        if row.get("frequency") not in (None, "")
    )
    frequency_impressions = sum(
        int(row.get("impressions") or 0)
        for row in rows
        if row.get("frequency") not in (None, "")
    )
    return {
        "spend": spend,
        "impressions": impressions,
        "reach": reach,
        "clicks": clicks,
        "link_clicks": link_clicks,
        "leads": leads,
        "conversations": conversations,
        "landing_page_views": landing_page_views,
        "video_views_3s": video_views_3s,
        "video_plays": video_plays,
        "video_p25": video_p25,
        "video_p50": video_p50,
        "video_p75": video_p75,
        "video_p95": video_p95,
        "thruplays": thruplays,
        "cpl": safe_divide(spend, Decimal(leads)),
        "ctr": safe_divide(Decimal(clicks) * 100, Decimal(impressions)),
        "cpc": safe_divide(spend, Decimal(clicks)),
        "cpm": safe_divide(spend * 1000, Decimal(impressions)),
        "link_ctr": safe_divide(Decimal(link_clicks) * 100, Decimal(impressions)),
        "frequency": safe_divide(frequency_weight, Decimal(frequency_impressions)),
        "landing_page_view_rate": safe_divide(
            Decimal(landing_page_views) * 100, Decimal(link_clicks)
        ),
        "cost_per_landing_page_view": safe_divide(spend, Decimal(landing_page_views)),
        "landing_page_conversion_rate": safe_divide(
            Decimal(leads) * 100, Decimal(landing_page_views)
        ),
        "hook_rate": (
            safe_divide(Decimal(video_views_3s) * 100, Decimal(impressions))
            if video_views_3s or video_plays else None
        ),
        "thruplay_rate": safe_divide(Decimal(thruplays) * 100, Decimal(video_plays)),
        "video_p25_rate": safe_divide(Decimal(video_p25) * 100, Decimal(video_plays)),
        "video_p50_rate": safe_divide(Decimal(video_p50) * 100, Decimal(video_plays)),
        "video_p75_rate": safe_divide(Decimal(video_p75) * 100, Decimal(video_plays)),
        "video_p95_rate": safe_divide(Decimal(video_p95) * 100, Decimal(video_plays)),
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
            "landing_page_views",
            "video_views_3s",
            "thruplays",
            "landing_page_view_rate",
            "cost_per_landing_page_view",
            "landing_page_conversion_rate",
            "hook_rate",
            "thruplay_rate",
        )
    }


def configured_budget(
    entity: dict[str, object], duration_days: int
) -> tuple[Decimal | None, str | None]:
    daily = entity.get("daily_budget")
    lifetime = entity.get("lifetime_budget")
    if daily not in (None, ""):
        return Decimal(str(daily)) * Decimal(duration_days), "DAILY_PERIOD"
    if lifetime not in (None, ""):
        return Decimal(str(lifetime)), "LIFETIME"
    return None, None


def budget_percent(spend: object, budget: Decimal | None) -> Decimal | None:
    if budget is None:
        return None
    return safe_divide(Decimal(str(spend or 0)) * 100, budget)


def build_investment_pacing(
    *, monthly_budget: Decimal | None, spent: Decimal, currency: str | None,
    today: date | None = None,
) -> dict[str, object]:
    current_day = today or date.today()
    days_in_month = monthrange(current_day.year, current_day.month)[1]
    days_elapsed = current_day.day
    elapsed_percent = (
        Decimal(days_elapsed) * 100 / Decimal(days_in_month)
    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if monthly_budget is None or monthly_budget <= 0:
        return {
            "currency": currency,
            "monthly_budget": monthly_budget,
            "spent": spent,
            "remaining": None,
            "percent_consumed": None,
            "projected_spend": None,
            "projected_percent": None,
            "expected_spend_to_date": None,
            "variance_to_expected": None,
            "elapsed_percent": elapsed_percent,
            "days_elapsed": days_elapsed,
            "days_in_month": days_in_month,
            "pace_status": "NOT_CONFIGURED",
        }
    percent_consumed = spent * 100 / monthly_budget
    projected_spend = spent / Decimal(days_elapsed) * Decimal(days_in_month)
    projected_percent = projected_spend * 100 / monthly_budget
    expected_spend = monthly_budget * Decimal(days_elapsed) / Decimal(days_in_month)
    variance = spent - expected_spend
    pace_delta = percent_consumed - elapsed_percent
    pace_status = "BELOW" if pace_delta < Decimal("-5") else (
        "ABOVE" if pace_delta > Decimal("5") else "ON_TRACK"
    )
    return {
        "currency": currency,
        "monthly_budget": monthly_budget,
        "spent": spent,
        "remaining": monthly_budget - spent,
        "percent_consumed": percent_consumed,
        "projected_spend": projected_spend,
        "projected_percent": projected_percent,
        "expected_spend_to_date": expected_spend,
        "variance_to_expected": variance,
        "elapsed_percent": elapsed_percent,
        "days_elapsed": days_elapsed,
        "days_in_month": days_in_month,
        "pace_status": pace_status,
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
