-- Fase 3 — núcleo relacional do DescompliADS.
-- Identidade interna usa UUID; IDs da Meta são preservados separadamente.
-- Campanhas, conjuntos e anúncios devem ser arquivados via status = 'ARCHIVED',
-- não apagados, para preservar histórico e análises.

create table public.clients (
    id uuid primary key default gen_random_uuid(),
    name text not null,
    slug text not null unique,
    status text not null default 'ACTIVE',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table public.meta_accounts (
    id uuid primary key default gen_random_uuid(),
    client_id uuid not null references public.clients(id) on delete restrict,
    meta_account_id text not null unique,
    name text not null,
    currency text,
    timezone text,
    status text not null default 'ACTIVE',
    last_synced_at timestamptz,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table public.campaigns (
    id uuid primary key default gen_random_uuid(),
    meta_account_id uuid not null references public.meta_accounts(id) on delete restrict,
    meta_campaign_id text not null unique,
    name text not null,
    objective text,
    status text not null default 'ACTIVE',
    meta_created_at timestamptz,
    meta_updated_at timestamptz,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table public.adsets (
    id uuid primary key default gen_random_uuid(),
    campaign_id uuid not null references public.campaigns(id) on delete restrict,
    meta_adset_id text not null unique,
    name text not null,
    status text not null default 'ACTIVE',
    optimization_goal text,
    billing_event text,
    daily_budget numeric(14,2),
    lifetime_budget numeric(14,2),
    meta_created_at timestamptz,
    meta_updated_at timestamptz,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table public.ads (
    id uuid primary key default gen_random_uuid(),
    adset_id uuid not null references public.adsets(id) on delete restrict,
    meta_ad_id text not null unique,
    name text not null,
    status text not null default 'ACTIVE',
    creative_id text,
    meta_created_at timestamptz,
    meta_updated_at timestamptz,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index idx_meta_accounts_client_id on public.meta_accounts(client_id);
create index idx_campaigns_meta_account_id on public.campaigns(meta_account_id);
create index idx_adsets_campaign_id on public.adsets(campaign_id);
create index idx_ads_adset_id on public.ads(adset_id);
create index idx_campaigns_status on public.campaigns(status);
create index idx_adsets_status on public.adsets(status);
create index idx_ads_status on public.ads(status);

alter table public.clients enable row level security;
alter table public.meta_accounts enable row level security;
alter table public.campaigns enable row level security;
alter table public.adsets enable row level security;
alter table public.ads enable row level security;

revoke all on table public.clients, public.meta_accounts, public.campaigns, public.adsets, public.ads from anon, authenticated;
grant select, insert, update, delete on table public.clients, public.meta_accounts, public.campaigns, public.adsets, public.ads to service_role;
