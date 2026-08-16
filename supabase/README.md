# Supabase — DescompliADS

Área de persistência do MVP SaaS na branch `meta-ads-pro`.

## Projeto oficial

Projeto Supabase do DescompliADS:

```text
ref: uxiknjsfyxgvisdmqciz
url: https://uxiknjsfyxgvisdmqciz.supabase.co
```

Este é o projeto oficial do MVP SaaS. Não reutilizar o banco do sistema ArIA nem bancos da branch `n8n-operacional`.

## Fase 2

A integração base FastAPI ↔ Supabase já está implementada no código.

Estrutura atual:

```text
supabase/
├── README.md
└── migrations/
    ├── 0001_app_health.sql
    ├── 0002_harden_rls_auto_enable_permissions.sql
    ├── 0003_realign_app_health_schema.sql
    ├── 0004_core_meta_entities.sql
    ├── 0005_daily_metrics.sql
    ├── 0006_intelligence_actions.sql
    └── 0007_sync_runs.sql
```

### 0001_app_health.sql

Cria a tabela técnica `public.app_health` para validar leitura e escrita antes do modelo de negócio.

### 0002_harden_rls_auto_enable_permissions.sql

Remove permissão de execução pública da função `public.rls_auto_enable()` já existente no projeto, após alerta do Security Advisor.

### 0007_sync_runs.sql

Cria o protocolo da sincronização automática da Meta. Registra duração e
resultado das execuções e usa um índice único parcial como trava para impedir
duas rotas `RUNNING` simultâneas. A tabela mantém RLS habilitado, revoga acesso
de `anon` e `authenticated` e concede somente ao backend `service_role`.

## Validação realizada no projeto real

- migration `app_health` aplicada com sucesso;
- tabela `public.app_health` confirmada;
- INSERT de teste executado;
- registro de teste removido;
- tabela confirmada novamente com zero registros;
- Security Advisor reexecutado;
- warnings de execução pública da função `rls_auto_enable()` corrigidos.

O único aviso restante é informativo: `app_health` possui RLS habilitado e nenhuma policy pública. Isso é intencional nesta fase, pois a tabela técnica deve ser acessada somente pelo backend.

## Segurança

- o backend usa `SUPABASE_SECRET_KEY` via variável de ambiente;
- a chave real nunca deve ser commitada;
- frontend/Next.js não deve receber essa chave;
- `app_health` mantém RLS habilitado;
- `anon` e `authenticated` não recebem acesso à tabela técnica nesta fase.

## Configuração do backend

```env
SUPABASE_URL=https://uxiknjsfyxgvisdmqciz.supabase.co
SUPABASE_SECRET_KEY=sb_secret_...
SUPABASE_HEALTH_TABLE=app_health
```

A Secret Key deve ser configurada somente no ambiente do backend.

## Última validação pendente da Fase 2

Com a Secret Key configurada no ambiente do FastAPI:

```bash
cd backend
python scripts/smoke_supabase.py
python scripts/smoke_supabase.py --write
```

Depois validar:

```http
GET /health/database
```

Documentação completa: `../docs/fases/fase-2-supabase.md`.
