from datetime import date
from decimal import Decimal

import pytest

from app.services.meta_graph_client import MetaGraphError

from app.services.meta_sync_service import (
    MetaSyncService,
    action_map,
    action_total,
    cents_to_decimal,
    creative_details,
    entity_status,
    metrics_payload,
)


class FakeResponse:
    def __init__(self, data=None) -> None:
        self.data = data


class FakeQuery:
    def __init__(self, database: dict[str, list[dict]], table: str) -> None:
        self.database = database
        self.table = table
        self.operation = "select"
        self.payload = None
        self.conflict = None
        self.filters: list[tuple[str, object]] = []

    def select(self, _columns: str):
        return self

    def upsert(self, payload, *, on_conflict: str):
        self.operation = "upsert"
        self.payload = payload
        self.conflict = on_conflict
        return self

    def update(self, payload):
        self.operation = "update"
        self.payload = payload
        return self

    def eq(self, column: str, value: object):
        self.filters.append((column, value))
        return self

    def limit(self, _limit: int):
        return self

    def execute(self):
        rows = self.database.setdefault(self.table, [])
        if self.operation == "upsert":
            payloads = self.payload if isinstance(self.payload, list) else [self.payload]
            saved = []
            conflict_columns = self.conflict.split(",")
            for payload in payloads:
                existing = next(
                    (
                        row
                        for row in rows
                        if all(row.get(column) == payload.get(column) for column in conflict_columns)
                    ),
                    None,
                )
                if existing:
                    existing.update(payload)
                    saved.append(existing)
                else:
                    created = {"id": f"{self.table}-{len(rows) + 1}", **payload}
                    rows.append(created)
                    saved.append(created)
            return FakeResponse(saved)
        matching = [
            row for row in rows if all(row.get(column) == value for column, value in self.filters)
        ]
        if self.operation == "update":
            for row in matching:
                row.update(self.payload)
        return FakeResponse(matching)


class FakeSupabase:
    def __init__(self, database: dict[str, list[dict]]) -> None:
        self.database = database

    def table(self, table: str) -> FakeQuery:
        return FakeQuery(self.database, table)


class FakeMeta:
    def __init__(self) -> None:
        self.insight_ranges: list[tuple[str, str, str]] = []

    def list_ad_accounts(self):
        return [{"account_id": "123", "name": "Conta", "account_status": 1}]

    def list_campaigns(self, _account_id: str):
        return [{"id": "new-campaign", "name": "Nova", "effective_status": "ACTIVE"}]

    def list_adsets(self, _account_id: str):
        return []

    def list_ads(self, _account_id: str):
        return []

    def list_daily_insights(self, _account_id: str, level: str, since: str, until: str):
        self.insight_ranges.append((level, since, until))
        if level != "campaign":
            return []
        return [
            {
                "campaign_id": "new-campaign",
                "date_start": "2026-08-15",
                "spend": "20",
                "actions": [{"action_type": "lead", "value": "2"}],
            }
        ]

    def list_breakdown_insights(
        self, _account_id: str, breakdown: str, _since: str, _until: str
    ):
        if breakdown != "age":
            return []
        return [{
            "campaign_id": "new-campaign", "date_start": "2026-08-15",
            "age": "25-34", "spend": "20", "impressions": "1000",
            "reach": "800", "inline_link_clicks": "25",
            "actions": [{"action_type": "lead", "value": "2"}],
        }]


def test_meta_status_preserves_paused_and_archives_historical_entities() -> None:
    assert entity_status("ACTIVE") == "ACTIVE"
    assert entity_status("PAUSED") == "PAUSED"
    assert entity_status("CAMPAIGN_PAUSED") == "PAUSED"
    assert entity_status("DELETED") == "ARCHIVED"


def test_meta_budget_cents_are_converted() -> None:
    assert cents_to_decimal("1250") == "12.5"
    assert cents_to_decimal(None) is None


def test_action_map_extracts_meta_action_values() -> None:
    assert action_map([{"action_type": "lead", "value": "3"}]) == {"lead": "3"}


def test_action_total_sums_video_and_page_events() -> None:
    assert action_total([{"value": "3"}, {"value": "2"}]) == 5


def test_creative_details_normalizes_video_content() -> None:
    details = creative_details({
        "name": "Criativo A", "thumbnail_url": "https://example.com/thumb.jpg",
        "object_story_spec": {"video_data": {
            "video_id": "video-1", "message": "Texto principal", "title": "Título",
            "call_to_action": {"type": "LEARN_MORE", "value": {"link": "https://example.com"}},
        }},
    })
    assert details == {
        "creative_name": "Criativo A", "creative_type": "VIDEO",
        "thumbnail_url": "https://example.com/thumb.jpg", "image_url": None,
        "video_id": "video-1", "primary_text": "Texto principal", "headline": "Título",
        "call_to_action_type": "LEARN_MORE", "destination_url": "https://example.com",
    }


def test_metrics_payload_maps_daily_values_for_upsert() -> None:
    payload = metrics_payload(
        {
            "date_start": date(2026, 8, 15).isoformat(),
            "spend": "25.50",
            "impressions": "1000",
            "reach": "800",
            "clicks": "30",
            "inline_link_clicks": "20",
            "ctr": "3.0",
            "actions": [{"action_type": "lead", "value": "2"}],
            "cost_per_action_type": [{"action_type": "lead", "value": "12.75"}],
        },
        "campaign_id",
        "internal-id",
    )

    assert payload is not None
    assert payload["campaign_id"] == "internal-id"
    assert Decimal(payload["spend"]) == Decimal("25.50")
    assert payload["leads"] == 2
    assert payload["cpl"] == "12.75"


def test_metrics_without_internal_entity_are_skipped() -> None:
    assert metrics_payload({"date_start": "2026-08-15"}, "ad_id", None) is None


def test_sync_upserts_current_entities_and_archives_missing_ones() -> None:
    database = {
        "meta_accounts": [{"id": "account-internal", "meta_account_id": "123"}],
        "campaigns": [
            {
                "id": "old-internal",
                "meta_account_id": "account-internal",
                "meta_campaign_id": "old-campaign",
                "status": "ACTIVE",
            }
        ],
        "adsets": [],
        "ads": [],
    }
    service = MetaSyncService(FakeSupabase(database), FakeMeta())  # type: ignore[arg-type]

    result = service.sync_account(
        __import__("uuid").UUID("11111111-1111-1111-1111-111111111111"), "act_123"
    )

    assert result["meta_accounts"] == 1
    assert result["campaigns"] == 1
    assert result["changes"] == {
        "meta_accounts": {"imported": 0, "updated": 1, "archived": 0},
        "campaigns": {"imported": 1, "updated": 0, "archived": 1},
        "adsets": {"imported": 0, "updated": 0, "archived": 0},
        "ads": {"imported": 0, "updated": 0, "archived": 0},
    }
    campaigns = database["campaigns"]
    assert next(row for row in campaigns if row["meta_campaign_id"] == "old-campaign")["status"] == "ARCHIVED"
    assert next(row for row in campaigns if row["meta_campaign_id"] == "new-campaign")["status"] == "ACTIVE"


def test_daily_metrics_are_upserted_by_entity_and_date() -> None:
    database = {
        "campaigns": [{"id": "campaign-internal", "meta_campaign_id": "new-campaign"}],
        "adsets": [],
        "ads": [],
        "campaign_metrics": [],
        "adset_metrics": [],
        "ad_metrics": [],
    }
    service = MetaSyncService(FakeSupabase(database), FakeMeta())  # type: ignore[arg-type]

    result = service.sync_daily_metrics("123", date(2026, 8, 15))

    assert result == {"campaign": 1, "adset": 0, "ad": 0}
    assert database["campaign_metrics"][0]["campaign_id"] == "campaign-internal"
    assert database["campaign_metrics"][0]["metric_date"] == "2026-08-15"


def test_daily_metrics_accept_historical_interval() -> None:
    database = {
        "campaigns": [{"id": "campaign-internal", "meta_campaign_id": "new-campaign"}],
        "adsets": [], "ads": [], "campaign_metrics": [], "adset_metrics": [], "ad_metrics": [],
    }
    meta = FakeMeta()
    service = MetaSyncService(FakeSupabase(database), meta)  # type: ignore[arg-type]

    service.sync_daily_metrics("123", date(2025, 11, 1), date(2025, 11, 30))

    assert meta.insight_ranges == [
        ("campaign", "2025-11-01", "2025-11-30"),
        ("adset", "2025-11-01", "2025-11-30"),
        ("ad", "2025-11-01", "2025-11-30"),
    ]


def test_breakdown_metrics_are_stored_separately() -> None:
    database = {
        "campaigns": [{"id": "campaign-internal", "meta_campaign_id": "new-campaign"}],
        "breakdown_metrics": [],
    }
    service = MetaSyncService(FakeSupabase(database), FakeMeta())  # type: ignore[arg-type]

    result = service.sync_breakdown_metrics("123", date(2026, 8, 15))

    assert result["age"] == 1
    assert database["breakdown_metrics"][0]["dimension_type"] == "AGE"
    assert database["breakdown_metrics"][0]["dimension_value"] == "25-34"


def test_breakdown_error_identifies_the_failed_dimension() -> None:
    class FailingMeta(FakeMeta):
        def list_breakdown_insights(
            self, _account_id: str, breakdown: str, _since: str, _until: str
        ):
            if breakdown == "platform_position":
                raise MetaGraphError("Invalid combination", code=100, status_code=400)
            return []

    database = {"campaigns": [], "breakdown_metrics": []}
    service = MetaSyncService(FakeSupabase(database), FailingMeta())  # type: ignore[arg-type]

    with pytest.raises(MetaGraphError, match="PLACEMENT/platform_position") as captured:
        service.sync_breakdown_metrics("123", date(2026, 8, 15))

    assert captured.value.code == 100
    assert captured.value.status_code == 400
