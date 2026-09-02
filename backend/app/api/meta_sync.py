from fastapi import APIRouter, Depends, Query, status
from supabase import Client

from app.api.dependencies import SupabaseClient, service_supabase_client_dependency
from app.models.meta_sync import SyncRecoveryCreate, SyncRequestCreate, SyncRequestRead, SyncRunRead
from app.services.meta_sync_control_service import MetaSyncControlService


router = APIRouter(prefix="/meta-sync", tags=["Sincronização Meta"])


@router.post("/requests", response_model=SyncRequestRead, status_code=status.HTTP_202_ACCEPTED)
def request_sync(
    payload: SyncRequestCreate,
    user_client: SupabaseClient,
    service_client: Client = Depends(service_supabase_client_dependency),
) -> dict[str, object]:
    return MetaSyncControlService(user_client, service_client).create_request(
        payload.client_id, payload.lookback_days
    )


@router.post("/recover", response_model=SyncRequestRead, status_code=status.HTTP_202_ACCEPTED)
def recover_sync(
    payload: SyncRecoveryCreate,
    user_client: SupabaseClient,
    service_client: Client = Depends(service_supabase_client_dependency),
) -> dict[str, object]:
    return MetaSyncControlService(user_client, service_client).recover(payload.run_id, payload.client_id)


@router.get("/requests", response_model=list[SyncRequestRead])
def list_sync_requests(
    user_client: SupabaseClient,
    service_client: Client = Depends(service_supabase_client_dependency),
    limit: int = Query(default=10, ge=1, le=50),
) -> list[dict[str, object]]:
    return MetaSyncControlService(user_client, service_client).list_requests(limit)


@router.get("/runs", response_model=list[SyncRunRead])
def list_sync_runs(
    user_client: SupabaseClient,
    service_client: Client = Depends(service_supabase_client_dependency),
    limit: int = Query(default=10, ge=1, le=50),
) -> list[dict[str, object]]:
    return MetaSyncControlService(user_client, service_client).list_runs(limit)
