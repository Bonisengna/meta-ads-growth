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

## API de leitura — Fase 4

Com `SUPABASE_URL` e `SUPABASE_SECRET_KEY` configurados, a primeira camada de
leitura está disponível em:

```http
GET /api/v1/clients
GET /api/v1/clients/{id}
GET /api/v1/meta-accounts
GET /api/v1/campaigns
GET /api/v1/campaigns/{id}
GET /api/v1/dashboard
```

As listas incluem entidades `ACTIVE` e `ARCHIVED`. Registros históricos não
são apagados. O dashboard consolida a quantidade de entidades e soma `spend`
e `leads` das métricas diárias de campanhas; `cpl` é calculado como
`spend / leads` e retorna `null` quando não há leads.

IDs inexistentes retornam HTTP 404, IDs inválidos retornam HTTP 422 e falhas
de acesso ao Supabase retornam HTTP 503. Os schemas e exemplos de resposta
podem ser consultados em `/docs`.

As listagens usam paginação (`page`, padrão 1; `page_size`, padrão 20 e máximo
100) e devolvem `items`, `page`, `page_size`, `total` e `pages`. Exemplos:

```http
GET /api/v1/clients?status=ARCHIVED&page=1&page_size=20
GET /api/v1/meta-accounts?client_id={client_id}&status=ACTIVE
GET /api/v1/campaigns?meta_account_id={meta_account_id}&status=ACTIVE
```

Sem o parâmetro `status`, tanto `ACTIVE` quanto `ARCHIVED` são retornados.

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

## Documentação

- Fase 1: `../docs/fases/fase-1-backend.md`
- Fase 2: `../docs/fases/fase-2-supabase.md`
