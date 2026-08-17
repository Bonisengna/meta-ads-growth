from datetime import date, datetime
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


class AdsetRead(ApiModel):
    id: UUID
    campaign_id: UUID
    meta_adset_id: str
    name: str
    status: EntityStatus
    optimization_goal: str | None = None
    billing_event: str | None = None
    daily_budget: Decimal | None = None
    lifetime_budget: Decimal | None = None
    meta_created_at: datetime | None = None
    meta_updated_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class AdRead(ApiModel):
    id: UUID
    adset_id: UUID
    meta_ad_id: str
    name: str
    status: EntityStatus
    creative_id: str | None = None
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
    impressions: int = 0
    clicks: int = 0
    leads: int = 0
    conversations: int = 0
    cpl: Decimal | None = Field(None, ge=0, max_digits=14, decimal_places=6, examples=[12.5])
    ctr: Decimal | None = Field(None, ge=0, max_digits=12, decimal_places=6)
    cpc: Decimal | None = Field(None, ge=0, max_digits=14, decimal_places=6)
    cpm: Decimal | None = Field(None, ge=0, max_digits=14, decimal_places=6)

    @field_serializer("spend", "cpl", "ctr", "cpc", "cpm", when_used="json")
    def serialize_money(self, value: Decimal | None) -> float | None:
        return float(value) if value is not None else None


class DatePeriod(ApiModel):
    date_from: date
    date_to: date
    days: int


class MetricsComparison(ApiModel):
    spend: Decimal | None = None
    impressions: Decimal | None = None
    clicks: Decimal | None = None
    leads: Decimal | None = None
    conversations: Decimal | None = None
    cpl: Decimal | None = None
    ctr: Decimal | None = None
    cpc: Decimal | None = None
    cpm: Decimal | None = None

    @field_serializer("*", when_used="json")
    def serialize_percent(self, value: Decimal | None) -> float | None:
        return float(value) if value is not None else None


class DashboardRead(ApiModel):
    clients: int
    meta_accounts: int
    campaigns: int
    adsets: int
    ads: int
    period: DatePeriod
    previous_period: DatePeriod
    metrics: DashboardMetrics
    previous_metrics: DashboardMetrics
    change_percent: MetricsComparison
    daily_series: list["DailyMetricPoint"]
    campaign_ranking: list["CampaignPerformance"]
    insights: list["PerformanceInsight"]


class DailyMetricPoint(ApiModel):
    metric_date: date
    spend: Decimal
    impressions: int
    clicks: int
    leads: int
    conversations: int

    @field_serializer("spend", when_used="json")
    def serialize_spend(self, value: Decimal) -> float:
        return float(value)


class CampaignPerformance(ApiModel):
    campaign_id: UUID
    name: str
    status: EntityStatus
    spend: Decimal
    impressions: int
    clicks: int
    leads: int
    conversations: int
    cpl: Decimal | None = None
    ctr: Decimal | None = None
    cpc: Decimal | None = None
    cost_per_conversation: Decimal | None = None

    @field_serializer("spend", "cpl", "ctr", "cpc", "cost_per_conversation", when_used="json")
    def serialize_decimal(self, value: Decimal | None) -> float | None:
        return float(value) if value is not None else None


class PerformanceInsight(ApiModel):
    code: str
    severity: Literal["INFO", "WARNING", "OPPORTUNITY"]
    title: str
    message: str


class BaseMetricRead(ApiModel):
    id: UUID
    metric_date: date
    spend: Decimal
    impressions: int
    reach: int
    clicks: int
    link_clicks: int
    ctr: Decimal | None = None
    cpc: Decimal | None = None
    cpm: Decimal | None = None
    frequency: Decimal | None = None
    leads: int
    cpl: Decimal | None = None
    conversations: int
    cost_per_conversation: Decimal | None = None
    created_at: datetime
    updated_at: datetime


class CampaignMetricRead(BaseMetricRead):
    campaign_id: UUID


class AdsetMetricRead(BaseMetricRead):
    adset_id: UUID


class AdMetricRead(BaseMetricRead):
    ad_id: UUID
