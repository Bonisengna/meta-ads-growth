-- Fase 10 — decisões humanas e acompanhamento de recomendações explicáveis.

alter table public.recommendations
    add column recommendation_key text,
    add column rule_code text,
    add column decision_note text,
    add column decided_by uuid references auth.users(id) on delete set null,
    add column decided_at timestamptz;

alter table public.recommendations
    alter column decided_by set default auth.uid(),
    alter column decided_at set default now();

alter table public.recommendations
    add constraint recommendations_status_check
    check (status in ('PENDING', 'ACCEPTED', 'REJECTED'));

create index idx_recommendations_key on public.recommendations(recommendation_key);
create index idx_recommendations_decided_by on public.recommendations(decided_by)
    where decided_by is not null;
create index idx_improvements_recommendation on public.improvements(recommendation_id)
    where recommendation_id is not null;

grant select, insert on table public.ai_analyses, public.recommendations,
    public.improvements to authenticated;

create or replace function public.can_edit_intelligence(
    target_campaign_id uuid, target_adset_id uuid, target_ad_id uuid
) returns boolean
language sql
stable
security invoker
set search_path = ''
as $$
    select exists (
        select 1
        from public.user_client_access access
        join public.meta_accounts account on account.client_id = access.client_id
        join public.campaigns campaign on campaign.meta_account_id = account.id
        left join public.adsets adset on adset.campaign_id = campaign.id
        left join public.ads ad on ad.adset_id = adset.id
        where access.user_id = (select auth.uid())
          and access.active
          and access.role in ('OWNER', 'ADMIN', 'ANALYST')
          and (
              campaign.id = target_campaign_id
              or adset.id = target_adset_id
              or ad.id = target_ad_id
          )
    );
$$;

revoke all on function public.can_edit_intelligence(uuid, uuid, uuid) from public;
grant execute on function public.can_edit_intelligence(uuid, uuid, uuid) to authenticated;

create or replace function public.can_read_intelligence(
    target_campaign_id uuid, target_adset_id uuid, target_ad_id uuid
) returns boolean
language sql
stable
security invoker
set search_path = ''
as $$
    select exists (
        select 1
        from public.user_client_access access
        join public.meta_accounts account on account.client_id = access.client_id
        join public.campaigns campaign on campaign.meta_account_id = account.id
        left join public.adsets adset on adset.campaign_id = campaign.id
        left join public.ads ad on ad.adset_id = adset.id
        where access.user_id = (select auth.uid()) and access.active
          and (campaign.id = target_campaign_id or adset.id = target_adset_id or ad.id = target_ad_id)
    );
$$;

revoke all on function public.can_read_intelligence(uuid, uuid, uuid) from public;
grant execute on function public.can_read_intelligence(uuid, uuid, uuid) to authenticated;

create policy "users read authorized analyses"
on public.ai_analyses for select to authenticated
using (public.can_read_intelligence(campaign_id, adset_id, ad_id));

create policy "analysts create authorized analyses"
on public.ai_analyses for insert to authenticated
with check (public.can_edit_intelligence(campaign_id, adset_id, ad_id));

create policy "users read authorized recommendations"
on public.recommendations for select to authenticated
using (exists (
    select 1 from public.ai_analyses analysis
    where analysis.id = recommendations.analysis_id
      and public.can_read_intelligence(analysis.campaign_id, analysis.adset_id, analysis.ad_id)
));

create policy "analysts decide authorized recommendations"
on public.recommendations for insert to authenticated
with check (
    decided_by = (select auth.uid())
    and decided_at is not null
    and exists (
        select 1 from public.ai_analyses analysis
        where analysis.id = recommendations.analysis_id
          and public.can_edit_intelligence(analysis.campaign_id, analysis.adset_id, analysis.ad_id)
    )
);

create policy "users read authorized improvements"
on public.improvements for select to authenticated
using (public.can_read_intelligence(campaign_id, adset_id, ad_id));

create policy "analysts create authorized improvements"
on public.improvements for insert to authenticated
with check (public.can_edit_intelligence(campaign_id, adset_id, ad_id));
