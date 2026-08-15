from fastapi.testclient import TestClient

from app.database.supabase import SupabaseNotConfiguredError
from app.main import app

client = TestClient(app)


def test_root() -> None:
    response = client.get("/")

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "DescompliADS API"
    assert body["status"] == "running"
    assert body["docs"] == "/docs"


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["timezone"] == "America/Sao_Paulo"


def test_api_v1_health() -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_database_health_returns_503_when_supabase_is_not_configured(monkeypatch) -> None:
    def fake_get_client():
        raise SupabaseNotConfiguredError("não configurado")

    monkeypatch.setattr("app.api.health.get_supabase_client", fake_get_client)

    response = client.get("/health/database")

    assert response.status_code == 503
    detail = response.json()["detail"]
    assert detail["status"] == "unconfigured"
    assert detail["service"] == "supabase"
