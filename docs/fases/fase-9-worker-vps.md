# Fase 9 — Worker de sincronização na VPS

O `meta-worker` executa a sincronização diária fora do processo da FastAPI. A
API continua atendendo o dashboard enquanto o worker consulta a Meta e grava no
Supabase.

```text
meta-worker (03:00 America/Sao_Paulo)
        ↓
contas ACTIVE
        ↓
entidades + últimos 3 dias de métricas
        ↓
UPSERT + ARCHIVED + sync_runs no Supabase
```

O worker reutiliza `MetaSyncRunner`. Portanto, mantém tentativas controladas,
trava contra concorrência, reprocessamento de atribuição, arquivamento histórico
e registros `RUNNING`, `SUCCESS`, `PARTIAL` ou `FAILED`.

## Serviço no EasyPanel

Crie um App separado no projeto `descompliads`:

```text
Nome: meta-worker
Repository: Bonisengna/meta-ads-growth
Branch: meta-ads-pro
Build Path: backend
Builder: Dockerfile
Dockerfile: Dockerfile.worker
Réplicas: 1
Domínio: nenhum
Porta publicada: nenhuma
```

Depois da primeira validação, crie para o worker um acionador de implantação e
um webhook próprios. Nunca reutilize o token do backend ou do frontend. Como o
worker não atende usuários, ele continua sem domínio mesmo com Auto Deploy.

Copie para o worker as mesmas variáveis de servidor do backend:

```text
ENVIRONMENT=production
DEBUG=false
TIMEZONE=America/Sao_Paulo

SUPABASE_URL=...
SUPABASE_SECRET_KEY=...
SUPABASE_PUBLISHABLE_KEY=...
SUPABASE_HEALTH_TABLE=app_health

META_GRAPH_BASE_URL=https://graph.facebook.com
META_GRAPH_VERSION=v25.0
META_ACCESS_TOKEN=...
META_APP_ID=...
META_APP_SECRET=...
META_REQUEST_TIMEOUT_SECONDS=30
META_SYNC_LOOKBACK_DAYS=3
META_SYNC_MAX_ATTEMPTS=3
META_SYNC_RETRY_DELAY_SECONDS=2
META_SYNC_LOCK_MINUTES=120
META_SYNC_DAILY_TIME=03:00
META_SYNC_RUN_ON_START=false
```

O worker não precisa de CORS, domínio, porta HTTP ou credenciais públicas do
frontend. Segredos permanecem apenas no ambiente do EasyPanel.

## Primeira validação

Na primeira implantação, use temporariamente:

```text
META_SYNC_RUN_ON_START=true
```

O log deve mostrar, sem tokens:

```text
worker_started
sync_finished
sync_scheduled
```

Confirme no Supabase que a nova linha em `sync_runs` terminou como `SUCCESS` ou
`PARTIAL` e confira o horário de `last_synced_at`. Depois altere imediatamente:

```text
META_SYNC_RUN_ON_START=false
```

e implante novamente. Isso evita uma coleta a cada atualização do container.

## Operação diária

- `META_SYNC_DAILY_TIME` usa o formato `HH:MM`;
- o fuso vem de `TIMEZONE`, não do relógio UTC do container;
- três dias são reprocessados por padrão para absorver ajustes de atribuição;
- a trava no Supabase impede a execução concorrente;
- falhas de uma conta permitem resultado `PARTIAL` para as demais;
- nenhuma campanha histórica é apagada; entidades fora de operação ficam
  `ARCHIVED`.

## Teste sem o computador local

Depois da primeira execução bem-sucedida:

1. desative a tarefa `DescompliADS Meta Sync` no Agendador do Windows;
2. mantenha `META_SYNC_RUN_ON_START=false` no EasyPanel;
3. aguarde a execução diária da VPS;
4. confira `sync_runs`, `/api/v1/health/meta` e o dashboard;
5. só remova a tarefa local depois de pelo menos duas execuções da VPS.

## Rollback

Se o worker novo falhar:

1. pare apenas o serviço `meta-worker`; não pare API ou frontend;
2. reative temporariamente a tarefa do Windows;
3. no EasyPanel, abra Deployments e restaure a última imagem funcional;
4. confirme que não existe linha `RUNNING` válida antes de disparar manualmente;
5. preserve `sync_runs` e métricas para auditoria; não apague registros;
6. depois do reparo, teste uma execução com `META_SYNC_RUN_ON_START=true` e volte
   para `false`.

## Analogia

A API é a recepção e o worker é o carteiro. Eles moram no mesmo condomínio, mas
trabalham em salas separadas. Se o carteiro atrasar, a recepção continua aberta;
o protocolo no Supabase mostra quando a entrega começou, terminou ou falhou.
