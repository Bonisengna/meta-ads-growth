# Fase 3 — Modelagem de dados

## Objetivo

Estruturar o banco do DescompliADS antes da coleta real de dados da Meta, separando identidade, histórico de performance e inteligência.

Princípio do produto:

**MÉTRICAS → DIAGNÓSTICO → RECOMENDAÇÃO → MELHORIA → VALIDAÇÃO → APRENDIZADO**

## Regra de preservação histórica

Campanhas, conjuntos e anúncios não devem ser removidos do banco quando deixarem de operar. O estado histórico deve ser preservado usando o campo `status`, inclusive `ARCHIVED` quando aplicável.

Isso permite que análises, recomendações, métricas e melhorias antigas continuem consultáveis.

## Hierarquia principal

```text
clients
  1 ── N meta_accounts
             1 ── N campaigns
                        1 ── N adsets
                                   1 ── N ads
```

## Identidade interna e identidade Meta

Cada objeto possui UUID próprio do DescompliADS e, quando aplicável, um identificador externo da Meta.

Exemplos:

- `meta_accounts.id` + `meta_accounts.meta_account_id`
- `campaigns.id` + `campaigns.meta_campaign_id`
- `adsets.id` + `adsets.meta_adset_id`
- `ads.id` + `ads.meta_ad_id`

O UUID interno é usado nas Foreign Keys do sistema. O ID Meta é preservado para sincronização e rastreabilidade.

## Separação entre identidade e métricas

As tabelas `campaigns`, `adsets` e `ads` representam identidade/configuração.

Performance histórica fica em tabelas diárias separadas:

```text
campaigns 1 ── N campaign_metrics
adsets    1 ── N adset_metrics
ads       1 ── N ad_metrics
```

Cada tabela de métricas possui unicidade por entidade + `metric_date`. Isso permite sincronização idempotente com UPSERT e construção de períodos de 7, 14, 30 dias ou personalizados.

## Métricas MVP

- spend
- impressions
- reach
- clicks
- link_clicks
- ctr
- cpc
- cpm
- frequency
- leads
- cpl
- conversations
- cost_per_conversation

## Camada de inteligência

```text
campaign / adset / ad
        ↓
   ai_analyses
        ↓
 recommendations
        ↓
  improvements
```

`alerts` também pode apontar para campanha, conjunto ou anúncio.

As tabelas `ai_analyses`, `improvements` e `alerts` exigem exatamente uma referência de entidade preenchida (`campaign_id`, `adset_id` ou `ad_id`).

### ai_analyses

Registra diagnósticos históricos. Análises novas não sobrescrevem análises anteriores.

### recommendations

Registra ações sugeridas a partir de uma análise.

Status inicial: `PENDING`.

### improvements

Acompanha uma ação e sua validação antes/depois.

Status previstos para o frontend:

- `PENDING` — Pendente
- `TESTING` — Em teste
- `APPLIED` — Aplicada
- `VALIDATING` — Validando
- `RESOLVED` — Resolvida
- `DISCARDED` — Descartada

### alerts

Registra situações que exigem atenção.

Severidades previstas:

- `INFO`
- `WARNING`
- `CRITICAL`

Status previstos:

- `OPEN`
- `ACKNOWLEDGED`
- `RESOLVED`
- `IGNORED`

## Segurança

As tabelas da Fase 3 usam RLS e não concedem acesso aos papéis `anon` e `authenticated` nesta etapa. O backend acessa os dados com role/chave de servidor.

## Migrations

- `0004_core_meta_entities.sql` — clientes e hierarquia Meta
- `0005_daily_metrics.sql` — métricas diárias
- `0006_intelligence_actions.sql` — análises, recomendações, melhorias e alertas

## Próxima fase

Após validar e aplicar as migrations, a próxima etapa é definir o contrato de sincronização Meta → Supabase: payloads, transformação, UPSERT, ordem de dependências e política de atualização de `status`/`ARCHIVED`.
