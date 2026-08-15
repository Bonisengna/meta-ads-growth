from functools import lru_cache

from supabase import Client, create_client

from app.config.settings import get_settings


class SupabaseNotConfiguredError(RuntimeError):
    """Erro lançado quando o backend ainda não recebeu as credenciais do Supabase."""


@lru_cache
def get_supabase_client() -> Client:
    """Cria e reutiliza o cliente Supabase usado pelo backend.

    A chave de servidor é lida exclusivamente das variáveis de ambiente/.env
    e nunca deve ser gravada no repositório.
    """

    settings = get_settings()

    if not settings.supabase_configured:
        raise SupabaseNotConfiguredError(
            "SUPABASE_URL e SUPABASE_SECRET_KEY ainda não foram configurados."
        )

    assert settings.supabase_url is not None
    assert settings.supabase_secret_key is not None

    return create_client(
        settings.supabase_url,
        settings.supabase_secret_key.get_secret_value(),
    )


def clear_supabase_client_cache() -> None:
    """Limpa o cache do cliente, útil em testes ou troca de configuração."""

    get_supabase_client.cache_clear()
