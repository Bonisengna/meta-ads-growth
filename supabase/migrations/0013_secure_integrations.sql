-- Ajustes seguros: metadados separados dos segredos armazenados no Supabase Vault.

create table public.system_admins (
    user_id uuid primary key references auth.users(id) on delete cascade,
    created_at timestamptz not null default now()
);

alter table public.system_admins enable row level security;
revoke all on table public.system_admins from anon, authenticated;
grant select on table public.system_admins to authenticated;
grant select, insert, delete on table public.system_admins to service_role;

create policy "system admins read own membership"
on public.system_admins for select to authenticated
using ((select auth.uid()) = user_id);

create table public.integration_credentials (
    id uuid primary key default gen_random_uuid(),
    client_id uuid references public.clients(id) on delete cascade,
    provider text not null,
    connection_name text not null,
    secret_id uuid not null,
    config jsonb not null default '{}'::jsonb,
    status text not null default 'CONFIGURED',
    last_validated_at timestamptz,
    updated_by uuid references auth.users(id) on delete set null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint integration_credentials_provider
        check (provider in ('META_CLIENT', 'META_SYSTEM', 'OPENAI')),
    constraint integration_credentials_status
        check (status in ('CONFIGURED', 'VALID', 'INVALID')),
    constraint integration_credentials_scope check (
        (provider = 'META_CLIENT' and client_id is not null)
        or (provider in ('META_SYSTEM', 'OPENAI') and client_id is null)
    )
);

create unique index integration_credentials_client_provider
    on public.integration_credentials(client_id, provider)
    where client_id is not null;
create unique index integration_credentials_system_provider
    on public.integration_credentials(provider)
    where client_id is null;
create index integration_credentials_updated_by
    on public.integration_credentials(updated_by) where updated_by is not null;

alter table public.integration_credentials enable row level security;
revoke all on table public.integration_credentials from anon, authenticated;
grant select, insert, update, delete on table public.integration_credentials to service_role;

create or replace function public.store_vault_secret(
    p_secret_value text, p_secret_name text, p_existing_secret_id uuid default null
) returns uuid
language plpgsql
security definer
set search_path = ''
as $$
declare stored_id uuid;
begin
    if p_secret_value is null or length(p_secret_value) < 8 then
        raise exception 'Segredo inválido';
    end if;
    if p_existing_secret_id is null then
        stored_id := vault.create_secret(p_secret_value, p_secret_name, 'DescompliADS integration');
    else
        perform vault.update_secret(p_existing_secret_id, p_secret_value, p_secret_name, 'DescompliADS integration');
        stored_id := p_existing_secret_id;
    end if;
    return stored_id;
end;
$$;

create or replace function public.read_vault_secret(p_secret_id uuid)
returns text
language sql
stable
security definer
set search_path = ''
as $$
    select decrypted_secret from vault.decrypted_secrets where id = p_secret_id;
$$;

revoke all on function public.store_vault_secret(text, text, uuid) from public, anon, authenticated;
revoke all on function public.read_vault_secret(uuid) from public, anon, authenticated;
grant execute on function public.store_vault_secret(text, text, uuid) to service_role;
grant execute on function public.read_vault_secret(uuid) to service_role;
