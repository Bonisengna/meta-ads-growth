from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

import app.api.dependencies as dependencies
from app.api.dependencies import authenticated_supabase_client_dependency
from app.config.settings import Settings
from app.middleware.rate_limit import RateLimitMiddleware
from app.main import app as main_app


class FakeAuth:
    def __init__(self, valid: bool) -> None:
        self.valid = valid

    def get_user(self, _token: str):
        if not self.valid:
            raise RuntimeError("invalid token")
        return SimpleNamespace(user=SimpleNamespace(id="user-1"))


class FakePostgrest:
    def __init__(self) -> None:
        self.token = None

    def auth(self, token: str) -> None:
        self.token = token


class FakeClient:
    def __init__(self, valid=True) -> None:
        self.auth = FakeAuth(valid)
        self.postgrest = FakePostgrest()


def credentials(token="valid-token"):
    return SimpleNamespace(scheme="Bearer", credentials=token)


def test_authentication_accepts_valid_supabase_user(monkeypatch) -> None:
    fake = FakeClient()
    settings = SimpleNamespace(
        supabase_url="https://project.supabase.co", supabase_publishable_key="publishable"
    )
    monkeypatch.setattr(dependencies, "get_settings", lambda: settings)
    monkeypatch.setattr(dependencies, "create_client", lambda _url, _key: fake)

    result = authenticated_supabase_client_dependency(credentials())

    assert result is fake
    assert fake.postgrest.token == "valid-token"


def test_authentication_rejects_invalid_token(monkeypatch) -> None:
    settings = SimpleNamespace(
        supabase_url="https://project.supabase.co", supabase_publishable_key="publishable"
    )
    monkeypatch.setattr(dependencies, "get_settings", lambda: settings)
    monkeypatch.setattr(dependencies, "create_client", lambda _url, _key: FakeClient(False))

    with pytest.raises(Exception) as captured:
        authenticated_supabase_client_dependency(credentials("invalid"))
    assert captured.value.status_code == 401


def test_production_rejects_debug_and_wildcard_cors() -> None:
    with pytest.raises(ValueError, match="DEBUG"):
        Settings(_env_file=None, environment="production", debug=True)
    with pytest.raises(ValueError, match="CORS"):
        Settings(
            _env_file=None,
            environment="production",
            debug=False,
            cors_allowed_origins="*",
        )


def test_rate_limit_returns_429() -> None:
    test_app = FastAPI()
    test_app.add_middleware(RateLimitMiddleware, requests=1, window_seconds=60)

    @test_app.get("/private")
    def private():
        return {"ok": True}

    test_client = TestClient(test_app)
    assert test_client.get("/private").status_code == 200
    response = test_client.get("/private")
    assert response.status_code == 429
    assert response.headers["Retry-After"] == "60"


def test_rate_limit_error_keeps_cors_headers() -> None:
    test_app = FastAPI()
    test_app.add_middleware(RateLimitMiddleware, requests=1, window_seconds=60)
    test_app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["GET"],
        allow_headers=["Authorization"],
    )

    @test_app.get("/private")
    def private():
        return {"ok": True}

    test_client = TestClient(test_app)
    headers = {"Origin": "http://localhost:3000"}
    assert test_client.get("/private", headers=headers).status_code == 200
    response = test_client.get("/private", headers=headers)

    assert response.status_code == 429
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert response.headers["Retry-After"] == "60"


def test_data_endpoint_requires_bearer_token() -> None:
    response = TestClient(main_app).get("/api/v1/clients")
    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_unauthorized_response_keeps_cors_headers() -> None:
    response = TestClient(main_app).get(
        "/api/v1/clients", headers={"Origin": "http://localhost:3000"}
    )
    assert response.status_code == 401
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_cors_accepts_only_configured_local_origin() -> None:
    response = TestClient(main_app).options(
        "/api/v1/clients",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_cors_allows_secure_settings_post() -> None:
    response = TestClient(main_app).options(
        "/api/v1/settings/meta",
        headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "POST"},
    )
    assert response.status_code == 200
    assert "POST" in response.headers["access-control-allow-methods"]


def test_cors_allows_client_update_patch() -> None:
    response = TestClient(main_app).options(
        "/api/v1/settings/clients/client-id",
        headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "PATCH"},
    )
    assert response.status_code == 200
    assert "PATCH" in response.headers["access-control-allow-methods"]
