-- Cadastro empresarial completo dos clientes do DescompliADS.
-- Os dados continuam em clients para preservar o vínculo com todo o histórico Meta.

alter table public.clients
    add column if not exists legal_name text,
    add column if not exists tax_id_type text not null default 'CNPJ',
    add column if not exists tax_id text,
    add column if not exists segment text,
    add column if not exists niche text,
    add column if not exists business_model text not null default 'B2C',
    add column if not exists primary_audience text,
    add column if not exists website text,
    add column if not exists contact_name text,
    add column if not exists contact_email text,
    add column if not exists contact_phone text,
    add column if not exists city text,
    add column if not exists state text,
    add column if not exists country_code text not null default 'BR',
    add column if not exists timezone text not null default 'America/Sao_Paulo',
    add column if not exists currency text not null default 'BRL',
    add column if not exists primary_goal text,
    add column if not exists monthly_media_budget numeric(14,2),
    add column if not exists onboarding_status text not null default 'NEW',
    add column if not exists notes text;

alter table public.clients
    add constraint clients_tax_id_type_check check (tax_id_type in ('CNPJ', 'CPF', 'OTHER')),
    add constraint clients_business_model_check check (business_model in ('B2B', 'B2C', 'B2B2C', 'LOCAL_SERVICES', 'OTHER')),
    add constraint clients_onboarding_status_check check (onboarding_status in ('NEW', 'SETUP', 'ACTIVE', 'PAUSED')),
    add constraint clients_country_code_check check (country_code ~ '^[A-Z]{2}$'),
    add constraint clients_currency_check check (currency ~ '^[A-Z]{3}$'),
    add constraint clients_monthly_media_budget_check check (monthly_media_budget is null or monthly_media_budget >= 0);

create index if not exists clients_segment_idx on public.clients(segment);
create index if not exists clients_onboarding_status_idx on public.clients(onboarding_status);

-- O navegador permanece com leitura direta. Escritas passam pela FastAPI,
-- que valida o papel do usuário e usa a chave de serviço somente no servidor.
revoke insert, update, delete on table public.clients from anon, authenticated;
grant select on table public.clients to authenticated;
grant select, insert, update, delete on table public.clients to service_role;
