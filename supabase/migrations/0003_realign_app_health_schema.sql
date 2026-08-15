-- Corrige o schema técnico app_health para alinhar o banco real ao contrato do backend.
-- A tabela estava vazia e continha colunas diferentes das esperadas pelo serviço Python.

drop table if exists public.app_health;

create table public.app_health (
    id uuid primary key default gen_random_uuid(),
    service text not null,
    test_marker text unique,
    created_at timestamptz not null default now()
);

alter table public.app_health enable row level security;

revoke all on table public.app_health from anon, authenticated;
grant select, insert, delete on table public.app_health to service_role;
