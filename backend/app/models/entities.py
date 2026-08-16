from datetime import datetime
from decimal import Decimal
from typing import Generic, Literal, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer


EntityStatus = Literal["ACTIVE", "ARCHIVED"]
T = TypeVar("T")


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="ignore")


class ClientRead(ApiModel):
    id: UUID
    name: str
    slug: str
    status: EntityStatus
    created_at: datetime
    updated_at: datetime


class MetaAccountRead(ApiModel):
    id: UUID
    client_id: UUID
    meta_account_id: str
    name: str
    currency: str | None = None
    timezone: str | None = None
    status: EntityStatus
    last_synced_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class CampaignRead(ApiModel):
    id: UUID
    meta_account_id: UUID
    meta_campaign_id: str
    name: str
    objective: str | None = None
    status: EntityStatus
    meta_created_at: datetime | None = None
    meta_updated_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class Page(ApiModel, Generic[T]):
    items: list[T]
    page: int
    page_size: int
    total: int
    pages: int


class DashboardMetrics(ApiModel):
    spend: Decimal = Field(Decimal("0"), ge=0, max_digits=14, decimal_places=2, examples=[0.0])
    leads: int = 0
    cpl: Decimal | None = Field(None, ge=0, max_digits=14, decimal_places=6, examples=[12.5])

    @field_serializer("spend", "cpl", when_used="json")
    def serialize_money(self, value: Decimal | None) -> float | None:
        return float(value) if value is not None else None


class DashboardRead(ApiModel):
    clients: int
    meta_accounts: int
    campaigns: int
    adsets: int
    ads: int
    metrics: DashboardMetrics
