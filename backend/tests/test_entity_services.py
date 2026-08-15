from types import SimpleNamespace
from uuid import UUID

import pytest

from app.services.entity_services import (
    CampaignService,
    ClientService,
    DashboardService,
    EntityNotFoundError,
)


CLIENT_ID = UUID("11111111-1111-1111-1111-111111111111")


class FakeQuery:
    def __init__(self, client: "FakeClient", table: str) -> None:
        self.client = client
        self.table = table
        self.is_count = False
        self.filters: list[tuple[str, str]] = []
        self.selected_range: tuple[int, int] | None = None

    def select(self, _columns: str, *, count=None, head=False):
        self.is_count = count == "exact"
        self.client.head = head
        return self

    def order(self, _column: str):
        return self

    def eq(self, column: str, value: str):
        self.filters.append((column, value))
        self.client.filters = self.filters
        return self

    def limit(self, _limit: int):
        return self

    def range(self, start: int, end: int):
        self.selected_range = (start, end)
        self.client.selected_range = self.selected_range
        return self

    def execute(self):
        if self.is_count and self.client.head:
            return SimpleNamespace(data=None, count=self.client.counts[self.table])
        return SimpleNamespace(
            data=self.client.rows.get(self.table, []),
            count=self.client.counts.get(self.table, 0) if self.is_count else None,
        )


class FakeClient:
    def __init__(self, rows=None, counts=None) -> None:
        self.rows = rows or {}
        self.counts = counts or {}
        self.filters: list[tuple[str, str]] = []
        self.selected_range: tuple[int, int] | None = None
        self.head = False

    def table(self, table: str) -> FakeQuery:
        return FakeQuery(self, table)


def test_client_service_lists_archived_entities() -> None:
    rows = [{"id": str(CLIENT_ID), "name": "Histórico", "status": "ARCHIVED"}]
    service = ClientService(FakeClient(rows={"clients": rows}))  # type: ignore[arg-type]

    result = service.list_clients(page=1, page_size=20)

    assert result["items"] == rows


def test_campaign_service_applies_filters_and_page_range() -> None:
    account_id = UUID("22222222-2222-2222-2222-222222222222")
    fake = FakeClient(counts={"campaigns": 42})
    service = CampaignService(fake)  # type: ignore[arg-type]

    result = service.list_campaigns(2, 20, "ARCHIVED", account_id)

    assert fake.filters == [
        ("status", "ARCHIVED"),
        ("meta_account_id", str(account_id)),
    ]
    assert fake.selected_range == (20, 39)
    assert result["total"] == 42
    assert result["pages"] == 3


def test_client_service_raises_not_found() -> None:
    service = ClientService(FakeClient())  # type: ignore[arg-type]

    with pytest.raises(EntityNotFoundError):
        service.get_client(CLIENT_ID)


def test_campaign_service_raises_not_found() -> None:
    service = CampaignService(FakeClient())  # type: ignore[arg-type]

    with pytest.raises(EntityNotFoundError):
        service.get_campaign(CLIENT_ID)


def test_dashboard_aggregates_campaign_metrics() -> None:
    counts = {"clients": 2, "meta_accounts": 3, "campaigns": 4, "adsets": 5, "ads": 6}
    rows = {"campaign_metrics": [{"spend": "30.00", "leads": 2}, {"spend": "15", "leads": 1}]}
    service = DashboardService(FakeClient(rows=rows, counts=counts))  # type: ignore[arg-type]

    result = service.get_dashboard()

    assert result["campaigns"] == 4
    assert result["metrics"] == {"spend": 45, "leads": 3, "cpl": 15}


def test_dashboard_returns_null_cpl_without_leads() -> None:
    counts = {table: 0 for table in DashboardService.ENTITY_TABLES}
    service = DashboardService(FakeClient(counts=counts))  # type: ignore[arg-type]

    assert service.get_dashboard()["metrics"]["cpl"] is None  # type: ignore[index]
