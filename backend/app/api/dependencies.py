from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase import Client, create_client

from app.config.settings import get_settings
from app.database.supabase import SupabaseNotConfiguredError, get_supabase_client


bearer_scheme = HTTPBearer(auto_error=False)


def authenticated_supabase_client_dependency(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> Client:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise unauthorized()
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_publishable_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Autenticação Supabase ainda não configurada no backend.",
        )
    client = create_client(settings.supabase_url, settings.supabase_publishable_key)
    try:
        response = client.auth.get_user(credentials.credentials)
        if response is None or response.user is None:
            raise unauthorized()
    except HTTPException:
        raise
    except Exception as exc:
        raise unauthorized() from exc
    client.postgrest.auth(credentials.credentials)
    return client


def unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token de acesso ausente, inválido ou expirado.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def service_supabase_client_dependency() -> Client:
    try:
        return get_supabase_client()
    except SupabaseNotConfiguredError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase ainda não configurado para este ambiente.",
        ) from exc


supabase_client_dependency = authenticated_supabase_client_dependency
SupabaseClient = Annotated[Client, Depends(supabase_client_dependency)]
AuthenticatedClient = Annotated[Client, Depends(authenticated_supabase_client_dependency)]
