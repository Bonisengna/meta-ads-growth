import json

import httpx
import pytest

from app.services.meta_graph_client import MetaGraphClient, MetaGraphError, account_node


def test_lists_all_paginated_ad_accounts_without_exposing_token() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.params.get("after") == "next-page":
            return httpx.Response(200, json={"data": [{"id": "act_2", "account_id": "2"}]})
        return httpx.Response(
            200,
            json={
                "data": [{"id": "act_1", "account_id": "1"}],
                "paging": {
                    "next": "https://graph.facebook.com/v25.0/me/adaccounts?after=next-page"
                },
            },
        )

    with MetaGraphClient("secret-token", transport=httpx.MockTransport(handler)) as client:
        rows = client.list_ad_accounts()

    assert [row["account_id"] for row in rows] == ["1", "2"]
    assert requests[0].url.params["access_token"] == "secret-token"
    assert "access_token" not in requests[1].url.params


def test_insights_serializes_time_range_and_level() -> None:
    captured: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return httpx.Response(200, json={"data": []})

    with MetaGraphClient("token", transport=httpx.MockTransport(handler)) as client:
        client.list_daily_insights("123", "campaign", "2026-08-15", "2026-08-15")

    assert captured[0].url.path.endswith("/act_123/insights")
    assert captured[0].url.params["level"] == "campaign"
    assert json.loads(captured[0].url.params["time_range"])["since"] == "2026-08-15"
    fields = captured[0].url.params["fields"].split(",")
    assert "actions" in fields
    assert "video_3_sec_watched_actions" not in fields


def test_breakdown_insights_send_one_supported_dimension() -> None:
    captured: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return httpx.Response(200, json={"data": []})

    with MetaGraphClient("token", transport=httpx.MockTransport(handler)) as client:
        client.list_breakdown_insights("123", "age", "2026-08-01", "2026-08-15")

    assert captured[0].url.params["breakdowns"] == "age"
    assert captured[0].url.params["level"] == "campaign"
    assert "actions" in captured[0].url.params["fields"]


def test_placement_breakdown_omits_incompatible_actions_field() -> None:
    captured: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return httpx.Response(200, json={"data": []})

    with MetaGraphClient("token", transport=httpx.MockTransport(handler)) as client:
        client.list_breakdown_insights(
            "123", "platform_position", "2026-08-01", "2026-08-15"
        )

    fields = captured[0].url.params["fields"].split(",")
    assert "actions" not in fields
    assert "inline_link_clicks" not in fields
    assert "clicks" in fields
    assert captured[0].url.params["action_breakdowns"] == "[]"


def test_http_failure_becomes_safe_meta_error() -> None:
    transport = httpx.MockTransport(lambda _request: httpx.Response(401, json={"error": {}}))

    with MetaGraphClient("invalid", transport=transport) as client:
        with pytest.raises(MetaGraphError, match="Falha ao consultar"):
            client.list_ad_accounts()


def test_http_failure_preserves_meta_error_details() -> None:
    transport = httpx.MockTransport(
        lambda _request: httpx.Response(
            400,
            json={"error": {"message": "Invalid parameter", "code": 100}},
        )
    )

    with MetaGraphClient("token", transport=transport) as client:
        with pytest.raises(MetaGraphError, match="Invalid parameter") as captured:
            client.list_ad_accounts()

    assert captured.value.code == 100
    assert captured.value.status_code == 400


def test_account_node_adds_prefix_once() -> None:
    assert account_node("123") == "act_123"
    assert account_node("act_123") == "act_123"
