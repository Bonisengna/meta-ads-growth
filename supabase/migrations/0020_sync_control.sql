-- Gate 2 — fila persistente, progresso e recuperação da sincronização Meta.

alter table public.sync_runs
    add column if not exists trigger_source text not null default 'SCHEDULED',
    add column if not exists requested_by uuid references auth.users(id) on delete set null,
    add column if not exists client_id uuid references public.clients(id) on delete set null,
    add column if not exists recovery_of uuid references public.sync_runs(id) on delete set null,
    add column if not exists current_stage text,
    add column if not exists current_account_name text,
    add column if not exists progress_current integer not null default 0,
    add column if not exists progress_total integer not null default 0;

alter table public.sync_runs
    drop constraint if exists sync_runs_trigger_source;
alter table public.sync_runs
    add constraint sync_runs_trigger_source
    check (trigger_source in ('SCHEDULED', 'MANUAL', 'RECOVERY'));
alter table public.sync_runs
    drop constraint if exists sync_runs_progress_nonnegative;
alter table public.sync_runs
    add constraint sync_runs_progress_nonnegative
    check (progress_current >= 0 and progress_total >= 0 and progress_current <= progress_total);

create table if not exists public.sync_requests (
    id uuid primary key default gen_random_uuid(),
    client_id uuid not null references public.clients(id) on delete cascade,
    requested_by uuid references auth.users(id) on delete set null,
    lookback_days integer not null default 3,
    status text not null default 'PENDING',
    recovery_of uuid references public.sync_runs(id) on delete set null,
    sync_run_id uuid references public.sync_runs(id) on delete set null,
    created_at timestamptz not null default now(),
    started_at timestamptz,
    finished_at timestamptz,
    error_summary text,
    constraint sync_requests_lookback_days check (lookback_days between 1 and 360),
    constraint sync_requests_status check (status in ('PENDING', 'RUNNING', 'SUCCESS', 'PARTIAL', 'FAILED'))
);

create index if not exists sync_requests_created_at on public.sync_requests(created_at desc);
create index if not exists sync_requests_status_created_at on public.sync_requests(status, created_at);
create unique index if not exists sync_requests_one_open_client
    on public.sync_requests(client_id)
    where status in ('PENDING', 'RUNNING');

alter table public.sync_requests enable row level security;
revoke all on table public.sync_requests from anon, authenticated;
grant select, insert, update on table public.sync_requests to service_role;

comment on table public.sync_requests is
    'Fila persistente de sincronizações manuais consumida pelo worker Meta.';
comment on column public.sync_runs.recovery_of is
    'Execução com falha que originou este reprocessamento.';
