-- Gate de confiabilidade operacional.
-- Mantém a coleta diária em 3 dias, mas permite backfill manual de até 360 dias.

alter table public.sync_runs
    drop constraint if exists sync_runs_lookback_days;

alter table public.sync_runs
    add constraint sync_runs_lookback_days
    check (lookback_days between 1 and 360);

alter table public.sync_runs
    add column if not exists accounts_partial integer not null default 0;

alter table public.sync_runs
    drop constraint if exists sync_runs_accounts_partial_nonnegative;

alter table public.sync_runs
    add constraint sync_runs_accounts_partial_nonnegative
    check (accounts_partial >= 0);

alter table public.meta_accounts
    add column if not exists last_entities_synced_at timestamptz,
    add column if not exists last_metrics_synced_at timestamptz,
    add column if not exists last_successful_sync_at timestamptz;

update public.meta_accounts
set last_entities_synced_at = coalesce(last_entities_synced_at, last_synced_at)
where last_entities_synced_at is null and last_synced_at is not null;

comment on column public.meta_accounts.last_entities_synced_at is
    'Última atualização bem-sucedida de conta, campanhas, conjuntos e anúncios.';
comment on column public.meta_accounts.last_metrics_synced_at is
    'Última atualização bem-sucedida das métricas essenciais.';
comment on column public.meta_accounts.last_successful_sync_at is
    'Última execução integral com entidades, métricas e detalhamentos.';

comment on column public.campaign_metrics.video_views_3s is
    'Visualizações curtas informadas pela action video_view da Meta.';
comment on column public.adset_metrics.video_views_3s is
    'Visualizações curtas informadas pela action video_view da Meta.';
comment on column public.ad_metrics.video_views_3s is
    'Visualizações curtas informadas pela action video_view da Meta.';
