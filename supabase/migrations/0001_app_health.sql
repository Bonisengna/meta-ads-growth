-- Fase 2 — tabela técnica para validar leitura e escrita do backend.
-- Não contém dados de negócio do DescompliADS.

create table if not exists public.app_health (
    id uuid primary key default gen_random_uuid(),
    service text not null,
    test_marker text unique,
    created_at timestamptz not null default now()
);

alter table public.app_health enable row level security;

-- A API backend usa uma chave secreta/role de servidor.
-- Nenhum acesso é concedido aos papéis públicos do frontend nesta fase.
revoke all on table public.app_health from anon, authenticated;
grant select, insert, delete on table public.app_health to service_role;
