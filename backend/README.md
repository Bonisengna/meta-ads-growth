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

## Documentação

- Fase 1: `../docs/fases/fase-1-backend.md`
- Fase 2: `../docs/fases/fase-2-supabase.md`
