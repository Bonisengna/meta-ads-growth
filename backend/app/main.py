from fastapi import FastAPI

from app.api.health import router as health_router
from app.config.settings import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    description="API backend do DescompliADS para métricas, análises e melhorias de campanhas Meta Ads.",
)

# Health disponível na raiz e também sob o prefixo versionado da API.
app.include_router(health_router)
app.include_router(health_router, prefix=settings.api_v1_prefix)


@app.get("/", tags=["Raiz"], summary="Identifica a API")
def root() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs",
    }
