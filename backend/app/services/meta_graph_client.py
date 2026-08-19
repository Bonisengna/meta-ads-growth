from collections.abc import Iterator
from typing import Any

import httpx


class MetaGraphError(RuntimeError):
    def __init__(self, message: str, *, code: int | None = None, status_code: int | None = None) -> None:
        self.code = code
        self.status_code = status_code
        super().__init__(message)


class MetaGraphClient:
    """Cliente HTTP isolado para leituras da Meta Graph API."""

    def __init__(
        self,
        access_token: str,
        *,
        version: str = "v25.0",
        base_url: str = "https://graph.facebook.com",
        timeout: float = 30.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.access_token = access_token
        self.version = version.strip("/")
        self.http = httpx.Client(
            base_url=f"{base_url.rstrip('/')}/{self.version}",
            timeout=timeout,
            transport=transport,
        )

    def close(self) -> None:
        self.http.close()

    def __enter__(self) -> "MetaGraphClient":
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()

    def validate_token(self, app_id: str, app_secret: str) -> dict[str, Any]:
        payload = self._get(
            "/debug_token",
            params={
                "input_token": self.access_token,
                "access_token": f"{app_id}|{app_secret}",
            },
            include_user_token=False,
        )
        return payload.get("data", {})

    def list_ad_accounts(self) -> list[dict[str, Any]]:
        return list(
            self._paginate(
                "/me/adaccounts",
                fields="id,account_id,name,currency,timezone_name,account_status",
            )
        )

    def list_campaigns(self, account_id: str) -> list[dict[str, Any]]:
        return list(
            self._paginate(
                f"/{account_node(account_id)}/campaigns",
                fields="id,name,objective,effective_status,created_time,updated_time",
            )
        )

    def list_adsets(self, account_id: str) -> list[dict[str, Any]]:
        return list(
            self._paginate(
                f"/{account_node(account_id)}/adsets",
                fields=(
                    "id,campaign_id,name,effective_status,optimization_goal,billing_event,"
                    "daily_budget,lifetime_budget,created_time,updated_time"
                ),
            )
        )

    def list_ads(self, account_id: str) -> list[dict[str, Any]]:
        return list(
            self._paginate(
                f"/{account_node(account_id)}/ads",
                fields="id,adset_id,name,effective_status,creative{id},created_time,updated_time",
            )
        )

    def list_daily_insights(
        self, account_id: str, level: str, since: str, until: str
    ) -> list[dict[str, Any]]:
        if level not in {"campaign", "adset", "ad"}:
            raise ValueError("level deve ser campaign, adset ou ad")
        return list(
            self._paginate(
                f"/{account_node(account_id)}/insights",
                fields=(
                    f"{level}_id,date_start,spend,impressions,reach,clicks,inline_link_clicks,"
                    "ctr,cpc,cpm,frequency,actions,cost_per_action_type"
                ),
                level=level,
                time_increment="1",
                time_range={"since": since, "until": until},
            )
        )

    def list_breakdown_insights(
        self, account_id: str, breakdown: str, since: str, until: str
    ) -> list[dict[str, Any]]:
        allowed = {
            "age", "gender", "publisher_platform", "platform_position",
            "impression_device", "region",
            "hourly_stats_aggregated_by_advertiser_time_zone",
        }
        if breakdown not in allowed:
            raise ValueError("breakdown não suportado")
        fields = "campaign_id,date_start,spend,impressions,reach,clicks"
        # A Meta trata `actions` e `inline_link_clicks` como métricas de ação.
        # Elas geram action_type, incompatível com platform_position.
        if breakdown != "platform_position":
            fields += ",inline_link_clicks,actions"
        breakdown_params = (
            {"action_breakdowns": "[]"}
            if breakdown == "platform_position"
            else {}
        )
        return list(
            self._paginate(
                f"/{account_node(account_id)}/insights",
                fields=fields,
                level="campaign",
                breakdowns=breakdown,
                time_increment="1",
                time_range={"since": since, "until": until},
                **breakdown_params,
            )
        )

    def _paginate(self, path: str, **params: Any) -> Iterator[dict[str, Any]]:
        params["limit"] = 100
        payload = self._get(path, params=params)
        while True:
            yield from payload.get("data", [])
            next_url = payload.get("paging", {}).get("next")
            if not next_url:
                break
            payload = self._get(next_url, include_user_token=False)

    def _get(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        include_user_token: bool = True,
    ) -> dict[str, Any]:
        request_params = dict(params or {})
        if "time_range" in request_params:
            import json

            request_params["time_range"] = json.dumps(request_params["time_range"])
        if include_user_token:
            request_params["access_token"] = self.access_token
        try:
            # `None` preserva os query params já presentes na URL de paginação.
            response = self.http.get(path, params=request_params or None)
        except httpx.HTTPError as exc:
            status_code = getattr(getattr(exc, "response", None), "status_code", None)
            raise MetaGraphError("Falha ao consultar a Meta Graph API.", status_code=status_code) from exc

        try:
            payload = response.json()
        except ValueError as exc:
            raise MetaGraphError(
                "A Meta Graph API retornou uma resposta inválida.",
                status_code=response.status_code,
            ) from exc

        if isinstance(payload, dict) and "error" in payload:
            error = payload["error"]
            raise MetaGraphError(
                error.get("message") or "Falha ao consultar a Meta Graph API.",
                code=error.get("code"),
                status_code=response.status_code,
            )
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise MetaGraphError(
                "Falha ao consultar a Meta Graph API.",
                status_code=response.status_code,
            ) from exc
        return payload


def account_node(account_id: str) -> str:
    return account_id if account_id.startswith("act_") else f"act_{account_id}"
