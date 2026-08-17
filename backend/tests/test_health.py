from fastapi.testclient import TestClient

from app.database.supabase import SupabaseNotConfiguredError
from app.api.dependencies import authenticated_supabase_client_dependency
from app.api.health import supabase_client_dependency
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
    app.dependency_overrides[authenticated_supabase_client_dependency] = lambda: object()

    response = client.get("/health/database")

    assert response.status_code == 503
    detail = response.json()["detail"]
    assert detail["status"] == "unconfigured"
    assert detail["service"] == "supabase"
    app.dependency_overrides.clear()


def test_operational_health_requires_authentication() -> None:
    assert client.get("/health/database").status_code == 401
    assert client.get("/health/meta").status_code == 401
