from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from uuid import UUID

import pytest

from app.services.entity_services import (
    CampaignService,
    ClientService,
    EntityNotFoundError,
    MetricService,
    aggregate_metrics,
    build_insights,
    build_recommendations,
    build_investment_pacing,
    compare_metrics,
    configured_budget,
    resolve_periods,
)

CLIENT_ID = UUID("11111111-1111-1111-1111-111111111111")


class FakeQuery:
    def __init__(self, client: "FakeClient", table: str) -> None:
        self.client = client
        self.table = table
        self.is_count = False

    def select(self, _columns: str, *, count=None, head=False):
        self.is_count = count == "exact"
        return self

    def order(self, _column: str, desc=False):
        return self

    def eq(self, column: str, value: object):
        self.client.filters.append(("eq", column, value))
        return self

    def gte(self, column: str, value: object):
        self.client.filters.append(("gte", column, value))
        return self

    def lte(self, column: str, value: object):
        self.client.filters.append(("lte", column, value))
        return self

    def limit(self, _limit: int):
        return self

    def range(self, start: int, end: int):
        self.client.selected_range = (start, end)
        return self

    def execute(self):
        rows = self.client.rows.get(self.table, [])
        return SimpleNamespace(
            data=rows,
            count=self.client.counts.get(self.table, len(rows)) if self.is_count else None,
        )


class FakeClient:
    def __init__(self, rows=None, counts=None) -> None:
        self.rows = rows or {}
        self.counts = counts or {}
        self.filters: list[tuple[str, str, object]] = []
        self.selected_range: tuple[int, int] | None = None

    def table(self, table: str) -> FakeQuery:
        return FakeQuery(self, table)


def test_client_service_lists_archived_entities() -> None:
    rows = [{"id": str(CLIENT_ID), "name": "Histórico", "status": "ARCHIVED"}]
    result = ClientService(FakeClient(rows={"clients": rows})).list_clients(1, 20)  # type: ignore[arg-type]
    assert result["items"] == rows


def test_campaign_service_applies_filters_and_page_range() -> None:
    account_id = UUID("22222222-2222-2222-2222-222222222222")
    fake = FakeClient(counts={"campaigns": 42})
    result = CampaignService(fake).list_campaigns(2, 20, "ARCHIVED", account_id)  # type: ignore[arg-type]
    assert fake.filters == [
        ("eq", "status", "ARCHIVED"),
        ("eq", "meta_account_id", str(account_id)),
    ]
    assert fake.selected_range == (20, 39)
    assert result["pages"] == 3


def test_services_raise_not_found() -> None:
    fake = FakeClient()
    with pytest.raises(EntityNotFoundError):
        ClientService(fake).get_client(CLIENT_ID)  # type: ignore[arg-type]
    with pytest.raises(EntityNotFoundError):
        CampaignService(fake).get_campaign(CLIENT_ID)  # type: ignore[arg-type]


def test_custom_period_has_equal_previous_period() -> None:
    current, previous = resolve_periods(30, date(2025, 11, 1), date(2025, 11, 30))
    assert current == (date(2025, 11, 1), date(2025, 11, 30))
    assert previous == (date(2025, 10, 2), date(2025, 10, 31))


def test_180_day_period_has_equal_previous_period() -> None:
    current, previous = resolve_periods(180)
    assert (current[1] - current[0]).days + 1 == 180
    assert (previous[1] - previous[0]).days + 1 == 180
    assert previous[1] == current[0] - date.resolution


def test_period_rejects_incomplete_or_reversed_dates() -> None:
    with pytest.raises(ValueError):
        resolve_periods(30, date(2025, 11, 1), None)
    with pytest.raises(ValueError):
        resolve_periods(30, date(2025, 11, 2), date(2025, 11, 1))


def test_aggregate_calculates_business_metrics() -> None:
    result = aggregate_metrics([
        {"spend": "30", "impressions": 1000, "reach": 800, "clicks": 50,
         "link_clicks": 40, "leads": 2, "conversations": 3, "frequency": "1.2",
         "landing_page_views": 30, "video_views_3s": 300, "video_plays": 250,
         "video_p25": 200, "video_p50": 150, "video_p75": 100, "video_p95": 50,
         "thruplays": 75},
        {"spend": "15", "impressions": 500, "reach": 400, "clicks": 10,
         "link_clicks": 5, "leads": 1, "conversations": 1, "frequency": "1.35",
         "landing_page_views": 5, "video_views_3s": 100, "video_plays": 100,
         "video_p25": 80, "video_p50": 60, "video_p75": 40, "video_p95": 20,
         "thruplays": 25},
    ])
    assert result["spend"] == Decimal("45")
    assert result["frequency"] == Decimal("1.250000")
    assert result["landing_page_views"] == 35
    assert result["landing_page_view_rate"] == Decimal("77.777778")
    assert result["cost_per_landing_page_view"] == Decimal("1.285714")
    assert result["landing_page_conversion_rate"] == Decimal("8.571429")
    assert result["hook_rate"] == Decimal("26.666667")
    assert result["thruplay_rate"] == Decimal("28.571429")
    assert result["video_p95_rate"] == Decimal("20.000000")


def test_budget_helpers_compare_configured_budget_and_real_spend() -> None:
    assert configured_budget({"daily_budget": "50"}, 7) == (Decimal("350"), "DAILY_PERIOD")
    assert configured_budget({"lifetime_budget": "900"}, 7) == (Decimal("900"), "LIFETIME")
    assert configured_budget({}, 7) == (None, None)


def test_investment_pacing_projects_month_and_classifies_rhythm() -> None:
    result = build_investment_pacing(
        monthly_budget=Decimal("3100"), spent=Decimal("2000"),
        today=date(2026, 8, 10), currency="BRL",
    )
    assert result["remaining"] == Decimal("1100")
    assert result["projected_spend"] == Decimal("6200.00")
    assert result["pace_status"] == "ABOVE"


def test_investment_pacing_handles_missing_budget() -> None:
    result = build_investment_pacing(
        monthly_budget=None, spent=Decimal("100"),
        today=date(2026, 8, 10), currency="BRL",
    )
    assert result["pace_status"] == "NOT_CONFIGURED"
    assert result["projected_spend"] is None


def test_comparison_returns_percent_and_null_for_zero_baseline() -> None:
    current = aggregate_metrics([{"spend": 150, "leads": 15}])
    previous = aggregate_metrics([{"spend": 100, "leads": 0}])
    change = compare_metrics(current, previous)
    assert change["spend"] == Decimal("50.00")
    assert change["leads"] is None


def test_insights_warn_when_spend_has_no_conversion() -> None:
    current = aggregate_metrics([
        {"spend": 30, "impressions": 1500, "clicks": 10, "leads": 0, "conversations": 0}
    ])
    codes = {item["code"] for item in build_insights(current, aggregate_metrics([]))}
    assert codes == {"SPEND_WITHOUT_CONVERSION", "LOW_CTR"}


def test_insights_do_not_claim_low_ctr_without_minimum_volume() -> None:
    current = aggregate_metrics([
        {"spend": 5, "impressions": 100, "clicks": 0, "leads": 0, "conversations": 0}
    ])
    assert [item["code"] for item in build_insights(current, aggregate_metrics([]))] == [
        "NO_STRONG_SIGNAL"
    ]


def test_metric_service_filters_period_without_status_filter() -> None:
    fake = FakeClient(rows={"campaign_metrics": []})
    MetricService(fake).list_metrics(  # type: ignore[arg-type]
        "campaigns", date(2025, 11, 1), date(2025, 11, 30), 1, 20, CLIENT_ID
    )
    assert fake.filters == [
        ("gte", "metric_date", "2025-11-01"),
        ("lte", "metric_date", "2025-11-30"),
        ("eq", "campaign_id", str(CLIENT_ID)),
    ]
    assert all(column != "status" for _, column, _ in fake.filters)


def test_recommendations_are_explainable_and_prioritized() -> None:
    recommendations = build_recommendations([{
        "entity_type": "ADSET", "entity_id": str(CLIENT_ID), "name": "Público A",
        "spend": Decimal("35"), "impressions": 2000, "conversations": 0,
        "ctr": Decimal("0.5"),
    }], [])
    assert [item["rule_code"] for item in recommendations] == [
        "SPEND_WITHOUT_CONVERSATION", "LOW_CTR"
    ]
    assert recommendations[0]["priority"] == "HIGH"
    assert "35.00" in str(recommendations[0]["evidence"])
