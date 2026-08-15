-- Fase 3 — métricas diárias por nível da hierarquia Meta Ads.
-- A granularidade diária permite montar períodos de 7, 14, 30 dias ou personalizados
-- sem duplicar agregados no banco.

create table public.campaign_metrics (
    id uuid primary key default gen_random_uuid(),
    campaign_id uuid not null references public.campaigns(id) on delete restrict,
    metric_date date not null,
    spend numeric(14,2) not null default 0,
    impressions bigint not null default 0,
    reach bigint not null default 0,
    clicks bigint not null default 0,
    link_clicks bigint not null default 0,
    ctr numeric(12,6),
    cpc numeric(14,6),
    cpm numeric(14,6),
    frequency numeric(12,6),
    leads bigint not null default 0,
    cpl numeric(14,6),
    conversations bigint not null default 0,
    cost_per_conversation numeric(14,6),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (campaign_id, metric_date)
);

create table public.adset_metrics (
    id uuid primary key default gen_random_uuid(),
    adset_id uuid not null references public.adsets(id) on delete restrict,
    metric_date date not null,
    spend numeric(14,2) not null default 0,
    impressions bigint not null default 0,
    reach bigint not null default 0,
    clicks bigint not null default 0,
    link_clicks bigint not null default 0,
    ctr numeric(12,6),
    cpc numeric(14,6),
    cpm numeric(14,6),
    frequency numeric(12,6),
    leads bigint not null default 0,
    cpl numeric(14,6),
    conversations bigint not null default 0,
    cost_per_conversation numeric(14,6),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (adset_id, metric_date)
);

create table public.ad_metrics (
    id uuid primary key default gen_random_uuid(),
    ad_id uuid not null references public.ads(id) on delete restrict,
    metric_date date not null,
    spend numeric(14,2) not null default 0,
    impressions bigint not null default 0,
    reach bigint not null default 0,
    clicks bigint not null default 0,
    link_clicks bigint not null default 0,
    ctr numeric(12,6),
    cpc numeric(14,6),
    cpm numeric(14,6),
    frequency numeric(12,6),
    leads bigint not null default 0,
    cpl numeric(14,6),
    conversations bigint not null default 0,
    cost_per_conversation numeric(14,6),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (ad_id, metric_date)
);

create index idx_campaign_metrics_date on public.campaign_metrics(metric_date);
create index idx_adset_metrics_date on public.adset_metrics(metric_date);
create index idx_ad_metrics_date on public.ad_metrics(metric_date);

alter table public.campaign_metrics enable row level security;
alter table public.adset_metrics enable row level security;
alter table public.ad_metrics enable row level security;

revoke all on table public.campaign_metrics, public.adset_metrics, public.ad_metrics from anon, authenticated;
grant select, insert, update, delete on table public.campaign_metrics, public.adset_metrics, public.ad_metrics to service_role;
