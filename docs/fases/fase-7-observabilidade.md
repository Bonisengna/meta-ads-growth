# Fase 7 — Observabilidade e tratamento de falhas

## Objetivo

Detectar falhas da integração Meta antes que o dashboard fique desatualizado.

## Endpoint operacional

```http
GET /health/meta
GET /api/v1/health/meta
```

Estados:

- `HEALTHY`: última execução concluída e contas atualizadas;
- `DEGRADED`: execução parcial/em andamento ou conta atrasada;
- `UNHEALTHY`: última execução falhou, não existe execução ou o token expirou;
- `UNCONFIGURED`: credencial Meta ausente no ambiente.

Respostas diferentes de `HEALTHY` usam HTTP 503 para integração com monitores.
O endpoint consulta o protocolo local no Supabase e não consome a Graph API.

## Contas atrasadas

`META_HEALTH_STALE_HOURS=26` define a tolerância desde
`last_metrics_synced_at`. O valor de 26 horas oferece uma margem de duas horas
para uma tarefa diária. O sistema mantém datas distintas para entidades,
métricas e conclusão total; assim, uma atualização de nomes ou status não
oculta uma falha na coleta de desempenho.

Se as métricas principais forem gravadas e apenas um detalhamento opcional
falhar, a conta e a execução ficam como `PARTIAL`. Os números principais
continuam disponíveis, acompanhados de um aviso de coleta parcial no frontend.

## Alertas de token

A migration `0008_integration_alerts.sql` cria alertas operacionais protegidos
por RLS. Quando a Meta retorna o código 190, a sincronização abre um alerta
`TOKEN_EXPIRED`. Uma execução posterior bem-sucedida resolve o alerta.

Mensagens armazenadas passam por mascaramento e não incluem tokens ou segredos.

## Relatório de entidades

Cada execução agora consolida, por nível:

```json
{
  "campaigns": {
    "imported": 1,
    "updated": 10,
    "archived": 1
  }
}
```

`imported` significa novo registro, `updated` significa entidade já conhecida
recebida novamente e `archived` significa entidade histórica que deixou de
operar. Nenhuma entidade histórica é apagada.

## Analogia

`sync_runs` é o livro de protocolo, `integration_alerts` é o painel de alarmes
e `/health/meta` é a luz da central: verde, amarela ou vermelha.
