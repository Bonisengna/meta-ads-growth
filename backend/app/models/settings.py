from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, SecretStr


class MetaIntegrationWrite(BaseModel):
    client_id: UUID
    connection_name: str = Field(min_length=2, max_length=120)
    ad_account_id: str = Field(min_length=5, max_length=40)
    business_id: str | None = Field(None, max_length=40)
    access_token: SecretStr


class SystemCredentialsWrite(BaseModel):
    meta_app_id: str | None = Field(None, max_length=80)
    meta_app_secret: SecretStr | None = None
    graph_version: str = Field("v25.0", pattern=r"^v\d+\.\d+$")
    openai_api_key: SecretStr | None = None


class CredentialStatus(BaseModel):
    provider: Literal["META_CLIENT", "META_SYSTEM", "OPENAI"]
    configured: bool
    status: str | None = None
    connection_name: str | None = None
    client_id: UUID | None = None
    config: dict[str, object] = Field(default_factory=dict)
    last_validated_at: datetime | None = None
    updated_at: datetime | None = None


class SettingsRead(BaseModel):
    system_admin: bool
    credentials: list[CredentialStatus]
