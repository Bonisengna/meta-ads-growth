from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client

from app.api.dependencies import SupabaseClient, service_supabase_client_dependency
from app.models.settings import CredentialStatus, MetaIntegrationWrite, SettingsRead, SystemCredentialsWrite
from app.services.meta_graph_client import MetaGraphError
from app.services.settings_service import SettingsService


router = APIRouter(prefix="/settings", tags=["Ajustes"])


@router.get("", response_model=SettingsRead)
def read_settings(
    user_client: SupabaseClient,
    service_client: Client = Depends(service_supabase_client_dependency),
) -> dict[str, object]:
    return SettingsService(user_client, service_client).read()


@router.post("/meta", response_model=CredentialStatus)
def save_meta_integration(
    payload: MetaIntegrationWrite,
    user_client: SupabaseClient,
    service_client: Client = Depends(service_supabase_client_dependency),
) -> dict[str, object]:
    try:
        return SettingsService(user_client, service_client).save_meta(payload)
    except HTTPException:
        raise
    except MetaGraphError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Não foi possível validar o token na Meta. Confira token, conta e permissões.",
        ) from exc


@router.post("/system", response_model=list[CredentialStatus])
def save_system_credentials(
    payload: SystemCredentialsWrite,
    user_client: SupabaseClient,
    service_client: Client = Depends(service_supabase_client_dependency),
) -> list[dict[str, object]]:
    return SettingsService(user_client, service_client).save_system(payload)
