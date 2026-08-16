# Backend — FastAPI

Backend do DescompliADS.

Responsabilidades:

- API REST;
- regras de negócio;
- consolidação de métricas;
- comparação de períodos;
- acesso ao Supabase;
- preparação de respostas para o frontend.

A API fica em `app/api/`.

## Saúde da aplicação

```http
GET /
GET /health
GET /api/v1/health
```

O `/health` é um liveness check e não depende de serviços externos.

## Saúde do Supabase

Na Fase 2 foi adicionado:

```http
GET /health/database
GET /api/v1/health/database
```

Esse endpoint consulta a tabela técnica `app_health` e retorna HTTP 503 quando o Supabase ainda não está configurado ou não pode ser consultado.

Configuração necessária no `.env`:

```env
SUPABASE_URL=
SUPABASE_SECRET_KEY=
SUPABASE_HEALTH_TABLE=app_health
```

Nunca versionar a chave real.

## Smoke test Supabase

Somente leitura:

```bash
python scripts/smoke_supabase.py
```

Leitura + escrita temporária + limpeza:

```bash
python scripts/smoke_supabase.py --write
```

## API histórica — Fase 5

Com `SUPABASE_URL` e `SUPABASE_SECRET_KEY` configurados, a primeira camada de
leitura está disponível em:

```http
GET /api/v1/clients
GET /api/v1/clients/{id}
GET /api/v1/meta-accounts
GET /api/v1/campaigns
GET /api/v1/campaigns/{id}
GET /api/v1/adsets
GET /api/v1/adsets/{id}
GET /api/v1/ads
GET /api/v1/ads/{id}
GET /api/v1/metrics/campaigns
GET /api/v1/metrics/adsets
GET /api/v1/metrics/ads
GET /api/v1/dashboard
```

As listas incluem entidades `ACTIVE` e `ARCHIVED`. Registros históricos não
são apagados. O dashboard calcula investimento, impressões, cliques, leads,
conversas, CPL, CTR, CPC e CPM. Ele também devolve o período anterior de mesma
duração e a variação percentual de cada indicador.

IDs inexistentes retornam HTTP 404, IDs inválidos retornam HTTP 422 e falhas
de acesso ao Supabase retornam HTTP 503. Os schemas e exemplos de resposta
podem ser consultados em `/docs`.

As listagens usam paginação (`page`, padrão 1; `page_size`, padrão 20 e máximo
100) e devolvem `items`, `page`, `page_size`, `total` e `pages`. Exemplos:

```http
GET /api/v1/clients?status=ARCHIVED&page=1&page_size=20
GET /api/v1/meta-accounts?client_id={client_id}&status=ACTIVE
GET /api/v1/campaigns?meta_account_id={meta_account_id}&status=ACTIVE
GET /api/v1/adsets?campaign_id={campaign_id}
GET /api/v1/ads?adset_id={adset_id}
```

Sem o parâmetro `status`, tanto `ACTIVE` quanto `ARCHIVED` são retornados.

O dashboard aceita janelas prontas de 7, 14, 30, 90 ou 120 dias:

```http
GET /api/v1/dashboard?days=30
GET /api/v1/dashboard?days=90&client_id={client_id}
GET /api/v1/dashboard?days=30&meta_account_id={meta_account_id}
GET /api/v1/dashboard?days=14&campaign_id={campaign_id}
```

Também aceita um intervalo personalizado. `date_from` e `date_to` devem ser
enviados juntos; nesse caso, `days` é ignorado:

```http
GET /api/v1/dashboard?date_from=2025-11-01&date_to=2025-11-30
GET /api/v1/metrics/campaigns?date_from=2025-11-01&date_to=2025-11-30&campaign_id={id}
GET /api/v1/metrics/adsets?date_from=2025-11-01&date_to=2025-11-30&adset_id={id}
GET /api/v1/metrics/ads?date_from=2025-11-01&date_to=2025-11-30&ad_id={id}
```

O status atual da entidade não é usado para excluir métricas. Assim, uma
campanha hoje `ARCHIVED` continua presente nas análises dos períodos em que
teve entrega.

## Meta Graph API — sincronização

A integração usa a versão configurável da Graph API e mantém as credenciais
somente no backend. O procedimento completo de criação do token, permissões,
configuração local, diagnóstico e preparação de produção está em:

- [Configuração da Meta Marketing API](docs/meta-marketing-api-setup.md)

Resumo das variáveis esperadas:

```env
META_GRAPH_BASE_URL=https://graph.facebook.com
META_GRAPH_VERSION=v25.0
META_ACCESS_TOKEN=
META_APP_ID=
META_APP_SECRET=
META_REQUEST_TIMEOUT_SECONDS=30
```

A sincronização não apaga campanhas, conjuntos ou anúncios. Entidades que não
forem retornadas ou não estiverem ativas passam a `ARCHIVED`. Os testes usam
transportes e respostas simuladas, portanto não consomem a API real.

Para executar os testes:

```bash
pytest
```

Para coletar uma faixa histórica, a partir de `backend/`:

```powershell
.\.venv\Scripts\python.exe scripts\smoke_meta.py --metrics ACCOUNT_ID --from-date 2025-11-01 --to-date 2025-11-30
```

O comando continua aceitando `--date AAAA-MM-DD` para apenas um dia. A coleta
usa `UPSERT`, portanto repetir o mesmo intervalo atualiza as linhas existentes
em vez de duplicá-las.

## Documentação

- Fase 1: `../docs/fases/fase-1-backend.md`
- Fase 2: `../docs/fases/fase-2-supabase.md`
- Fase 5: `../docs/fases/fase-5-historico-dashboard.md`
