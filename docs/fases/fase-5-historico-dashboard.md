# Fase 5 — Coleta histórica e dashboard por período

## Objetivo

Transformar métricas diárias isoladas em séries históricas úteis para análise,
permitindo selecionar um período e compará-lo com o intervalo imediatamente
anterior de mesma duração.

## Coleta histórica

Execute a partir de `backend/`:

```powershell
.\.venv\Scripts\python.exe scripts\smoke_meta.py --metrics ACCOUNT_ID --from-date 2025-11-01 --to-date 2025-11-30
```

A Meta Graph API é consultada com incremento diário. Campanhas, conjuntos e
anúncios são gravados com unicidade por entidade e data. O `UPSERT` permite
reprocessar uma faixa com segurança, atualizando valores sem criar duplicatas.

## Períodos e comparação

O dashboard oferece janelas de 7, 14, 30, 90, 120, 180 e 360 dias, além de datas
personalizadas. Uma janela de 30 dias é comparada aos 30 dias imediatamente
anteriores. A resposta contém `period`, `previous_period`, `metrics`,
`previous_metrics` e `change_percent`.

Quando o valor anterior é zero ou inexistente, a variação percentual retorna
`null`, pois não existe uma base válida para divisão.

## Filtros

O endpoint `/api/v1/dashboard` aceita `client_id`, `meta_account_id` e
`campaign_id`. Os filtros seguem a hierarquia:

```text
cliente → conta Meta → campanha → conjunto → anúncio → métricas
```

## Indicadores

- investimento: soma de `spend`;
- leads e conversas: soma das ações atribuídas;
- CPL: investimento dividido por leads;
- CTR: cliques divididos por impressões, multiplicado por 100;
- CPC: investimento dividido por cliques;
- CPM: investimento dividido por impressões, multiplicado por 1.000.

## Histórico preservado

`ARCHIVED` representa uma entidade que deixou de operar, não um registro
apagado. As consultas históricas filtram por entidade e data, nunca pelo status
atual. Por isso, resultados antigos permanecem nos relatórios.

## Endpoints adicionados

```http
GET /api/v1/adsets
GET /api/v1/adsets/{id}
GET /api/v1/ads
GET /api/v1/ads/{id}
GET /api/v1/metrics/campaigns
GET /api/v1/metrics/adsets
GET /api/v1/metrics/ads
GET /api/v1/dashboard
```

Todos podem ser explorados e validados em `/docs` enquanto o servidor local
estiver em execução.
