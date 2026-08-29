from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from supabase import Client

from app.services.meta_graph_client import MetaGraphClient, MetaGraphError


class MetaEntityNotAccessibleError(LookupError):
    pass


BREAKDOWN_SPECS = {
    "AGE": "age",
    "GENDER": "gender",
    "PLATFORM": "publisher_platform",
    "PLACEMENT": "platform_position",
    "DEVICE": "impression_device",
    "REGION": "region",
    "HOUR": "hourly_stats_aggregated_by_advertiser_time_zone",
}


class MetaSyncService:
    """Orquestra Meta → Supabase preservando identidades e histórico."""

    def __init__(self, supabase: Client, meta: MetaGraphClient) -> None:
        self.supabase = supabase
        self.meta = meta
        self._video_duration_cache: dict[str, str | None] = {}

    def sync_account(self, client_id: UUID, account_id: str) -> dict[str, int]:
        normalized_id = account_id.removeprefix("act_")
        remote_account = next(
            (
                account
                for account in self.meta.list_ad_accounts()
                if str(account.get("account_id")) == normalized_id
                or str(account.get("id")) == f"act_{normalized_id}"
            ),
            None,
        )
        if remote_account is None:
            raise MetaEntityNotAccessibleError(
                f"Conta de anúncios {normalized_id} não acessível para este token."
            )

        account, account_created = self._upsert_one(
            "meta_accounts",
            {
                "client_id": str(client_id),
                "meta_account_id": normalized_id,
                "name": remote_account.get("name") or normalized_id,
                "currency": remote_account.get("currency"),
                "timezone": remote_account.get("timezone_name"),
                "status": account_status(remote_account.get("account_status")),
                "updated_at": now_iso(),
            },
            "meta_account_id",
        )

        campaigns = self.meta.list_campaigns(normalized_id)
        campaign_ids, campaign_changes = self._sync_campaigns(account["id"], campaigns)
        adsets = self.meta.list_adsets(normalized_id)
        adset_ids, adset_changes = self._sync_adsets(campaign_ids, adsets)
        ads = self.meta.list_ads(normalized_id)
        ad_changes = self._sync_ads(adset_ids, ads)
        synced_at = now_iso()
        (
            self.supabase.table("meta_accounts")
            .update({
                "last_synced_at": synced_at,
                "last_entities_synced_at": synced_at,
                "updated_at": synced_at,
            })
            .eq("id", account["id"])
            .execute()
        )

        return {
            "meta_accounts": 1,
            "campaigns": len(campaigns),
            "adsets": len(adsets),
            "ads": len(ads),
            "changes": {
                "meta_accounts": change_stats(account_created),
                "campaigns": campaign_changes,
                "adsets": adset_changes,
                "ads": ad_changes,
            },
        }

    def sync_daily_metrics(
        self, account_id: str, since: date, until: date | None = None
    ) -> dict[str, int]:
        until = until or since
        counts: dict[str, int] = {}
        for level, table, external_column, internal_column in (
            ("campaign", "campaign_metrics", "campaign_id", "campaign_id"),
            ("adset", "adset_metrics", "adset_id", "adset_id"),
            ("ad", "ad_metrics", "ad_id", "ad_id"),
        ):
            rows = self.meta.list_daily_insights(
                account_id, level, since.isoformat(), until.isoformat()
            )
            id_map = self._internal_id_map(entity_table(level), meta_id_column(level))
            payloads = [
                metrics_payload(row, internal_column, id_map.get(str(row.get(external_column))))
                for row in rows
            ]
            payloads = [payload for payload in payloads if payload is not None]
            if payloads:
                (
                    self.supabase.table(table)
                    .upsert(payloads, on_conflict=f"{internal_column},metric_date")
                    .execute()
                )
            counts[level] = len(payloads)
        return counts

    def mark_metrics_synced(self, account_id: str, *, complete: bool) -> None:
        """Registra separadamente o núcleo de métricas e a coleta integral."""
        synced_at = now_iso()
        values = {"last_metrics_synced_at": synced_at, "updated_at": synced_at}
        if complete:
            values["last_successful_sync_at"] = synced_at
        (
            self.supabase.table("meta_accounts")
            .update(values)
            .eq("meta_account_id", account_id.removeprefix("act_"))
            .execute()
        )

    def sync_breakdown_metrics(
        self, account_id: str, since: date, until: date | None = None
    ) -> dict[str, int]:
        until = until or since
        campaign_ids = self._internal_id_map("campaigns", "meta_campaign_id")
        counts: dict[str, int] = {}
        for dimension_type, meta_breakdown in BREAKDOWN_SPECS.items():
            try:
                rows = self.meta.list_breakdown_insights(
                    account_id, meta_breakdown, since.isoformat(), until.isoformat()
                )
            except MetaGraphError as exc:
                raise MetaGraphError(
                    f"Falha no detalhamento {dimension_type}/{meta_breakdown}: {exc}",
                    code=exc.code,
                    status_code=exc.status_code,
                ) from exc
            payloads = [
                breakdown_payload(
                    row,
                    dimension_type,
                    meta_breakdown,
                    campaign_ids.get(str(row.get("campaign_id"))),
                )
                for row in rows
            ]
            payloads = [payload for payload in payloads if payload is not None]
            for start in range(0, len(payloads), 500):
                self.supabase.table("breakdown_metrics").upsert(
                    payloads[start:start + 500],
                    on_conflict="campaign_id,metric_date,dimension_type,dimension_value",
                ).execute()
            counts[dimension_type.lower()] = len(payloads)
        return counts

    def _sync_campaigns(
        self, meta_account_id: str, remote_rows: list[dict[str, Any]]
    ) -> tuple[dict[str, str], dict[str, int]]:
        result: dict[str, str] = {}
        changes = change_stats()
        for row in remote_rows:
            saved, created = self._upsert_one(
                "campaigns",
                {
                    "meta_account_id": meta_account_id,
                    "meta_campaign_id": row["id"],
                    "name": row.get("name") or row["id"],
                    "objective": row.get("objective"),
                    "buying_type": row.get("buying_type"),
                    "daily_budget": cents_to_decimal(row.get("daily_budget")),
                    "lifetime_budget": cents_to_decimal(row.get("lifetime_budget")),
                    "budget_remaining": cents_to_decimal(row.get("budget_remaining")),
                    "start_time": row.get("start_time"),
                    "stop_time": row.get("stop_time"),
                    "status": entity_status(row.get("effective_status")),
                    "meta_created_at": row.get("created_time"),
                    "meta_updated_at": row.get("updated_time"),
                    "updated_at": now_iso(),
                },
                "meta_campaign_id",
            )
            changes["imported" if created else "updated"] += 1
            result[row["id"]] = saved["id"]
        changes["archived"] = self._archive_missing(
            "campaigns", "meta_account_id", meta_account_id, "meta_campaign_id", set(result)
        )
        return result, changes

    def _sync_adsets(
        self, campaign_ids: dict[str, str], remote_rows: list[dict[str, Any]]
    ) -> tuple[dict[str, str], dict[str, int]]:
        result: dict[str, str] = {}
        changes = change_stats()
        grouped: dict[str, set[str]] = {value: set() for value in campaign_ids.values()}
        for row in remote_rows:
            campaign_id = campaign_ids.get(str(row.get("campaign_id")))
            if not campaign_id:
                continue
            saved, created = self._upsert_one(
                "adsets",
                {
                    "campaign_id": campaign_id,
                    "meta_adset_id": row["id"],
                    "name": row.get("name") or row["id"],
                    "status": entity_status(row.get("effective_status")),
                    "optimization_goal": row.get("optimization_goal"),
                    "billing_event": row.get("billing_event"),
                    "daily_budget": cents_to_decimal(row.get("daily_budget")),
                    "lifetime_budget": cents_to_decimal(row.get("lifetime_budget")),
                    "budget_remaining": cents_to_decimal(row.get("budget_remaining")),
                    "start_time": row.get("start_time"),
                    "end_time": row.get("end_time"),
                    "meta_created_at": row.get("created_time"),
                    "meta_updated_at": row.get("updated_time"),
                    "updated_at": now_iso(),
                },
                "meta_adset_id",
            )
            changes["imported" if created else "updated"] += 1
            result[row["id"]] = saved["id"]
            grouped[campaign_id].add(row["id"])
        for campaign_id, present in grouped.items():
            changes["archived"] += self._archive_missing(
                "adsets", "campaign_id", campaign_id, "meta_adset_id", present
            )
        return result, changes

    def _sync_ads(
        self, adset_ids: dict[str, str], remote_rows: list[dict[str, Any]]
    ) -> dict[str, int]:
        changes = change_stats()
        grouped: dict[str, set[str]] = {value: set() for value in adset_ids.values()}
        for row in remote_rows:
            adset_id = adset_ids.get(str(row.get("adset_id")))
            if not adset_id:
                continue
            creative = row.get("creative") or {}
            details = creative_details(creative)
            video_id = details.get("video_id")
            video_duration = self._video_duration(str(video_id)) if video_id else None
            _, created = self._upsert_one(
                "ads",
                {
                    "adset_id": adset_id,
                    "meta_ad_id": row["id"],
                    "name": row.get("name") or row["id"],
                    "status": entity_status(row.get("effective_status")),
                    "creative_id": creative.get("id"),
                    **details,
                    "video_duration_seconds": video_duration,
                    "meta_created_at": row.get("created_time"),
                    "meta_updated_at": row.get("updated_time"),
                    "updated_at": now_iso(),
                },
                "meta_ad_id",
            )
            changes["imported" if created else "updated"] += 1
            grouped[adset_id].add(row["id"])
        for adset_id, present in grouped.items():
            changes["archived"] += self._archive_missing(
                "ads", "adset_id", adset_id, "meta_ad_id", present
            )
        return changes

    def _video_duration(self, video_id: str) -> str | None:
        if video_id in self._video_duration_cache:
            return self._video_duration_cache[video_id]
        getter = getattr(self.meta, "get_video_details", None)
        if not callable(getter):
            return None
        try:
            payload = getter(video_id)
            length = payload.get("length")
            value = None if length in (None, "") else str(Decimal(str(length)))
        except (MetaGraphError, ValueError, TypeError):
            value = None
        self._video_duration_cache[video_id] = value
        return value

    def _upsert_one(
        self, table: str, payload: dict[str, Any], conflict_column: str
    ) -> tuple[dict[str, Any], bool]:
        existing = (
            self.supabase.table(table)
            .select("id")
            .eq(conflict_column, str(payload[conflict_column]))
            .limit(1)
            .execute()
        )
        created = not bool(existing.data)
        response = (
            self.supabase.table(table)
            .upsert(payload, on_conflict=conflict_column)
            .select("*")
            .execute()
        )
        rows = response.data or []
        if not rows:
            raise RuntimeError(f"Supabase não retornou o registro de {table} após UPSERT.")
        return rows[0], created

    def _archive_missing(
        self,
        table: str,
        parent_column: str,
        parent_id: str,
        external_column: str,
        present_ids: set[str],
    ) -> int:
        archived = 0
        response = (
            self.supabase.table(table)
            .select(f"id,{external_column},status")
            .eq(parent_column, parent_id)
            .execute()
        )
        for row in response.data or []:
            if row[external_column] not in present_ids and row.get("status") != "ARCHIVED":
                (
                    self.supabase.table(table)
                    .update({"status": "ARCHIVED", "updated_at": now_iso()})
                    .eq("id", row["id"])
                    .execute()
                )
                archived += 1
        return archived

    def _internal_id_map(self, table: str, meta_column: str) -> dict[str, str]:
        response = self.supabase.table(table).select(f"id,{meta_column}").execute()
        return {str(row[meta_column]): row["id"] for row in response.data or []}


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


def change_stats(created: bool | None = None) -> dict[str, int]:
    result = {"imported": 0, "updated": 0, "archived": 0}
    if created is not None:
        result["imported" if created else "updated"] = 1
    return result


def entity_status(effective_status: Any) -> str:
    normalized = str(effective_status or "").upper()
    if normalized == "ACTIVE":
        return "ACTIVE"
    if normalized in {"PAUSED", "CAMPAIGN_PAUSED", "ADSET_PAUSED"}:
        return "PAUSED"
    return "ARCHIVED"


def account_status(account_status_value: Any) -> str:
    return "ACTIVE" if str(account_status_value) == "1" else "ARCHIVED"


def cents_to_decimal(value: Any) -> str | None:
    if value in (None, ""):
        return None
    return str(Decimal(str(value)) / Decimal("100"))


def entity_table(level: str) -> str:
    return {"campaign": "campaigns", "adset": "adsets", "ad": "ads"}[level]


def meta_id_column(level: str) -> str:
    return {
        "campaign": "meta_campaign_id",
        "adset": "meta_adset_id",
        "ad": "meta_ad_id",
    }[level]


def metrics_payload(
    row: dict[str, Any], internal_column: str, internal_id: str | None
) -> dict[str, Any] | None:
    if not internal_id:
        return None
    actions = action_map(row.get("actions"))
    costs = action_map(row.get("cost_per_action_type"))
    leads = int(float(actions.get("lead", 0)))
    conversations = int(float(actions.get("onsite_conversion.messaging_conversation_started_7d", 0)))
    return {
        internal_column: internal_id,
        "metric_date": row["date_start"],
        "spend": decimal_or_zero(row.get("spend")),
        "impressions": int(row.get("impressions") or 0),
        "reach": int(row.get("reach") or 0),
        "clicks": int(row.get("clicks") or 0),
        "link_clicks": int(row.get("inline_link_clicks") or 0),
        "ctr": decimal_or_none(row.get("ctr")),
        "cpc": decimal_or_none(row.get("cpc")),
        "cpm": decimal_or_none(row.get("cpm")),
        "frequency": decimal_or_none(row.get("frequency")),
        "leads": leads,
        "cpl": costs.get("lead"),
        "conversations": conversations,
        "cost_per_conversation": costs.get(
            "onsite_conversion.messaging_conversation_started_7d"
        ),
        "landing_page_views": int(float(actions.get("landing_page_view", 0))),
        # A Graph API expõe a visualização curta como action_type=video_view;
        # `video_3_sec_watched_actions` não é um campo válido no Ads Insights.
        "video_views_3s": int(float(actions.get("video_view", 0))),
        "video_plays": action_total(row.get("video_play_actions")),
        "video_p25": action_total(row.get("video_p25_watched_actions")),
        "video_p50": action_total(row.get("video_p50_watched_actions")),
        "video_p75": action_total(row.get("video_p75_watched_actions")),
        "video_p95": action_total(row.get("video_p95_watched_actions")),
        "thruplays": action_total(row.get("video_thruplay_watched_actions")),
        "updated_at": now_iso(),
    }


def breakdown_payload(
    row: dict[str, Any],
    dimension_type: str,
    meta_breakdown: str,
    campaign_id: str | None,
) -> dict[str, Any] | None:
    dimension_value = row.get(meta_breakdown)
    if not campaign_id or dimension_value in (None, ""):
        return None
    actions = action_map(row.get("actions"))
    return {
        "campaign_id": campaign_id,
        "metric_date": row["date_start"],
        "dimension_type": dimension_type,
        "dimension_value": str(dimension_value),
        "spend": decimal_or_zero(row.get("spend")),
        "impressions": int(row.get("impressions") or 0),
        "reach": int(row.get("reach") or 0),
        "clicks": int(row.get("clicks") or 0),
        "link_clicks": int(row.get("inline_link_clicks") or 0),
        "leads": int(float(actions.get("lead", 0))),
        "conversations": int(float(actions.get(
            "onsite_conversion.messaging_conversation_started_7d", 0
        ))),
        "updated_at": now_iso(),
    }


def action_map(values: Any) -> dict[str, str]:
    return {
        str(item.get("action_type")): str(item.get("value"))
        for item in values or []
        if item.get("action_type") and item.get("value") is not None
    }


def action_total(values: Any) -> int:
    return int(sum(Decimal(str(item.get("value") or 0)) for item in values or []))


def creative_details(creative: dict[str, Any]) -> dict[str, Any]:
    story = creative.get("object_story_spec") or {}
    video_data = story.get("video_data") or {}
    link_data = story.get("link_data") or {}
    photo_data = story.get("photo_data") or {}
    call_to_action = (
        video_data.get("call_to_action")
        or link_data.get("call_to_action")
        or photo_data.get("call_to_action")
        or {}
    )
    call_value = call_to_action.get("value") or {}
    video_id = creative.get("video_id") or video_data.get("video_id")
    creative_type = creative.get("object_type")
    if not creative_type:
        creative_type = "VIDEO" if video_id else "IMAGE" if (
            creative.get("image_url") or link_data.get("picture") or photo_data
        ) else "UNKNOWN"
    return {
        "creative_name": creative.get("name"),
        "creative_type": str(creative_type),
        "thumbnail_url": creative.get("thumbnail_url") or link_data.get("picture"),
        "image_url": creative.get("image_url") or link_data.get("picture"),
        "video_id": str(video_id) if video_id else None,
        "primary_text": (
            creative.get("body") or video_data.get("message")
            or link_data.get("message") or photo_data.get("message")
        ),
        "headline": (
            creative.get("title") or video_data.get("title") or link_data.get("name")
        ),
        "call_to_action_type": (
            creative.get("call_to_action_type") or call_to_action.get("type")
        ),
        "destination_url": call_value.get("link") or link_data.get("link"),
    }


def decimal_or_zero(value: Any) -> str:
    return str(Decimal(str(value or 0)))


def decimal_or_none(value: Any) -> str | None:
    return None if value in (None, "") else str(Decimal(str(value)))
