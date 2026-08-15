-- FASE 3 — Tendência e Fadiga
-- Banco alvo: Supabase / PostgreSQL.
-- Esta migration cria uma view de janelas históricas; não executa decisões na Meta.

create or replace view public.v_meta_ads_tendencia_janelas as
with referencia_conta as (
  select
    conta_anuncio,
    max(data_referencia) as data_referencia
  from public.meta_ads_metricas_diarias
  group by conta_anuncio
),
base as (
  select
    m.*,
    r.data_referencia as data_referencia_conta,
    (r.data_referencia - m.data_referencia) as dias_atras,
    case
      when m.nivel_analise = 'anuncio' then m.id_anuncio
      when m.nivel_analise = 'conjunto' then m.id_conjunto
      else m.id_campanha
    end as id_objeto,
    case
      when m.nivel_analise = 'anuncio' then m.nome_anuncio
      when m.nivel_analise = 'conjunto' then m.nome_conjunto
      else m.nome_campanha
    end as nome_objeto,
    case
      when m.alcance > 0 then m.impressoes::numeric / m.alcance
      else null
    end as frequencia_diaria
  from public.meta_ads_metricas_diarias m
  join referencia_conta r using (conta_anuncio)
  where m.data_referencia >= r.data_referencia - 29
)
select
  conta_anuncio,
  nivel_analise,
  id_objeto,
  max(nome_objeto) as nome_objeto,
  max(objetivo_original) as objetivo_original,
  max(data_referencia_conta) as data_referencia,

  count(distinct data_referencia) filter (where dias_atras between 0 and 2) as dias_3,
  count(distinct data_referencia) filter (where dias_atras between 0 and 6) as dias_7,
  count(distinct data_referencia) filter (where dias_atras between 0 and 13) as dias_14,
  count(distinct data_referencia) filter (where dias_atras between 0 and 29) as dias_30,

  sum(investimento) filter (where dias_atras between 0 and 2) as investimento_3d,
  sum(impressoes) filter (where dias_atras between 0 and 2) as impressoes_3d,
  sum(cliques) filter (where dias_atras between 0 and 2) as cliques_3d,
  sum(cliques_link) filter (where dias_atras between 0 and 2) as cliques_link_3d,
  sum(conversas_iniciadas) filter (where dias_atras between 0 and 2) as conversas_3d,
  avg(frequencia_diaria) filter (where dias_atras between 0 and 2) as frequencia_media_diaria_3d,

  sum(investimento) filter (where dias_atras between 0 and 6) as investimento_7d,
  sum(impressoes) filter (where dias_atras between 0 and 6) as impressoes_7d,
  sum(cliques) filter (where dias_atras between 0 and 6) as cliques_7d,
  sum(cliques_link) filter (where dias_atras between 0 and 6) as cliques_link_7d,
  sum(conversas_iniciadas) filter (where dias_atras between 0 and 6) as conversas_7d,
  avg(frequencia_diaria) filter (where dias_atras between 0 and 6) as frequencia_media_diaria_7d,

  sum(investimento) filter (where dias_atras between 0 and 13) as investimento_14d,
  sum(impressoes) filter (where dias_atras between 0 and 13) as impressoes_14d,
  sum(cliques) filter (where dias_atras between 0 and 13) as cliques_14d,
  sum(cliques_link) filter (where dias_atras between 0 and 13) as cliques_link_14d,
  sum(conversas_iniciadas) filter (where dias_atras between 0 and 13) as conversas_14d,
  avg(frequencia_diaria) filter (where dias_atras between 0 and 13) as frequencia_media_diaria_14d,

  sum(investimento) filter (where dias_atras between 0 and 29) as investimento_30d,
  sum(impressoes) filter (where dias_atras between 0 and 29) as impressoes_30d,
  sum(cliques) filter (where dias_atras between 0 and 29) as cliques_30d,
  sum(cliques_link) filter (where dias_atras between 0 and 29) as cliques_link_30d,
  sum(conversas_iniciadas) filter (where dias_atras between 0 and 29) as conversas_30d,
  avg(frequencia_diaria) filter (where dias_atras between 0 and 29) as frequencia_media_diaria_30d,

  -- Baseline sem sobreposição para alerta rápido: 7 dias imediatamente anteriores aos 3 dias recentes.
  sum(investimento) filter (where dias_atras between 3 and 9) as investimento_baseline_7d,
  sum(impressoes) filter (where dias_atras between 3 and 9) as impressoes_baseline_7d,
  sum(cliques) filter (where dias_atras between 3 and 9) as cliques_baseline_7d,
  sum(cliques_link) filter (where dias_atras between 3 and 9) as cliques_link_baseline_7d,
  sum(conversas_iniciadas) filter (where dias_atras between 3 and 9) as conversas_baseline_7d,
  avg(frequencia_diaria) filter (where dias_atras between 3 and 9) as frequencia_media_baseline_7d,

  -- Confirmação: 7 dias atuais comparados aos 7 imediatamente anteriores.
  sum(investimento) filter (where dias_atras between 7 and 13) as investimento_7d_anterior,
  sum(impressoes) filter (where dias_atras between 7 and 13) as impressoes_7d_anterior,
  sum(cliques) filter (where dias_atras between 7 and 13) as cliques_7d_anterior,
  sum(cliques_link) filter (where dias_atras between 7 and 13) as cliques_link_7d_anterior,
  sum(conversas_iniciadas) filter (where dias_atras between 7 and 13) as conversas_7d_anterior,
  avg(frequencia_diaria) filter (where dias_atras between 7 and 13) as frequencia_media_7d_anterior
from base
group by conta_anuncio, nivel_analise, id_objeto;

comment on view public.v_meta_ads_tendencia_janelas is
'Janelas de 3, 7, 14 e 30 dias para análise de tendência e fadiga de Meta Ads.';
