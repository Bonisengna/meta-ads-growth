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


@lru_cache
def get_settings() -> Settings:
    """Retorna uma instância única das configurações durante o processo."""

    return Settings()
