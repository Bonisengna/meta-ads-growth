from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.entities import router as entities_router
from app.api.health import router as health_router
from app.api.settings import router as settings_router
from app.config.settings import get_settings
from app.middleware.rate_limit import RateLimitMiddleware

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    description="API backend do DescompliADS para métricas, análises e melhorias de campanhas Meta Ads.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)
app.add_middleware(
    RateLimitMiddleware,
    requests=settings.rate_limit_requests,
    window_seconds=settings.rate_limit_window_seconds,
)

# Health disponível na raiz e também sob o prefixo versionado da API.
app.include_router(health_router)
app.include_router(health_router, prefix=settings.api_v1_prefix)
app.include_router(entities_router, prefix=settings.api_v1_prefix)
app.include_router(settings_router, prefix=settings.api_v1_prefix)


@app.get("/", tags=["Raiz"], summary="Identifica a API")
def root() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs",
    }
