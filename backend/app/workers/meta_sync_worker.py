import json
import re
import time
from datetime import UTC, datetime, time as clock_time, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.config.settings import get_settings
from app.database.supabase import get_supabase_client
from app.services.meta_sync_control_service import claim_next_request, finish_request
from app.services.meta_sync_job import run_meta_sync
from app.services.meta_sync_runner import SyncAlreadyRunningError, safe_error

POLL_SECONDS = 5.0

def parse_daily_time(value: str) -> clock_time:
    """Converte HH:MM em horário diário estrito."""

    if re.fullmatch(r"\d{2}:\d{2}", value) is None:
        raise ValueError("META_SYNC_DAILY_TIME deve usar o formato HH:MM")
    try:
        parsed = datetime.strptime(value, "%H:%M")
    except ValueError as exc:
        raise ValueError("META_SYNC_DAILY_TIME deve usar o formato HH:MM") from exc
    return parsed.time()


def resolve_timezone(name: str) -> ZoneInfo | timezone:
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError:
        if name == "America/Sao_Paulo":
            return timezone(timedelta(hours=-3), name)
        raise


def next_scheduled_run(now: datetime, daily_time: str, timezone_name: str) -> datetime:
    """Calcula a próxima execução e devolve o instante em UTC."""

    zone = resolve_timezone(timezone_name)
    local_now = now.astimezone(zone)
    target_time = parse_daily_time(daily_time)
    target = datetime.combine(local_now.date(), target_time, tzinfo=zone)
    if target <= local_now:
        target += timedelta(days=1)
    return target.astimezone(UTC)


def emit(event: str, **fields: Any) -> None:
    payload = {"event": event, "at": datetime.now(UTC).isoformat(), **fields}
    print(json.dumps(payload, ensure_ascii=False, default=str), flush=True)


def run_once() -> None:
    settings = get_settings()
    try:
        result = run_meta_sync(settings=settings)
        emit(
            "sync_finished",
            status=result["status"],
            run_id=result["run_id"],
            accounts_total=result["accounts_total"],
            accounts_success=result["accounts_success"],
            accounts_failed=result["accounts_failed"],
        )
    except SyncAlreadyRunningError as exc:
        emit("sync_skipped", status="SKIPPED", message=safe_error(exc))
    except Exception as exc:
        emit("sync_failed", status="FAILED", message=safe_error(exc))

def process_pending_requests() -> int:
    """Consome pedidos persistentes; devolve quantos foram concluídos."""

    client = get_supabase_client()
    processed = 0
    while request := claim_next_request(client):
        try:
            result = run_meta_sync(
                int(request["lookback_days"]),
                client_id=str(request["client_id"]),
                trigger_source="RECOVERY" if request.get("recovery_of") else "MANUAL",
                requested_by=str(request["requested_by"]) if request.get("requested_by") else None,
                recovery_of=str(request["recovery_of"]) if request.get("recovery_of") else None,
            )
            finish_request(client, str(request["id"]), result)
            processed += 1
            emit(
                "sync_request_finished",
                request_id=request["id"],
                run_id=result["run_id"],
                status=result["status"],
            )
        except SyncAlreadyRunningError:
            client.table("sync_requests").update(
                {"status": "PENDING", "started_at": None}
            ).eq("id", request["id"]).execute()
            break
        except Exception as exc:
            finish_request(client, str(request["id"]), None, exc)
            processed += 1
            emit("sync_request_failed", request_id=request["id"], message=safe_error(exc))
    return processed


def main() -> None:
    settings = get_settings()
    parse_daily_time(settings.meta_sync_daily_time)
    resolve_timezone(settings.timezone)
    emit(
        "worker_started",
        daily_time=settings.meta_sync_daily_time,
        timezone=settings.timezone,
        lookback_days=settings.meta_sync_lookback_days,
        run_on_start=settings.meta_sync_run_on_start,
    )

    if settings.meta_sync_run_on_start:
        run_once()

    scheduled = next_scheduled_run(
        datetime.now(UTC), settings.meta_sync_daily_time, settings.timezone
    )
    emit("sync_scheduled", scheduled_at=scheduled.isoformat())
    while True:
        now = datetime.now(UTC)
        try:
            process_pending_requests()
        except Exception as exc:
            emit("sync_queue_poll_failed", status="FAILED", message=safe_error(exc))
        if now >= scheduled:
            run_once()
            scheduled = next_scheduled_run(
                datetime.now(UTC), settings.meta_sync_daily_time, settings.timezone
            )
            emit("sync_scheduled", scheduled_at=scheduled.isoformat())
        time.sleep(min(POLL_SECONDS, max(1.0, (scheduled - datetime.now(UTC)).total_seconds())))


if __name__ == "__main__":
    main()
