from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from supabase import Client

from app.services.meta_graph_client import MetaGraphClient


class MetaEntityNotAccessibleError(LookupError):
    pass


class MetaSyncService:
    """Orquestra Meta → Supabase preservando identidades e histórico."""

    def __init__(self, supabase: Client, meta: MetaGraphClient) -> None:
        self.supabase = supabase
        self.meta = meta

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
        (
            self.supabase.table("meta_accounts")
            .update({"last_synced_at": now_iso(), "updated_at": now_iso()})
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
            _, created = self._upsert_one(
                "ads",
                {
                    "adset_id": adset_id,
                    "meta_ad_id": row["id"],
                    "name": row.get("name") or row["id"],
                    "status": entity_status(row.get("effective_status")),
                    "creative_id": creative.get("id"),
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
    return "ACTIVE" if effective_status == "ACTIVE" else "ARCHIVED"


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
        "updated_at": now_iso(),
    }


def action_map(values: Any) -> dict[str, str]:
    return {
        str(item.get("action_type")): str(item.get("value"))
        for item in values or []
        if item.get("action_type") and item.get("value") is not None
    }


def decimal_or_zero(value: Any) -> str:
    return str(Decimal(str(value or 0)))


def decimal_or_none(value: Any) -> str | None:
    return None if value in (None, "") else str(Decimal(str(value)))
