-- Índices usados pelas políticas RLS e pelo acompanhamento de melhorias.

drop index if exists public.idx_improvements_recommendation;

create index if not exists idx_improvements_campaign_id
    on public.improvements(campaign_id) where campaign_id is not null;
create index if not exists idx_improvements_adset_id
    on public.improvements(adset_id) where adset_id is not null;
create index if not exists idx_improvements_ad_id
    on public.improvements(ad_id) where ad_id is not null;
