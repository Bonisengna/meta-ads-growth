-- Índices dos vínculos adicionados pelo controle de sincronização.

create index if not exists sync_runs_client_started
    on public.sync_runs(client_id, started_at desc);
create index if not exists sync_runs_requested_by
    on public.sync_runs(requested_by);
create index if not exists sync_runs_recovery_of
    on public.sync_runs(recovery_of);

create index if not exists sync_requests_requested_by
    on public.sync_requests(requested_by);
create index if not exists sync_requests_recovery_of
    on public.sync_requests(recovery_of);
create index if not exists sync_requests_sync_run_id
    on public.sync_requests(sync_run_id);

comment on index public.sync_runs_client_started is
    'Histórico recente de sincronização por cliente.';
