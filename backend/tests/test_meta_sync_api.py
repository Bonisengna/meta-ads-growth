import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.models.meta_sync import SyncRequestCreate


client = TestClient(app)


def test_sync_control_routes_are_documented() -> None:
    paths = app.openapi()["paths"]

    assert "/api/v1/meta-sync/requests" in paths
    assert "/api/v1/meta-sync/runs" in paths
    assert "/api/v1/meta-sync/recover" in paths


def test_sync_history_requires_authentication() -> None:
    response = client.get("/api/v1/meta-sync/runs")

    assert response.status_code == 401
    assert "Token de acesso" in response.json()["detail"]


def test_sync_request_accepts_360_day_backfill() -> None:
    payload = SyncRequestCreate(
        client_id="11111111-1111-1111-1111-111111111111", lookback_days=360
    )

    assert payload.lookback_days == 360


def test_sync_request_rejects_more_than_360_days() -> None:
    with pytest.raises(ValidationError):
        SyncRequestCreate(
            client_id="11111111-1111-1111-1111-111111111111", lookback_days=361
        )
