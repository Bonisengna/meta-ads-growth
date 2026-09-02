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
    ├── 0007_sync_runs.sql
    ├── 0008_integration_alerts.sql
    ├── 0009_integration_alerts_account_index.sql
    ├── 0010_user_client_access_rls.sql
    ├── ...
    ├── 0019_operational_reliability.sql
    ├── 0020_sync_control.sql
    └── 0021_sync_control_indexes.sql
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

### 0008_integration_alerts.sql

Cria alertas operacionais de token e integração com RLS, acesso exclusivo do
backend e unicidade para impedir alertas abertos duplicados.

### 0010_user_client_access_rls.sql

Cria o vínculo entre usuários do Supabase Auth e clientes do SaaS. Concede
leitura a `authenticated` somente sob políticas RLS que percorrem a hierarquia
cliente → conta → campanha → conjunto → anúncio → métricas.

### 0019_operational_reliability.sql

Amplia a carga histórica para 360 dias, registra contas parcialmente
sincronizadas e separa os horários de atualização das entidades, métricas e
execuções totalmente concluídas. O campo legado `last_synced_at` é preservado
por compatibilidade, mas não deve ser usado para afirmar que as métricas estão
atuais.

### 0020_sync_control.sql

Cria a fila persistente de sincronizações solicitadas pelo painel e adiciona
progresso, origem, cliente e vínculo de recuperação a `sync_runs`. O worker
consome a fila sem depender de uma requisição HTTP longa. A fila é protegida
por RLS, acessível somente pela `service_role` e impede dois pedidos abertos
para o mesmo cliente.
### 0021_sync_control_indexes.sql

Adiciona índices aos vínculos da fila e do histórico identificados pelo
Performance Advisor após a aplicação da migration `0020`.


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
