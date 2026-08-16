-- Fase 6 — protocolo de execução e trava da sincronização automática Meta.

create table public.sync_runs (
    id uuid primary key default gen_random_uuid(),
    scope text not null default 'META_ALL',
    status text not null default 'RUNNING',
    started_at timestamptz not null default now(),
    finished_at timestamptz,
    duration_ms bigint,
    lock_expires_at timestamptz not null,
    lookback_days integer not null,
    accounts_total integer not null default 0,
    accounts_success integer not null default 0,
    accounts_failed integer not null default 0,
    result jsonb not null default '{}'::jsonb,
    error_summary text,
    created_at timestamptz not null default now(),
    constraint sync_runs_status check (status in ('RUNNING', 'SUCCESS', 'PARTIAL', 'FAILED')),
    constraint sync_runs_lookback_days check (lookback_days between 1 and 120),
    constraint sync_runs_duration check (duration_ms is null or duration_ms >= 0)
);

-- Uma única execução RUNNING por escopo. O índice torna a trava atômica.
create unique index sync_runs_one_running_scope
    on public.sync_runs(scope)
    where status = 'RUNNING';

create index sync_runs_started_at on public.sync_runs(started_at desc);
create index sync_runs_status_started_at on public.sync_runs(status, started_at desc);

alter table public.sync_runs enable row level security;

revoke all on table public.sync_runs from anon, authenticated;
grant select, insert, update on table public.sync_runs to service_role;
