from datetime import datetime, timezone
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

    def select(self, _columns: str, *, count=None, head=False):
        self.is_count = count == "exact"
        self.head = head
        return self

    def order(self, _column: str):
        return self

    def eq(self, _column: str, _value: str):
        return self

    def limit(self, _limit: int):
        return self

    def range(self, _start: int, _end: int):
        return self

    def execute(self):
        if self.client.failure:
            raise RuntimeError("database error")
        if self.is_count and self.head:
            return SimpleNamespace(data=None, count=self.client.counts.get(self.table, 0))
        rows = self.client.rows.get(self.table, [])
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
        "/api/v1/dashboard",
    }

    assert expected <= paths.keys()
