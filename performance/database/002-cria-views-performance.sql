-- FASE 2 — Motor de Performance
-- Views derivadas da base diária criada na Fase 1.
-- Não altera métricas brutas; apenas calcula indicadores.

create or replace view public.vw_meta_ads_performance_diaria as
select
  m.*,

  -- CTR calculado a partir de todos os cliques.
  case when m.impressoes > 0
    then round((m.cliques::numeric / m.impressoes::numeric) * 100, 4)
    else null
  end as ctr_calculado,

  -- CTR de link mede apenas cliques que levam para o destino.
  case when m.impressoes > 0
    then round((m.cliques_link::numeric / m.impressoes::numeric) * 100, 4)
    else null
  end as ctr_link,

  case when m.cliques > 0
    then round(m.investimento / m.cliques::numeric, 4)
    else null
  end as cpc_calculado,

  case when m.impressoes > 0
    then round((m.investimento / m.impressoes::numeric) * 1000, 4)
    else null
  end as cpm_calculado,

  case when m.conversas_iniciadas > 0
    then round(m.investimento / m.conversas_iniciadas::numeric, 4)
    else null
  end as custo_conversa_calculado,

  -- Conversas divididas por cliques no link.
  case when m.cliques_link > 0
    then round((m.conversas_iniciadas::numeric / m.cliques_link::numeric) * 100, 4)
    else null
  end as taxa_clique_conversa,

  case when m.alcance > 0
    then round(m.impressoes::numeric / m.alcance::numeric, 4)
    else null
  end as frequencia

from public.meta_ads_metricas_diarias m;

comment on view public.vw_meta_ads_performance_diaria is
'Indicadores derivados diariamente a partir das métricas brutas da Meta Ads.';

create or replace view public.vw_meta_ads_benchmark_diario as
select
  data_referencia,
  conta_anuncio,
  nivel_analise,
  coalesce(objetivo_original, '') as objetivo_original,
  count(*) as quantidade_objetos,
  sum(investimento) as investimento_total,
  sum(impressoes) as impressoes_total,
  sum(alcance) as alcance_total,
  sum(cliques) as cliques_total,
  sum(cliques_link) as cliques_link_total,
  sum(conversas_iniciadas) as conversas_total,

  case when sum(cliques) > 0
    then round(sum(investimento) / sum(cliques)::numeric, 4)
    else null
  end as cpc_medio,

  case when sum(impressoes) > 0
    then round((sum(investimento) / sum(impressoes)::numeric) * 1000, 4)
    else null
  end as cpm_medio,

  case when sum(impressoes) > 0
    then round((sum(cliques_link)::numeric / sum(impressoes)::numeric) * 100, 4)
    else null
  end as ctr_link_medio,

  case when sum(conversas_iniciadas) > 0
    then round(sum(investimento) / sum(conversas_iniciadas)::numeric, 4)
    else null
  end as custo_conversa_medio,

  case when sum(cliques_link) > 0
    then round((sum(conversas_iniciadas)::numeric / sum(cliques_link)::numeric) * 100, 4)
    else null
  end as taxa_clique_conversa_media,

  case when sum(alcance) > 0
    then round(sum(impressoes)::numeric / sum(alcance)::numeric, 4)
    else null
  end as frequencia_media,

  round(sum(investimento) / nullif(count(*), 0), 4) as investimento_medio_objeto

from public.meta_ads_metricas_diarias
group by
  data_referencia,
  conta_anuncio,
  nivel_analise,
  coalesce(objetivo_original, '');

comment on view public.vw_meta_ads_benchmark_diario is
'Benchmark diário ponderado por conta, nível de análise e objetivo da campanha.';