import argparse
import json
import sys
from datetime import date
from pathlib import Path
from uuid import UUID

# Permite executar `python scripts/smoke_meta.py` a partir de backend/.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config.settings import get_settings
from app.database.supabase import get_supabase_client
from app.services.meta_graph_client import MetaGraphClient, MetaGraphError
from app.services.meta_sync_service import MetaSyncService


def main() -> int:
    parser = argparse.ArgumentParser(description="Valida e sincroniza a Meta Graph API.")
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--validate", action="store_true")
    action.add_argument("--list-accounts", action="store_true")
    action.add_argument("--sync-account", metavar="ACCOUNT_ID")
    action.add_argument("--metrics", metavar="ACCOUNT_ID")
    parser.add_argument("--client-id", type=UUID)
    parser.add_argument("--date", type=date.fromisoformat)
    parser.add_argument("--from-date", dest="date_from", type=date.fromisoformat)
    parser.add_argument("--to-date", dest="date_to", type=date.fromisoformat)
    args = parser.parse_args()
    settings = get_settings()

    if not settings.meta_configured:
        parser.error("META_ACCESS_TOKEN não configurado no .env.")
    assert settings.meta_access_token is not None

    try:
        with MetaGraphClient(
            settings.meta_access_token.get_secret_value(),
            version=settings.meta_graph_version,
            base_url=settings.meta_graph_base_url,
            timeout=settings.meta_request_timeout_seconds,
        ) as meta:
            if args.validate:
                if not settings.meta_debug_configured:
                    parser.error("META_APP_ID e META_APP_SECRET são necessários para validar.")
                assert settings.meta_app_id and settings.meta_app_secret
                result = meta.validate_token(
                    settings.meta_app_id, settings.meta_app_secret.get_secret_value()
                )
                safe = {
                    "is_valid": result.get("is_valid", False),
                    "app_id": result.get("app_id"),
                    "type": result.get("type"),
                    "expires_at": result.get("expires_at"),
                    "scopes": result.get("scopes", []),
                }
            elif args.list_accounts:
                safe = [
                    {
                        "id": row.get("id"),
                        "account_id": row.get("account_id"),
                        "name": row.get("name"),
                        "currency": row.get("currency"),
                        "timezone_name": row.get("timezone_name"),
                        "account_status": row.get("account_status"),
                    }
                    for row in meta.list_ad_accounts()
                ]
            elif args.sync_account:
                if not args.client_id:
                    parser.error("--client-id é obrigatório com --sync-account.")
                safe = MetaSyncService(get_supabase_client(), meta).sync_account(
                    args.client_id, args.sync_account
                )
            else:
                if args.date and (args.date_from or args.date_to):
                    parser.error("Use --date ou --from-date/--to-date, não ambos.")
                if (args.date_from is None) != (args.date_to is None):
                    parser.error("--from-date e --to-date devem ser informados juntos.")
                date_from = args.date_from or args.date or date.today()
                date_to = args.date_to or date_from
                if date_from > date_to:
                    parser.error("--from-date não pode ser posterior a --to-date.")
                safe = MetaSyncService(get_supabase_client(), meta).sync_daily_metrics(
                    args.metrics, date_from, date_to
                )
        print(json.dumps(safe, indent=2, ensure_ascii=False, default=str))
        return 0
    except MetaGraphError as exc:
        print(
            json.dumps(
                {"status": "error", "message": str(exc), "meta_code": exc.code},
                ensure_ascii=False,
            )
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
