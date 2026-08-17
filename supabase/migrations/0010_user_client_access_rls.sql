-- Fase 8 — autorização multi-tenant por usuário e cliente.

create table public.user_client_access (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users(id) on delete cascade,
    client_id uuid not null references public.clients(id) on delete cascade,
    role text not null default 'VIEWER',
    active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint user_client_access_role check (role in ('OWNER', 'ADMIN', 'ANALYST', 'VIEWER')),
    constraint user_client_access_unique unique (user_id, client_id)
);

create index user_client_access_client_id on public.user_client_access(client_id);
alter table public.user_client_access enable row level security;
revoke all on table public.user_client_access from anon, authenticated;
grant select on table public.user_client_access to authenticated;
grant select, insert, update, delete on table public.user_client_access to service_role;

create policy "users read own active access"
on public.user_client_access for select to authenticated
using ((select auth.uid()) = user_id and active);

grant select on table public.clients, public.meta_accounts, public.campaigns,
    public.adsets, public.ads, public.campaign_metrics, public.adset_metrics,
    public.ad_metrics to authenticated;

create policy "users read authorized clients"
on public.clients for select to authenticated
using (exists (
    select 1 from public.user_client_access access
    where access.client_id = clients.id
      and access.user_id = (select auth.uid()) and access.active
));

create policy "users read authorized meta accounts"
on public.meta_accounts for select to authenticated
using (exists (
    select 1 from public.user_client_access access
    where access.client_id = meta_accounts.client_id
      and access.user_id = (select auth.uid()) and access.active
));

create policy "users read authorized campaigns"
on public.campaigns for select to authenticated
using (exists (
    select 1 from public.meta_accounts account
    join public.user_client_access access on access.client_id = account.client_id
    where account.id = campaigns.meta_account_id
      and access.user_id = (select auth.uid()) and access.active
));

create policy "users read authorized adsets"
on public.adsets for select to authenticated
using (exists (
    select 1 from public.campaigns campaign
    join public.meta_accounts account on account.id = campaign.meta_account_id
    join public.user_client_access access on access.client_id = account.client_id
    where campaign.id = adsets.campaign_id
      and access.user_id = (select auth.uid()) and access.active
));

create policy "users read authorized ads"
on public.ads for select to authenticated
using (exists (
    select 1 from public.adsets adset
    join public.campaigns campaign on campaign.id = adset.campaign_id
    join public.meta_accounts account on account.id = campaign.meta_account_id
    join public.user_client_access access on access.client_id = account.client_id
    where adset.id = ads.adset_id
      and access.user_id = (select auth.uid()) and access.active
));

create policy "users read authorized campaign metrics"
on public.campaign_metrics for select to authenticated
using (exists (
    select 1 from public.campaigns campaign
    join public.meta_accounts account on account.id = campaign.meta_account_id
    join public.user_client_access access on access.client_id = account.client_id
    where campaign.id = campaign_metrics.campaign_id
      and access.user_id = (select auth.uid()) and access.active
));

create policy "users read authorized adset metrics"
on public.adset_metrics for select to authenticated
using (exists (
    select 1 from public.adsets adset
    join public.campaigns campaign on campaign.id = adset.campaign_id
    join public.meta_accounts account on account.id = campaign.meta_account_id
    join public.user_client_access access on access.client_id = account.client_id
    where adset.id = adset_metrics.adset_id
      and access.user_id = (select auth.uid()) and access.active
));

create policy "users read authorized ad metrics"
on public.ad_metrics for select to authenticated
using (exists (
    select 1 from public.ads ad
    join public.adsets adset on adset.id = ad.adset_id
    join public.campaigns campaign on campaign.id = adset.campaign_id
    join public.meta_accounts account on account.id = campaign.meta_account_id
    join public.user_client_access access on access.client_id = account.client_id
    where ad.id = ad_metrics.ad_id
      and access.user_id = (select auth.uid()) and access.active
));
