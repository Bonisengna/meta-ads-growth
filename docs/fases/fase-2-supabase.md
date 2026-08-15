# Fase 2 — Supabase

Status: **implementação de integração concluída; conexão com projeto exclusivo do DescompliADS ainda pendente**.

## Objetivo

Conectar o backend FastAPI ao Supabase sem misturar o SaaS com bancos existentes de outros projetos.

A Fase 2 cobre:

- cliente Python do Supabase;
- variáveis de ambiente;
- chave secreta somente no backend;
- readiness do banco;
- tabela técnica de health;
- teste unitário de leitura;
- teste unitário de escrita;
- smoke test manual de leitura e escrita.

O modelo de negócio (clientes, contas, campanhas, métricas, análises etc.) pertence à **Fase 3**.

## Arquivos principais

```text
backend/
├── app/
│   ├── config/settings.py
│   ├── database/supabase.py
│   ├── services/supabase_service.py
│   └── api/health.py
├── scripts/
│   └── smoke_supabase.py
├── tests/
│   ├── test_health.py
│   └── test_supabase_service.py
└── .env.example

supabase/
└── migrations/
    └── 0001_app_health.sql
```

## Variáveis de ambiente

```env
SUPABASE_URL=
SUPABASE_SECRET_KEY=
SUPABASE_HEALTH_TABLE=app_health
```

Nunca versionar a chave real.

A aplicação continua iniciando mesmo sem Supabase configurado. Nesse estado:

```http
GET /health
```

continua retornando HTTP 200, enquanto:

```http
GET /health/database
GET /api/v1/health/database
```

retornam HTTP 503 com status `unconfigured`.

Isso separa:

- **liveness** — a API está viva;
- **readiness** — a dependência Supabase está pronta.

## Tabela técnica

A migration `0001_app_health.sql` cria somente:

```text
public.app_health
```

Essa tabela não faz parte do modelo comercial do SaaS. Ela existe para validar a infraestrutura antes da Fase 3.

## Como testar

### 1. Testes automatizados

Dentro de `backend/`:

```bash
pip install -r requirements-dev.txt
pytest -q
```

Os testes não dependem de um Supabase real para validar a lógica de leitura e escrita.

### 2. Configurar projeto real

No projeto Supabase exclusivo do DescompliADS:

1. aplicar `supabase/migrations/0001_app_health.sql`;
2. obter a Project URL;
3. criar/copiar uma Secret Key de servidor;
4. preencher o `.env` local:

```env
SUPABASE_URL=https://SEU-PROJETO.supabase.co
SUPABASE_SECRET_KEY=sb_secret_...
SUPABASE_HEALTH_TABLE=app_health
```

### 3. Teste somente leitura

Dentro de `backend/`:

```bash
python scripts/smoke_supabase.py
```

Resultado esperado:

```json
{
  "read": {
    "status": "ok",
    "service": "supabase",
    "table": "app_health",
    "rows_sampled": 0
  }
}
```

`rows_sampled` também pode ser `1` se houver um registro na tabela.

### 4. Teste real de escrita

```bash
python scripts/smoke_supabase.py --write
```

O script:

```text
insere marcador temporário
        ↓
confirma escrita
        ↓
remove marcador
```

Nenhum dado de teste deve permanecer na tabela ao final.

### 5. Testar readiness pela API

Com FastAPI rodando:

```http
GET /health/database
```

Esperado com Supabase funcionando:

```json
{
  "status": "ok",
  "service": "supabase",
  "table": "app_health",
  "rows_sampled": 0
}
```

## Segurança

- usar Secret Key apenas no backend;
- nunca expor a Secret Key no Next.js/browser;
- nunca commitar `.env`;
- `app_health` mantém RLS habilitado;
- acesso `anon` e `authenticated` está revogado nessa tabela técnica;
- o frontend usará outro modelo de acesso quando autenticação/RLS forem definidos.

## Estado atual

Implementado:

- [x] dependência `supabase` no Python;
- [x] configuração via `.env`;
- [x] cliente reutilizável;
- [x] tratamento de configuração ausente;
- [x] `/health/database`;
- [x] `/api/v1/health/database`;
- [x] migration técnica `app_health`;
- [x] teste unitário de leitura;
- [x] teste unitário de escrita e limpeza;
- [x] smoke test manual;

Pendente para concluir a Fase 2 em ambiente real:

- [ ] criar ou selecionar um projeto Supabase exclusivo do DescompliADS;
- [ ] aplicar `0001_app_health.sql` nesse projeto;
- [ ] configurar `SUPABASE_URL` e `SUPABASE_SECRET_KEY` no ambiente;
- [ ] executar smoke test de leitura;
- [ ] executar smoke test de escrita;
- [ ] confirmar `/health/database` HTTP 200.

## Critério de encerramento

A Fase 2 é considerada encerrada quando um projeto Supabase exclusivo do DescompliADS responder com sucesso aos testes de leitura e escrita e ao endpoint `/health/database`.
