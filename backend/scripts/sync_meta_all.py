import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config.settings import get_settings
from app.database.supabase import get_supabase_client
from app.services.meta_graph_client import MetaGraphClient
from app.services.meta_sync_runner import MetaSyncRunner, SyncAlreadyRunningError, safe_error


def main() -> int:
    settings = get_settings()
    parser = argparse.ArgumentParser(
        description="Sincroniza entidades e métricas de todas as contas Meta ativas."
    )
    parser.add_argument("--lookback-days", type=int, default=settings.meta_sync_lookback_days)
    args = parser.parse_args()
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
            result = MetaSyncRunner(
                get_supabase_client(),
                meta,
                max_attempts=settings.meta_sync_max_attempts,
                retry_delay_seconds=settings.meta_sync_retry_delay_seconds,
                lock_minutes=settings.meta_sync_lock_minutes,
            ).run(args.lookback_days)
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
        return 0 if result["status"] == "SUCCESS" else 2
    except SyncAlreadyRunningError as exc:
        print(json.dumps({"status": "SKIPPED", "message": str(exc)}, ensure_ascii=False))
        return 3
    except Exception as exc:
        print(json.dumps({"status": "FAILED", "message": safe_error(exc)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
