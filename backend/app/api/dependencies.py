from typing import Annotated

from fastapi import Depends, HTTPException, status
from supabase import Client

from app.database.supabase import SupabaseNotConfiguredError, get_supabase_client


def supabase_client_dependency() -> Client:
    try:
        return get_supabase_client()
    except SupabaseNotConfiguredError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase ainda não configurado para este ambiente.",
        ) from exc


SupabaseClient = Annotated[Client, Depends(supabase_client_dependency)]
