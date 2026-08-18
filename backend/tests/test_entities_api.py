from datetime import date, datetime, timezone
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.api.dependencies import supabase_client_dependency
from app.main import app


ID = "11111111-1111-1111-1111-111111111111"
NOW = datetime(2026, 8, 15, tzinfo=timezone.utc).isoformat()


class FakeQuery:
    def __init__(self, client: "FakeClient", table: str) -> None:
        self.client = client
        self.table = table
        self.is_count = False
        self.head = False
        self.filters = []

    def select(self, _columns: str, *, count=None, head=False):
        self.is_count = count == "exact"
        self.head = head
        return self

    def order(self, _column: str, desc=False):
        return self

    def eq(self, column: str, value: str):
        self.filters.append(("eq", column, value))
        return self

    def in_(self, column: str, values: list[str]):
        self.filters.append(("in", column, values))
        return self

    def gte(self, column: str, value: str):
        self.filters.append(("gte", column, value))
        return self

    def lte(self, column: str, value: str):
        self.filters.append(("lte", column, value))
        return self

    def limit(self, _limit: int):
        return self

    def range(self, _start: int, _end: int):
        return self

    def execute(self):
        if self.client.failure:
            raise RuntimeError("database error")
        rows = self.client.rows.get(self.table, [])
        for operation, column, value in self.filters:
            if operation == "eq":
                rows = [row for row in rows if str(row.get(column)) == str(value)]
            elif operation == "in":
                rows = [row for row in rows if str(row.get(column)) in value]
            elif operation == "gte":
                rows = [row for row in rows if str(row.get(column)) >= str(value)]
            elif operation == "lte":
                rows = [row for row in rows if str(row.get(column)) <= str(value)]
        if self.is_count and self.head:
            return SimpleNamespace(data=None, count=len(rows))
        return SimpleNamespace(data=rows, count=len(rows) if self.is_count else None)


class FakeClient:
    def __init__(self, rows=None, failure=False) -> None:
        self.rows = rows or {}
        self.counts = {}
        self.failure = failure

    def table(self, table: str) -> FakeQuery:
        return FakeQuery(self, table)


client = TestClient(app)


def override(fake: FakeClient) -> None:
    app.dependency_overrides[supabase_client_dependency] = lambda: fake


def teardown_function() -> None:
    app.dependency_overrides.clear()


def test_list_clients_keeps_archived_records() -> None:
    row = {
        "id": ID,
        "name": "Cliente histórico",
        "slug": "cliente-historico",
        "status": "ARCHIVED",
        "created_at": NOW,
        "updated_at": NOW,
    }
    override(FakeClient(rows={"clients": [row]}))

    response = client.get("/api/v1/clients")

    assert response.status_code == 200
    body = response.json()
    assert body["items"][0]["status"] == "ARCHIVED"
    assert body["total"] == 1


def test_invalid_pagination_and_status_return_422() -> None:
    override(FakeClient())

    assert client.get("/api/v1/clients?page=0").status_code == 422
    assert client.get("/api/v1/clients?page_size=101").status_code == 422
    assert client.get("/api/v1/clients?status=DELETED").status_code == 422


def test_get_client_returns_404() -> None:
    override(FakeClient())

    response = client.get(f"/api/v1/clients/{ID}")

    assert response.status_code == 404
    assert response.json()["detail"]["id"] == ID


def test_invalid_uuid_returns_422() -> None:
    override(FakeClient())

    assert client.get("/api/v1/campaigns/not-a-uuid").status_code == 422


def test_supabase_failure_returns_503() -> None:
    override(FakeClient(failure=True))

    response = client.get("/api/v1/campaigns")

    assert response.status_code == 503
    assert response.json()["detail"] == "Não foi possível consultar o Supabase."


def test_all_read_routes_are_documented() -> None:
    paths = app.openapi()["paths"]
    expected = {
        "/api/v1/clients",
        "/api/v1/clients/{client_id}",
        "/api/v1/meta-accounts",
        "/api/v1/campaigns",
        "/api/v1/campaigns/{campaign_id}",
        "/api/v1/adsets",
        "/api/v1/adsets/{adset_id}",
        "/api/v1/ads",
        "/api/v1/ads/{ad_id}",
        "/api/v1/metrics/campaigns",
        "/api/v1/metrics/adsets",
        "/api/v1/metrics/ads",
        "/api/v1/dashboard",
    }

    assert expected <= paths.keys()


def test_dashboard_serializes_money_as_json_number() -> None:
    account_id = "22222222-2222-2222-2222-222222222222"
    campaign_id = "33333333-3333-3333-3333-333333333333"
    adset_id = "44444444-4444-4444-4444-444444444444"
    metric_date = date.today().isoformat()
    fake = FakeClient(rows={
        "clients": [{"id": ID}],
        "meta_accounts": [{"id": account_id, "client_id": ID}],
        "campaigns": [{"id": campaign_id, "meta_account_id": account_id}],
        "adsets": [{"id": adset_id, "campaign_id": campaign_id}],
        "ads": [{"id": "55555555-5555-5555-5555-555555555555", "adset_id": adset_id}],
        "campaign_metrics": [{
            "campaign_id": campaign_id, "metric_date": metric_date,
            "spend": "12.50", "impressions": 1000, "reach": 800, "clicks": 25,
            "link_clicks": 20,
            "leads": 1, "conversations": 2,
        }],
    })
    override(fake)

    response = client.get("/api/v1/dashboard")

    assert response.status_code == 200
    assert response.json()["metrics"] == {
        "spend": 12.5, "impressions": 1000, "reach": 800, "clicks": 25,
        "link_clicks": 20, "leads": 1, "conversations": 2, "cpl": 12.5,
        "ctr": 2.5, "cpc": 0.5, "cpm": 12.5, "link_ctr": 2.0,
        "frequency": 1.25,
    }


def test_dashboard_validates_period_filters() -> None:
    override(FakeClient())
    assert client.get("/api/v1/dashboard?days=30").status_code == 200
    assert client.get("/api/v1/dashboard?days=120").status_code == 200
    assert client.get("/api/v1/dashboard?days=8").status_code == 422
    assert client.get("/api/v1/dashboard?date_from=2025-11-01").status_code == 422


def test_metrics_reject_reversed_period() -> None:
    override(FakeClient())
    response = client.get(
        "/api/v1/metrics/campaigns?date_from=2025-11-30&date_to=2025-11-01"
    )
    assert response.status_code == 422
