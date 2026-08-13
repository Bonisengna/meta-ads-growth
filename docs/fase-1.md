# Fase 1 — Coleta de Dados

Status: **implementada em desenvolvimento e aguardando teste no n8n**.

## Workflow para teste

```text
workflows/01-coleta-diaria-meta-ads-v2.json
```

A versão sem `v2` fica mantida apenas como histórico da primeira implementação.

## Alterações realizadas

- coleta somente do dia anterior;
- timezone `America/Sao_Paulo`;
- granularidade diária com `time_increment = 1`;
- coleta separada por campanha, conjunto e anúncio;
- correção do CPC dos conjuntos;
- `account_id` solicitado explicitamente na Meta;
- criação da chave `CHAVE REGISTRO`;
- gravação no Sheets com `Append or Update Row` usando a chave como correspondência;
- nomes dos nodes em português claro;
- comentários breves nos nodes de código.

## Chave única

Formato:

```text
data|conta|nivel|id_objeto
```

Exemplo:

```text
2026-08-12|742175035567342|anuncio|120238203537350438
```

Reexecutar o mesmo dia e objeto deve atualizar a linha existente em vez de criar outra.

## Google Sheets

As três abas históricas foram preservadas e receberam a coluna:

```text
CHAVE REGISTRO
```

Os registros legados permanecem sem chave. As análises da nova base diária deverão considerar apenas registros com `CHAVE REGISTRO` preenchida.

## Banco principal

Decisão arquitetural:

```text
Supabase / PostgreSQL = banco principal
Google Sheets = visualização e exportação
```

A migration está em:

```text
database/001-cria-metricas-meta-ads.sql
```

Ela ainda não foi aplicada em banco de produção.

## Teste obrigatório no n8n

1. Importar `01-coleta-diaria-meta-ads-v2.json`.
2. Conferir as credenciais da Meta e Google Sheets.
3. Manter o workflow desativado.
4. Executar manualmente uma vez.
5. Confirmar que os dados são somente do dia anterior.
6. Confirmar `CHAVE REGISTRO` preenchida nos três níveis.
7. Conferir o CPC de um conjunto com a Meta.
8. Executar novamente.
9. Confirmar que nenhuma linha duplicada foi criada.
10. Só depois ativar o agendamento diário.

## Critério de conclusão

- [x] CPC dos conjuntos corrigido.
- [x] Coleta diária definida.
- [x] Timezone definido.
- [x] Chave única criada.
- [x] Migration PostgreSQL criada.
- [x] Sheets preparado com chave.
- [ ] Workflow importado no n8n.
- [ ] Primeira execução aprovada.
- [ ] Segunda execução sem duplicação aprovada.
- [ ] CPC conferido com dado real da Meta.
- [ ] Agendamento diário ativado.

## Fora do escopo desta fase

A separação entre `LEAD` e `CONVERSA INICIADA` será feita posteriormente, junto com a integração do funil comercial. A Fase 1 também não executa alterações automáticas de orçamento ou status das campanhas.
