# Gate 1 — Confiança e semântica dos dados

## Objetivo

Garantir que os números exibidos ao gestor tenham origem, fórmula,
disponibilidade e atualização compreensíveis antes de novas funcionalidades.
Este gate não inclui IA, CRM ou Webhooks.

## Contrato do dashboard

`GET /api/v1/dashboard` inclui `data_confidence` com:

- moeda e fuso horário da conta filtrada;
- data máxima encontrada no período e horários das últimas sincronizações;
- aviso quando o período contém o dia atual, ainda parcial;
- atribuição da conta Meta e registro da ação por impressão;
- confirmação de que entidades `ARCHIVED` continuam no histórico;
- catálogo das fórmulas e da disponibilidade de cada indicador;
- alertas para moedas/fusos mistos, coleta ausente ou atrasada e LPV ausente.

## Regras de agregação

São somáveis entre dias e entidades:

- investimento;
- impressões;
- cliques e cliques no link;
- leads, conversas e visualizações da página;
- eventos de vídeo.

CTR, CPC, CPM, CPL e taxas do funil são recalculados a partir dos totais, em
vez de usar média simples das taxas diárias.

Alcance representa pessoas únicas e frequência depende desse alcance. Portanto,
ambos são não aditivos. O dashboard só os mantém quando o recorte corresponde a
uma única linha exata; em agregações de vários dias ou campanhas devolve `null`
e explica a indisponibilidade. A reconciliação consulta alcance e frequência
diretamente na Meta como referência do período, sem somar valores diários.

## Atribuição

As consultas de Insights enviam explicitamente:

```text
use_account_attribution_setting=true
action_report_time=impression
```

Assim, o DescompliADS respeita a janela configurada na conta de anúncios e
mantém a conversão no dia da impressão que recebeu a atribuição.

## Reconciliação assistida

A comparação é somente leitura e não exibe o token:

```powershell
cd C:\Projetos\meta-ads-growth\backend
.\.venv\Scripts\python.exe scripts\reconcile_meta.py 742175035567342
```

O comando confere 7, 30, 180 e 360 dias. `MATCH` significa igualdade nas
métricas aditivas. `MATCH_NO_DATA` significa que Meta e Supabase estão ambos
zerados no período. `MISMATCH` identifica a métrica e a diferença exata.

Quando houver divergência, reprocessar o histórico e repetir a conferência:

```powershell
.\.venv\Scripts\python.exe scripts\sync_meta_all.py --lookback-days 360
.\.venv\Scripts\python.exe scripts\reconcile_meta.py 742175035567342
```

## Evidência de aceite

Em 30/08/2026, a conta `CONTACAZA85_1` foi reconciliada:

- 7, 30 e 180 dias: `MATCH_NO_DATA`;
- 360 dias: `MATCH`;
- investimento: 468,73 em ambos;
- impressões: 104.429 em ambos;
- cliques: 3.512 em ambos;
- cliques no link: 2.930 em ambos;
- conversas: 51 em ambos.

A sincronização histórica gravou as métricas principais e ficou `PARTIAL`
somente nos detalhamentos por hora porque a Meta retornou limite temporário de
requisições. Esse detalhe pode ser reprocessado pela próxima coleta automática.
