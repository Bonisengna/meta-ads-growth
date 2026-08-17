import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config.settings import get_settings
from app.services.meta_sync_job import run_meta_sync
from app.services.meta_sync_runner import SyncAlreadyRunningError, safe_error


def main() -> int:
    settings = get_settings()
    parser = argparse.ArgumentParser(
        description="Sincroniza entidades e métricas de todas as contas Meta ativas."
    )
    parser.add_argument("--lookback-days", type=int, default=settings.meta_sync_lookback_days)
    args = parser.parse_args()
    if not settings.meta_configured:
        parser.error("META_ACCESS_TOKEN não configurado no .env.")
    try:
        result = run_meta_sync(args.lookback_days, settings=settings)
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
