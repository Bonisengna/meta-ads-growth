-- Recortes analíticos da Meta mantidos separados dos totais para evitar dupla contagem.

create table public.breakdown_metrics (
    id uuid primary key default gen_random_uuid(),
    campaign_id uuid not null references public.campaigns(id) on delete cascade,
    metric_date date not null,
    dimension_type text not null,
    dimension_value text not null,
    spend numeric(14,2) not null default 0,
    impressions bigint not null default 0,
    reach bigint not null default 0,
    clicks bigint not null default 0,
    link_clicks bigint not null default 0,
    leads integer not null default 0,
    conversations integer not null default 0,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint breakdown_metrics_dimension_type check (
        dimension_type in ('AGE','GENDER','PLATFORM','PLACEMENT','DEVICE','REGION','HOUR')
    ),
    constraint breakdown_metrics_unique unique (
        campaign_id, metric_date, dimension_type, dimension_value
    )
);

create index breakdown_metrics_campaign_date
    on public.breakdown_metrics(campaign_id, metric_date);
create index breakdown_metrics_dimension_date
    on public.breakdown_metrics(dimension_type, metric_date);

alter table public.breakdown_metrics enable row level security;
revoke all on table public.breakdown_metrics from anon, authenticated;
grant select on table public.breakdown_metrics to authenticated;
grant select, insert, update, delete on table public.breakdown_metrics to service_role;

create policy "users read authorized breakdown metrics"
on public.breakdown_metrics for select to authenticated
using (
    exists (
        select 1
        from public.campaigns campaign
        join public.meta_accounts account on account.id = campaign.meta_account_id
        join public.user_client_access access on access.client_id = account.client_id
        where campaign.id = breakdown_metrics.campaign_id
          and access.user_id = (select auth.uid())
          and access.active
    )
);
