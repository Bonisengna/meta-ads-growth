from datetime import date, datetime
from decimal import Decimal
from typing import Generic, Literal, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer


EntityStatus = Literal["ACTIVE", "PAUSED", "ARCHIVED"]
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
    last_entities_synced_at: datetime | None = None
    last_metrics_synced_at: datetime | None = None
    last_successful_sync_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class CampaignRead(ApiModel):
    id: UUID
    meta_account_id: UUID
    meta_campaign_id: str
    name: str
    objective: str | None = None
    buying_type: str | None = None
    daily_budget: Decimal | None = None
    lifetime_budget: Decimal | None = None
    budget_remaining: Decimal | None = None
    start_time: datetime | None = None
    stop_time: datetime | None = None
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
    budget_remaining: Decimal | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
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
    creative_name: str | None = None
    creative_type: str | None = None
    thumbnail_url: str | None = None
    image_url: str | None = None
    video_id: str | None = None
    video_duration_seconds: Decimal | None = None
    primary_text: str | None = None
    headline: str | None = None
    call_to_action_type: str | None = None
    destination_url: str | None = None
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
    reach: int | None = None
    clicks: int = 0
    link_clicks: int = 0
    leads: int = 0
    conversations: int = 0
    landing_page_views: int = 0
    video_views_3s: int = 0
    video_plays: int = 0
    video_p25: int = 0
    video_p50: int = 0
    video_p75: int = 0
    video_p95: int = 0
    thruplays: int = 0
    cpl: Decimal | None = Field(None, ge=0, max_digits=14, decimal_places=6, examples=[12.5])
    ctr: Decimal | None = Field(None, ge=0, max_digits=12, decimal_places=6)
    cpc: Decimal | None = Field(None, ge=0, max_digits=14, decimal_places=6)
    cpm: Decimal | None = Field(None, ge=0, max_digits=14, decimal_places=6)
    link_ctr: Decimal | None = Field(None, ge=0, max_digits=12, decimal_places=6)
    frequency: Decimal | None = Field(None, ge=0, max_digits=12, decimal_places=6)
    landing_page_view_rate: Decimal | None = None
    cost_per_landing_page_view: Decimal | None = None
    landing_page_conversion_rate: Decimal | None = None
    hook_rate: Decimal | None = None
    thruplay_rate: Decimal | None = None
    video_p25_rate: Decimal | None = None
    video_p50_rate: Decimal | None = None
    video_p75_rate: Decimal | None = None
    video_p95_rate: Decimal | None = None

    @field_serializer(
        "spend", "cpl", "ctr", "cpc", "cpm", "link_ctr", "frequency",
        "landing_page_view_rate", "cost_per_landing_page_view",
        "landing_page_conversion_rate", "hook_rate", "thruplay_rate",
        "video_p25_rate", "video_p50_rate", "video_p75_rate", "video_p95_rate",
        when_used="json",
    )
    def serialize_money(self, value: Decimal | None) -> float | None:
        return float(value) if value is not None else None


class DatePeriod(ApiModel):
    date_from: date
    date_to: date
    days: int


class MetricsComparison(ApiModel):
    spend: Decimal | None = None
    impressions: Decimal | None = None
    reach: Decimal | None = None
    clicks: Decimal | None = None
    link_clicks: Decimal | None = None
    leads: Decimal | None = None
    conversations: Decimal | None = None
    cpl: Decimal | None = None
    ctr: Decimal | None = None
    cpc: Decimal | None = None
    cpm: Decimal | None = None
    link_ctr: Decimal | None = None
    frequency: Decimal | None = None
    landing_page_views: Decimal | None = None
    video_views_3s: Decimal | None = None
    thruplays: Decimal | None = None
    landing_page_view_rate: Decimal | None = None
    cost_per_landing_page_view: Decimal | None = None
    landing_page_conversion_rate: Decimal | None = None
    hook_rate: Decimal | None = None
    thruplay_rate: Decimal | None = None

    @field_serializer("*", when_used="json")
    def serialize_percent(self, value: Decimal | None) -> float | None:
        return float(value) if value is not None else None


class InvestmentPacing(ApiModel):
    currency: str | None = None
    monthly_budget: Decimal | None = None
    spent: Decimal = Decimal("0")
    remaining: Decimal | None = None
    percent_consumed: Decimal | None = None
    projected_spend: Decimal | None = None
    projected_percent: Decimal | None = None
    expected_spend_to_date: Decimal | None = None
    variance_to_expected: Decimal | None = None
    elapsed_percent: Decimal
    days_elapsed: int
    days_in_month: int
    pace_status: Literal["NOT_CONFIGURED", "BELOW", "ON_TRACK", "ABOVE"]

    @field_serializer(
        "monthly_budget", "spent", "remaining", "percent_consumed",
        "projected_spend", "projected_percent", "expected_spend_to_date",
        "variance_to_expected", "elapsed_percent", when_used="json",
    )
    def serialize_decimal(self, value: Decimal | None) -> float | None:
        return float(value) if value is not None else None


class AdOperation(ApiModel):
    id: UUID
    adset_id: UUID
    name: str
    status: EntityStatus
    creative_type: str | None = None
    thumbnail_url: str | None = None
    image_url: str | None = None
    video_duration_seconds: Decimal | None = None
    primary_text: str | None = None
    headline: str | None = None
    call_to_action_type: str | None = None
    destination_url: str | None = None
    metrics: DashboardMetrics

    @field_serializer("video_duration_seconds", when_used="json")
    def serialize_duration(self, value: Decimal | None) -> float | None:
        return float(value) if value is not None else None


class AdsetOperation(ApiModel):
    id: UUID
    campaign_id: UUID
    name: str
    status: EntityStatus
    optimization_goal: str | None = None
    daily_budget: Decimal | None = None
    lifetime_budget: Decimal | None = None
    configured_budget: Decimal | None = None
    budget_type: Literal["DAILY_PERIOD", "LIFETIME"] | None = None
    budget_utilization: Decimal | None = None
    metrics: DashboardMetrics
    ads: list[AdOperation] = Field(default_factory=list)

    @field_serializer(
        "daily_budget", "lifetime_budget", "configured_budget",
        "budget_utilization", when_used="json",
    )
    def serialize_budget(self, value: Decimal | None) -> float | None:
        return float(value) if value is not None else None


class CampaignOperation(ApiModel):
    id: UUID
    meta_account_id: UUID
    name: str
    objective: str | None = None
    status: EntityStatus
    daily_budget: Decimal | None = None
    lifetime_budget: Decimal | None = None
    configured_budget: Decimal | None = None
    budget_type: Literal["DAILY_PERIOD", "LIFETIME"] | None = None
    budget_utilization: Decimal | None = None
    has_delivery: bool
    metrics: DashboardMetrics
    adsets: list[AdsetOperation] = Field(default_factory=list)

    @field_serializer(
        "daily_budget", "lifetime_budget", "configured_budget",
        "budget_utilization", when_used="json",
    )
    def serialize_budget(self, value: Decimal | None) -> float | None:
        return float(value) if value is not None else None


MetricQuality = Literal["AVAILABLE", "ESTIMATED", "UNAVAILABLE", "NOT_APPLICABLE"]


class MetricDefinition(ApiModel):
    key: str
    label: str
    source: str
    formula: str
    aggregation: str
    quality: MetricQuality
    note: str | None = None


class DataQualityIssue(ApiModel):
    code: str
    severity: Literal["INFO", "WARNING", "CRITICAL"]
    title: str
    message: str


class DataConfidence(ApiModel):
    status: Literal["TRUSTED", "ATTENTION", "NO_DATA"]
    source: Literal["META_ADS_INSIGHTS"] = "META_ADS_INSIGHTS"
    currency: str | None = None
    timezone: str | None = None
    attribution_model: Literal["ACCOUNT_SETTING"] = "ACCOUNT_SETTING"
    action_report_time: Literal["IMPRESSION"] = "IMPRESSION"
    includes_today: bool
    current_day_is_partial: bool
    archived_history_included: bool = True
    metrics_through: date | None = None
    last_entities_synced_at: datetime | None = None
    last_metrics_synced_at: datetime | None = None
    last_successful_sync_at: datetime | None = None
    metric_catalog: list[MetricDefinition] = Field(default_factory=list)
    issues: list[DataQualityIssue] = Field(default_factory=list)


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
    investment_pacing: InvestmentPacing
    campaign_operations: list[CampaignOperation]
    daily_series: list["DailyMetricPoint"]
    campaign_ranking: list["CampaignPerformance"]
    adset_ranking: list["EntityPerformance"]
    ad_ranking: list["EntityPerformance"]
    insights: list["PerformanceInsight"]
    recommendations: list["RecommendationRead"]
    breakdowns: "BreakdownAnalytics"
    data_confidence: DataConfidence


class BreakdownPoint(ApiModel):
    value: str
    spend: Decimal
    impressions: int
    reach: int | None = None
    link_clicks: int
    leads: int
    conversations: int
    cpa: Decimal | None = None
    conversion_rate: Decimal | None = None
    ctr: Decimal | None = None
    cpm: Decimal | None = None

    @field_serializer("spend", "cpa", "conversion_rate", "ctr", "cpm", when_used="json")
    def serialize_decimal(self, value: Decimal | None) -> float | None:
        return float(value) if value is not None else None


class BreakdownAnalytics(ApiModel):
    age: list[BreakdownPoint] = Field(default_factory=list)
    gender: list[BreakdownPoint] = Field(default_factory=list)
    platform: list[BreakdownPoint] = Field(default_factory=list)
    placement: list[BreakdownPoint] = Field(default_factory=list)
    device: list[BreakdownPoint] = Field(default_factory=list)
    region: list[BreakdownPoint] = Field(default_factory=list)
    hour: list[BreakdownPoint] = Field(default_factory=list)


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


class EntityPerformance(ApiModel):
    entity_type: Literal["ADSET", "AD"]
    entity_id: UUID
    name: str
    status: EntityStatus
    spend: Decimal
    impressions: int
    clicks: int
    leads: int
    conversations: int
    ctr: Decimal | None = None
    cpc: Decimal | None = None
    cost_per_conversation: Decimal | None = None

    @field_serializer("spend", "ctr", "cpc", "cost_per_conversation", when_used="json")
    def serialize_decimal(self, value: Decimal | None) -> float | None:
        return float(value) if value is not None else None


class RecommendationRead(ApiModel):
    key: str
    entity_type: Literal["ADSET", "AD"]
    entity_id: UUID
    entity_name: str
    rule_code: str
    priority: Literal["HIGH", "MEDIUM", "LOW"]
    title: str
    explanation: str
    evidence: str
    expected_impact: str
    status: Literal["PENDING", "ACCEPTED", "REJECTED"] = "PENDING"


class RecommendationDecision(ApiModel):
    key: str
    entity_type: Literal["ADSET", "AD"]
    entity_id: UUID
    entity_name: str = Field(min_length=1, max_length=255)
    rule_code: str = Field(min_length=1, max_length=80)
    priority: Literal["HIGH", "MEDIUM", "LOW"]
    title: str = Field(min_length=1, max_length=255)
    explanation: str = Field(min_length=1, max_length=2000)
    evidence: str = Field(min_length=1, max_length=1000)
    expected_impact: str = Field(min_length=1, max_length=1000)
    status: Literal["ACCEPTED", "REJECTED"]
    note: str | None = Field(None, max_length=1000)
    period_from: date
    period_to: date


class RecommendationDecisionRead(ApiModel):
    id: UUID
    key: str
    status: Literal["ACCEPTED", "REJECTED"]
    decided_at: datetime


class ImprovementRead(ApiModel):
    id: UUID
    recommendation_id: UUID | None = None
    campaign_id: UUID | None = None
    adset_id: UUID | None = None
    ad_id: UUID | None = None
    title: str
    hypothesis: str | None = None
    status: str
    metric_name: str | None = None
    before_value: Decimal | None = None
    after_value: Decimal | None = None
    result: str | None = None
    conclusion: str | None = None
    created_at: datetime


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
    landing_page_views: int = 0
    video_views_3s: int = 0
    video_plays: int = 0
    video_p25: int = 0
    video_p50: int = 0
    video_p75: int = 0
    video_p95: int = 0
    thruplays: int = 0
    created_at: datetime
    updated_at: datetime


class CampaignMetricRead(BaseMetricRead):
    campaign_id: UUID


class AdsetMetricRead(BaseMetricRead):
    adset_id: UUID


class AdMetricRead(BaseMetricRead):
    ad_id: UUID
