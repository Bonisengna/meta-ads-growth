"""Compara os totais locais com a Meta sem alterar ou sincronizar dados."""

import argparse
import json
import sys
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from uuid import UUID

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config.settings import get_settings
from app.database.supabase import get_supabase_client
from app.services.entity_services import DashboardService
from app.services.meta_graph_client import MetaGraphClient, MetaGraphError
from app.services.meta_sync_service import metrics_payload

WINDOWS = (7, 30, 180, 360)
ADDITIVE_METRICS = (
    "spend", "impressions", "clicks", "link_clicks", "leads",
    "conversations", "landing_page_views",
)


def normalized(value: object, key: str) -> Decimal:
    if key == "spend":
        return Decimal(str(value or 0)).quantize(Decimal("0.01"))
    return Decimal(int(value or 0))


def compare_totals(
    local: dict[str, object], meta: dict[str, object]
) -> dict[str, object]:
    differences: dict[str, object] = {}
    matches = True
    for key in ADDITIVE_METRICS:
        local_value = normalized(local.get(key), key)
        meta_value = normalized(meta.get(key), key)
        difference = local_value - meta_value
        metric_matches = difference == 0
        matches = matches and metric_matches
        differences[key] = {
            "local": local_value,
            "meta": meta_value,
            "difference": difference,
            "matches": metric_matches,
        }
    return {"matches": matches, "metrics": differences}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Reconcilia 7, 30, 180 e 360 dias entre Supabase e Meta."
    )
    parser.add_argument("account_id", help="ID numérico da conta, com ou sem act_.")
    parser.add_argument(
        "--windows", default=",".join(map(str, WINDOWS)),
        help="Janelas separadas por vírgula. Padrão: 7,30,180,360.",
    )
    parser.add_argument("--date", type=date.fromisoformat, default=date.today())
    args = parser.parse_args()
    windows = tuple(int(value.strip()) for value in args.windows.split(",") if value.strip())
    if not windows or any(value not in WINDOWS for value in windows):
        parser.error("As janelas permitidas são 7, 30, 180 e 360 dias.")

    settings = get_settings()
    if not settings.meta_configured:
        parser.error("META_ACCESS_TOKEN não configurado no ambiente.")
    assert settings.meta_access_token is not None
    supabase = get_supabase_client()
    account_id = args.account_id.removeprefix("act_")
    account_rows = (
        supabase.table("meta_accounts")
        .select("id,name,currency,timezone")
        .eq("meta_account_id", account_id)
        .limit(1)
        .execute().data or []
    )
    if not account_rows:
        print(json.dumps({"status": "FAILED", "message": "Conta não encontrada no Supabase."}, ensure_ascii=False))
        return 1
    account = account_rows[0]
    results: list[dict[str, object]] = []
    try:
        with MetaGraphClient(
            settings.meta_access_token.get_secret_value(),
            version=settings.meta_graph_version,
            base_url=settings.meta_graph_base_url,
            timeout=settings.meta_request_timeout_seconds,
        ) as meta:
            for days in windows:
                date_from = args.date - timedelta(days=days - 1)
                local = DashboardService(supabase).get_dashboard(
                    days=days, date_from=date_from, date_to=args.date,
                    meta_account_id=UUID(str(account["id"])),
                )["metrics"]
                rows = meta.list_period_insights(
                    account_id, date_from.isoformat(), args.date.isoformat()
                )
                if rows:
                    meta_totals = metrics_payload(rows[0], "account_id", account_id) or {}
                    comparison = compare_totals(local, meta_totals)
                    status = "MATCH" if comparison["matches"] else "MISMATCH"
                else:
                    local_is_zero = all(normalized(local.get(key), key) == 0 for key in ADDITIVE_METRICS)
                    meta_totals = {}
                    comparison = {"matches": local_is_zero, "metrics": {}}
                    status = "MATCH_NO_DATA" if local_is_zero else "MISMATCH"
                results.append({
                    "days": days, "date_from": date_from, "date_to": args.date,
                    "status": status, **comparison,
                    "reference_non_additive": {
                        "reach": rows[0].get("reach") if rows else None,
                        "frequency": rows[0].get("frequency") if rows else None,
                        "note": "Referência direta da Meta; não é soma das linhas diárias.",
                    },
                })
    except MetaGraphError as exc:
        print(json.dumps({"status": "FAILED", "message": str(exc), "meta_code": exc.code}, ensure_ascii=False))
        return 1

    accepted = {"MATCH", "MATCH_NO_DATA"}
    overall = "MATCH" if all(item["status"] in accepted for item in results) else "ATTENTION"
    print(json.dumps({
        "status": overall, "account_id": account_id, "account_name": account["name"],
        "currency": account.get("currency"), "timezone": account.get("timezone"),
        "attribution": "ACCOUNT_SETTING", "action_report_time": "IMPRESSION",
        "results": results,
    }, indent=2, ensure_ascii=False, default=str))
    return 0 if overall == "MATCH" else 2


if __name__ == "__main__":
    raise SystemExit(main())
