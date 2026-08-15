from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client

from app.config.settings import get_settings
from app.database.supabase import SupabaseNotConfiguredError, get_supabase_client
from app.services.supabase_service import SupabaseService

router = APIRouter(tags=["Saúde"])


def supabase_client_dependency() -> Client:
    """Traduz ausência de configuração em HTTP 503 sem expor segredos."""

    try:
        return get_supabase_client()
    except SupabaseNotConfiguredError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "unconfigured",
                "service": "supabase",
                "message": "Supabase ainda não configurado para este ambiente.",
            },
        ) from exc


@router.get("/health", summary="Verifica a saúde da API")
def health_check() -> dict[str, str]:
    """Liveness: confirma que a API está executando sem depender do banco."""

    settings = get_settings()
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "timezone": settings.timezone,
    }


@router.get("/health/database", summary="Verifica a conexão com o Supabase")
def database_health(
    client: Client = Depends(supabase_client_dependency),
) -> dict[str, object]:
    """Readiness: valida uma leitura mínima na Data API do Supabase."""

    try:
        return SupabaseService(client).read_health()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "error",
                "service": "supabase",
                "message": "Não foi possível consultar o Supabase.",
            },
        ) from exc
