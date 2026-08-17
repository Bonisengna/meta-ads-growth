-- Fase 7 — alertas operacionais da integração Meta.

create table public.integration_alerts (
    id uuid primary key default gen_random_uuid(),
    meta_account_id uuid references public.meta_accounts(id) on delete set null,
    scope_key text not null default 'GLOBAL',
    alert_type text not null,
    severity text not null default 'ERROR',
    title text not null,
    message text not null,
    status text not null default 'OPEN',
    detected_at timestamptz not null default now(),
    resolved_at timestamptz,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint integration_alerts_status check (status in ('OPEN', 'RESOLVED')),
    constraint integration_alerts_severity check (severity in ('WARNING', 'ERROR', 'CRITICAL'))
);

create unique index integration_alerts_one_open
    on public.integration_alerts(alert_type, scope_key)
    where status = 'OPEN';
create index integration_alerts_status_detected
    on public.integration_alerts(status, detected_at desc);

alter table public.integration_alerts enable row level security;
revoke all on table public.integration_alerts from anon, authenticated;
grant select, insert, update on table public.integration_alerts to service_role;
