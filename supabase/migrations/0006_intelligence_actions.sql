-- Fase 3 — camada de inteligência e acompanhamento do DescompliADS.
-- Cada análise/alerta deve apontar para exatamente uma entidade Meta:
-- campanha, conjunto ou anúncio.

create table public.ai_analyses (
    id uuid primary key default gen_random_uuid(),
    campaign_id uuid references public.campaigns(id) on delete restrict,
    adset_id uuid references public.adsets(id) on delete restrict,
    ad_id uuid references public.ads(id) on delete restrict,
    period_start date not null,
    period_end date not null,
    analysis_type text not null,
    problem text,
    possible_causes text,
    summary text not null,
    priority text not null default 'MEDIUM',
    rating numeric(4,2),
    model text,
    prompt_version text,
    created_at timestamptz not null default now(),
    constraint ai_analyses_one_entity check (num_nonnulls(campaign_id, adset_id, ad_id) = 1),
    constraint ai_analyses_period check (period_end >= period_start)
);

create table public.recommendations (
    id uuid primary key default gen_random_uuid(),
    analysis_id uuid not null references public.ai_analyses(id) on delete cascade,
    title text not null,
    description text not null,
    action_type text,
    priority text not null default 'MEDIUM',
    expected_impact text,
    status text not null default 'PENDING',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table public.improvements (
    id uuid primary key default gen_random_uuid(),
    recommendation_id uuid references public.recommendations(id) on delete set null,
    campaign_id uuid references public.campaigns(id) on delete restrict,
    adset_id uuid references public.adsets(id) on delete restrict,
    ad_id uuid references public.ads(id) on delete restrict,
    title text not null,
    hypothesis text,
    description text,
    status text not null default 'PENDING',
    metric_name text,
    before_value numeric(18,6),
    after_value numeric(18,6),
    started_at timestamptz,
    validation_due_at timestamptz,
    finished_at timestamptz,
    result text,
    conclusion text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint improvements_one_entity check (num_nonnulls(campaign_id, adset_id, ad_id) = 1)
);

create table public.alerts (
    id uuid primary key default gen_random_uuid(),
    campaign_id uuid references public.campaigns(id) on delete restrict,
    adset_id uuid references public.adsets(id) on delete restrict,
    ad_id uuid references public.ads(id) on delete restrict,
    alert_type text not null,
    severity text not null default 'WARNING',
    title text not null,
    message text not null,
    metric_name text,
    current_value numeric(18,6),
    threshold_value numeric(18,6),
    status text not null default 'OPEN',
    detected_at timestamptz not null default now(),
    resolved_at timestamptz,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint alerts_one_entity check (num_nonnulls(campaign_id, adset_id, ad_id) = 1)
);

create index idx_ai_analyses_campaign on public.ai_analyses(campaign_id) where campaign_id is not null;
create index idx_ai_analyses_adset on public.ai_analyses(adset_id) where adset_id is not null;
create index idx_ai_analyses_ad on public.ai_analyses(ad_id) where ad_id is not null;
create index idx_recommendations_analysis on public.recommendations(analysis_id);
create index idx_recommendations_status on public.recommendations(status);
create index idx_improvements_status on public.improvements(status);
create index idx_alerts_status on public.alerts(status);
create index idx_alerts_detected_at on public.alerts(detected_at);

alter table public.ai_analyses enable row level security;
alter table public.recommendations enable row level security;
alter table public.improvements enable row level security;
alter table public.alerts enable row level security;

revoke all on table public.ai_analyses, public.recommendations, public.improvements, public.alerts from anon, authenticated;
grant select, insert, update, delete on table public.ai_analyses, public.recommendations, public.improvements, public.alerts to service_role;
