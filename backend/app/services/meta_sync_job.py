from typing import Any

from app.config.settings import Settings, get_settings
from app.database.supabase import get_supabase_client
from app.services.meta_graph_client import MetaGraphClient
from app.services.meta_sync_runner import MetaSyncRunner


def run_meta_sync(
    lookback_days: int | None = None,
    *,
    settings: Settings | None = None,
) -> dict[str, Any]:
    """Executa uma coleta completa usando somente configuração de servidor."""

    current = settings or get_settings()
    if not current.meta_configured:
        raise RuntimeError("META_ACCESS_TOKEN não configurado no ambiente.")
    assert current.meta_access_token is not None

    days = current.meta_sync_lookback_days if lookback_days is None else lookback_days
    with MetaGraphClient(
        current.meta_access_token.get_secret_value(),
        version=current.meta_graph_version,
        base_url=current.meta_graph_base_url,
        timeout=current.meta_request_timeout_seconds,
    ) as meta:
        return MetaSyncRunner(
            get_supabase_client(),
            meta,
            max_attempts=current.meta_sync_max_attempts,
            retry_delay_seconds=current.meta_sync_retry_delay_seconds,
            lock_minutes=current.meta_sync_lock_minutes,
        ).run(days)
