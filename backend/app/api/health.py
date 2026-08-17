from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from supabase import Client

from app.api.dependencies import authenticated_supabase_client_dependency
from app.config.settings import get_settings
from app.database.supabase import SupabaseNotConfiguredError, get_supabase_client
from app.services.supabase_service import SupabaseService
from app.services.meta_health_service import MetaHealthService

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
    _authenticated: Client = Depends(authenticated_supabase_client_dependency),
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


@router.get(
    "/health/meta",
    summary="Verifica a saúde da integração Meta",
    response_model=None,
)
def meta_health(
    _authenticated: Client = Depends(authenticated_supabase_client_dependency),
    client: Client = Depends(supabase_client_dependency),
) -> Any:
    """Readiness operacional baseada nas execuções e contas sincronizadas."""

    settings = get_settings()
    if not settings.meta_configured:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "UNCONFIGURED", "service": "meta"},
        )
    try:
        result = MetaHealthService(
            client, stale_hours=settings.meta_health_stale_hours
        ).check()
        if result["status"] != "HEALTHY":
            return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=result)
        return result
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "ERROR",
                "service": "meta",
                "message": "Não foi possível consultar a saúde da integração Meta.",
            },
        ) from exc
