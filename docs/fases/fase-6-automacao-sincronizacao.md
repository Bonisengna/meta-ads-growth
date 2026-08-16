# Fase 6 — Automação da sincronização

## Objetivo

Eliminar a execução manual conta por conta. Um comando percorre todas as contas
`ACTIVE`, atualiza a hierarquia Meta e reprocessa as métricas recentes,
incluindo o dia atual.

## 1. Aplicar a migration

Antes da primeira execução, aplique no SQL Editor do Supabase:

```text
supabase/migrations/0007_sync_runs.sql
```

A migration cria `sync_runs`, habilita RLS, bloqueia `anon` e `authenticated`,
e concede acesso somente ao backend por `service_role`. Ela também cria uma
restrição única para existir apenas uma execução `RUNNING` por escopo.

## 2. Configuração

Valores padrão disponíveis no `backend/.env`:

```env
META_SYNC_LOOKBACK_DAYS=3
META_SYNC_MAX_ATTEMPTS=3
META_SYNC_RETRY_DELAY_SECONDS=2
META_SYNC_LOCK_MINUTES=120
```

- `LOOKBACK_DAYS=3`: atualiza hoje e os dois dias anteriores;
- `MAX_ATTEMPTS=3`: limita novas tentativas de erros temporários;
- `RETRY_DELAY_SECONDS=2`: espera 2, depois 4 segundos;
- `LOCK_MINUTES=120`: considera abandonada uma execução que excedeu duas horas.

Erros permanentes, como token inválido, não são repetidos. HTTP 408, 425, 429,
erros de rede e respostas 5xx usam espera exponencial.

## 3. Teste manual do comando único

Execute a partir de `backend/`:

```powershell
.\.venv\Scripts\python.exe scripts\sync_meta_all.py
```

Para uma janela diferente:

```powershell
.\.venv\Scripts\python.exe scripts\sync_meta_all.py --lookback-days 7
```

A saída informa o status geral e o resultado de cada conta. Códigos de saída:

- `0`: `SUCCESS`;
- `1`: falha geral;
- `2`: `PARTIAL`;
- `3`: execução ignorada porque outra sincronização está ativa.

## 4. Agendamento diário no Windows

Depois do teste manual aprovado, abra o PowerShell no diretório `backend/` e
registre a tarefa para 03:00:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\install_windows_sync_task.ps1 -DailyAt "03:00"
```

Teste a tarefa sem esperar o horário:

```powershell
Start-ScheduledTask -TaskName "DescompliADS Meta Sync"
Get-ScheduledTaskInfo -TaskName "DescompliADS Meta Sync"
```

Esse agendamento é adequado ao ambiente local inicial. Na VPS, a Fase 9 deve
substituí-lo por um serviço/agendador do servidor.

## Protocolo de execução

Cada linha de `sync_runs` registra início, fim, duração, janela reprocessada,
quantidade de contas bem-sucedidas ou com falha e um resumo JSON. Mensagens de
erro são limitadas e valores com nomes de token/segredo são mascarados.

Status possíveis:

- `RUNNING`: execução em andamento;
- `SUCCESS`: todas as contas terminaram;
- `PARTIAL`: pelo menos uma conta terminou e outra falhou;
- `FAILED`: nenhuma conta terminou ou ocorreu falha geral.

## Analogia

O comando é o carteiro, o agendador é o horário fixo da rota, `sync_runs` é o
livro de protocolo e a trava é a placa “carteiro em rota”. O reprocessamento
dos últimos dias permite substituir entregas provisórias pelos números finais
ajustados pela atribuição da Meta.
