from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações do backend carregadas do ambiente ou arquivo .env."""

    app_name: str = "DescompliADS API"
    app_version: str = "0.1.0"
    environment: str = "development"
    debug: bool = True
    api_v1_prefix: str = "/api/v1"
    timezone: str = "America/Sao_Paulo"

    # Supabase — valores reais devem existir apenas no ambiente/.env.
    supabase_url: str | None = None
    supabase_secret_key: SecretStr | None = None
    supabase_health_table: str = "app_health"

    # Meta Graph API — segredos existem somente no ambiente/.env.
    meta_graph_base_url: str = "https://graph.facebook.com"
    meta_graph_version: str = "v25.0"
    meta_access_token: SecretStr | None = None
    meta_app_id: str | None = None
    meta_app_secret: SecretStr | None = None
    meta_request_timeout_seconds: float = 30.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def supabase_configured(self) -> bool:
        """Informa se URL e chave de servidor foram fornecidas."""

        return bool(self.supabase_url and self.supabase_secret_key)

    @property
    def meta_configured(self) -> bool:
        return bool(self.meta_access_token)

    @property
    def meta_debug_configured(self) -> bool:
        return bool(self.meta_access_token and self.meta_app_id and self.meta_app_secret)


@lru_cache
def get_settings() -> Settings:
    """Retorna uma instância única das configurações durante o processo."""

    return Settings()
