from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator


class MetaIntegrationWrite(BaseModel):
    client_id: UUID
    connection_name: str = Field(min_length=2, max_length=120)
    ad_account_id: str = Field(min_length=5, max_length=40)
    business_id: str | None = Field(None, max_length=40)
    access_token: SecretStr


class SystemCredentialsWrite(BaseModel):
    meta_app_id: str | None = Field(None, max_length=80)
    meta_app_secret: SecretStr | None = None
    system_user_id: str | None = Field(None, max_length=80)
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


BusinessModel = Literal["B2B", "B2C", "B2B2C", "LOCAL_SERVICES", "OTHER"]
OnboardingStatus = Literal["NEW", "SETUP", "ACTIVE", "PAUSED"]
TaxIdType = Literal["CNPJ", "CPF", "OTHER"]


class ClientProfileBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=2, max_length=160)
    legal_name: str | None = Field(None, max_length=200)
    tax_id_type: TaxIdType = "CNPJ"
    tax_id: str | None = Field(None, max_length=30)
    segment: str = Field(min_length=2, max_length=120)
    niche: str = Field(min_length=2, max_length=160)
    business_model: BusinessModel = "B2C"
    primary_audience: str | None = Field(None, max_length=500)
    website: str | None = Field(None, max_length=300)
    contact_name: str | None = Field(None, max_length=160)
    contact_email: str | None = Field(None, max_length=254)
    contact_phone: str | None = Field(None, max_length=40)
    city: str | None = Field(None, max_length=120)
    state: str | None = Field(None, max_length=80)
    country_code: str = Field("BR", pattern=r"^[A-Z]{2}$")
    timezone: str = Field("America/Sao_Paulo", min_length=3, max_length=80)
    currency: str = Field("BRL", pattern=r"^[A-Z]{3}$")
    primary_goal: str | None = Field(None, max_length=300)
    monthly_media_budget: Decimal | None = Field(None, ge=0, max_digits=14, decimal_places=2)
    onboarding_status: OnboardingStatus = "NEW"
    notes: str | None = Field(None, max_length=3000)


class ClientCreate(ClientProfileBase):
    pass


class ClientUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str | None = Field(None, min_length=2, max_length=160)
    legal_name: str | None = Field(None, max_length=200)
    tax_id_type: TaxIdType | None = None
    tax_id: str | None = Field(None, max_length=30)
    segment: str | None = Field(None, min_length=2, max_length=120)
    niche: str | None = Field(None, min_length=2, max_length=160)
    business_model: BusinessModel | None = None
    primary_audience: str | None = Field(None, max_length=500)
    website: str | None = Field(None, max_length=300)
    contact_name: str | None = Field(None, max_length=160)
    contact_email: str | None = Field(None, max_length=254)
    contact_phone: str | None = Field(None, max_length=40)
    city: str | None = Field(None, max_length=120)
    state: str | None = Field(None, max_length=80)
    country_code: str | None = Field(None, pattern=r"^[A-Z]{2}$")
    timezone: str | None = Field(None, min_length=3, max_length=80)
    currency: str | None = Field(None, pattern=r"^[A-Z]{3}$")
    primary_goal: str | None = Field(None, max_length=300)
    monthly_media_budget: Decimal | None = Field(None, ge=0, max_digits=14, decimal_places=2)
    onboarding_status: OnboardingStatus | None = None
    status: Literal["ACTIVE", "ARCHIVED"] | None = None
    notes: str | None = Field(None, max_length=3000)

    @field_validator(
        "name", "tax_id_type", "segment", "niche", "business_model", "country_code",
        "timezone", "currency", "onboarding_status", "status",
    )
    @classmethod
    def required_fields_cannot_be_null(cls, value: object) -> object:
        if value is None:
            raise ValueError("o campo não pode ser nulo quando informado")
        return value


class ManagedClientRead(ClientProfileBase):
    id: UUID
    slug: str
    status: Literal["ACTIVE", "ARCHIVED"]
    can_manage: bool
    created_at: datetime
    updated_at: datetime
