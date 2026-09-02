# Gate 2 — Confiabilidade da sincronização

**Estado final: CONCLUÍDO em 02/09/2026.**

## Contrato operacional

A coleta automática roda no worker separado da API, diariamente às 03:00 no
fuso `America/Sao_Paulo`. Cada ciclo revisa o dia atual e os dois dias
anteriores. Isso absorve ajustes tardios de atribuição sem duplicar dados,
porque entidades e métricas continuam usando UPSERT.

A migration obrigatória deste gate é:

```text
supabase/migrations/0020_sync_control.sql
supabase/migrations/0021_sync_control_indexes.sql
```

Ela adiciona progresso às linhas de `sync_runs` e cria `sync_requests`, a fila
persistente dos pedidos feitos pelo painel. As duas tabelas têm RLS, não são
acessíveis por `anon` ou `authenticated` e ficam restritas à `service_role`.

## Estados visíveis

- `PENDING`: pedido persistido e aguardando o worker;
- `RUNNING`: coleta em andamento;
- `SUCCESS`: todas as contas e etapas foram concluídas;
- `PARTIAL`: métricas essenciais foram preservadas, mas uma conta ou um
  detalhamento falhou;
- `FAILED`: nenhuma conta foi concluída ou ocorreu falha geral.

O painel mostra a conta em processamento, o progresso, o período, e o total de
contas, campanhas, conjuntos e anúncios importados, atualizados ou arquivados.
Arquivar preserva todo o histórico.

## Coleta manual e backfill

Em **Ajustes → Meta Ads → Atualização dos dados**, selecione o cliente e o
período. O padrão recomendado é 3 dias. Backfills de 7, 30, 90, 180 ou 360
dias devem ser usados para recuperar histórico, não como rotina diária.

O clique em **Sincronizar agora** cria uma linha `PENDING`; não mantém uma
requisição HTTP longa aberta. O worker consulta a fila a cada cinco segundos.
Fechar o navegador não cancela a coleta.

Somente `OWNER`, `ADMIN` ou Superadmin podem solicitar uma coleta. Cada pedido
é limitado ao cliente selecionado. A trava única de `sync_runs` continua
impedindo duas coletas Meta simultâneas, inclusive entre ciclo diário e pedido
manual.

## Retries e alertas

HTTP 408, 425, 429, respostas 5xx e falhas de rede recebem até três tentativas
com espera exponencial. Erros permanentes não são repetidos.

- código Meta 190 abre `TOKEN_EXPIRED`;
- falha de uma conta abre `ACCOUNT_STALE`;
- uma coleta posterior bem-sucedida resolve automaticamente o alerta da conta;
- `/api/v1/health/meta` continua informando contas sem métricas recentes.

Mensagens persistidas passam por mascaramento de token e segredo.

## Recuperação de falha

1. Abra **Ajustes → Meta Ads** e leia a causa registrada.
2. Se houver `TOKEN_EXPIRED`, renove o token no ambiente seguro do worker e
   implante novamente. Nunca cole o token em logs ou mensagens.
3. Confirme que o worker está ativo e que não existe uma execução `RUNNING`
   válida há menos de `META_SYNC_LOCK_MINUTES`.
4. Clique em **Reprocessar execução**. O sistema mantém o mesmo cliente e
   período e liga a nova execução à anterior por `recovery_of`.
5. Aguarde `SUCCESS` ou `PARTIAL` e confira o relatório de alterações.
6. Se a falha persistir, preserve as linhas de `sync_runs` e `sync_requests`
   para diagnóstico; não apague métricas nem entidades.

Uma trava abandonada só é liberada depois do vencimento configurado. A próxima
execução marca a anterior como `FAILED` com a mensagem de trava expirada.

## Validação do gate

Antes de publicar:

```powershell
cd C:\Projetos\meta-ads-growth\backend
.\.venv\Scripts\python.exe -m pytest -q

cd C:\Projetos\meta-ads-growth\frontend
pnpm lint
pnpm build
```

Os testes automatizados devem comprovar três ciclos consecutivos, exclusão
mútua, backfill de 360 dias, retry temporário, resultado parcial, alerta de
token, alerta de conta e recuperação de uma falha simulada.

Em produção, o aceite final requer ciclos reais consecutivos do worker. Esse
tempo de observação não deve ser substituído por um teste unitário. Durante a
observação, acompanhe logs do `meta-worker`, `sync_runs`, `sync_requests` e
`/api/v1/health/meta`.

## Aceite final

Em 02/09/2026, foram confirmados:

- API e worker implantados na VPS;
- endpoints de controle presentes no OpenAPI de produção;
- migrações `0020` e `0021` operantes;
- dez execuções recentes consecutivas em `SUCCESS`;
- execução agendada `7a8e5232-8bb9-4934-b87e-01185cf63719` concluída;
- recuperação da falha `ca114930-ea86-4793-83f7-fc7d9f2ee4a0` pela execução
  `54e51e98-f798-485c-935a-9cf9e0e7370d`, finalizada como `RECOVERY/SUCCESS`;
- atualização da conta ativa sem alertas abertos;
- HTTP `401` no endpoint de execuções sem autenticação;
- PostgreSQL `42501` na tentativa de acesso anônimo à fila;
- nenhuma credencial encontrada nos registros examinados;
- `107` testes de backend, lint e build de produção do frontend aprovados.

Com essas evidências, o Gate 2 foi encerrado e o Gate 3 foi liberado.
