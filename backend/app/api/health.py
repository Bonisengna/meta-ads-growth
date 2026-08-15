from fastapi import APIRouter

from app.config.settings import get_settings

router = APIRouter(tags=["Saúde"])


@router.get("/health", summary="Verifica a saúde da API")
def health_check() -> dict[str, str]:
    """Retorna um diagnóstico simples sem depender de serviços externos."""

    settings = get_settings()
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "timezone": settings.timezone,
    }
