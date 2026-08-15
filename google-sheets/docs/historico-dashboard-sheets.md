# Histórico de Análises IA e Dashboard no Google Sheets

Status: estrutura inicial implementada e aguardando teste do workflow 09 no n8n.

## Objetivo

Cada conta Meta Ads terá uma planilha própria. A planilha funciona simultaneamente como:

- histórico bruto das métricas já existentes;
- histórico estruturado das análises da IA;
- histórico das prioridades recomendadas;
- dashboard gerencial dentro do próprio Google Sheets.

Os módulos 05/06 de tracking e feedback para Meta ficam fora desta etapa.

## Arquitetura

```text
02 | MOTOR DE PERFORMANCE ───┐
                             ├── pacote de análise
04 | TENDÊNCIA E FADIGA ─────┘
             ↓
08 | ANALISTA IA
             ↓
pacote_analise + analise_ia + briefing_gestor
             ↓
09 | HISTÓRICO E DASHBOARD SHEETS
          ↙       ↘
 ANALISES IA   PRIORIDADES IA
          \       /
           DASHBOARD
```

## Uma planilha por conta

A regra é:

```text
1 conta Meta = 1 arquivo Google Sheets
```

Isso evita misturar dados de clientes e simplifica permissões, filtros, fórmulas e compartilhamento.

Para uma nova conta:

1. duplique a planilha-template;
2. mantenha os nomes das abas;
3. altere `PLANILHA_ID` e `CONTA` no node `DEFINE CONTA E PLANILHA` do workflow 09;
4. configure a credencial Google Sheets adequada;
5. conecte a saída completa do Analista IA ao workflow 09.

## Abas

### CONFIG

Guarda parâmetros do arquivo:

```text
CHAVE_CONTA
ID_CONTA_META
MOEDA
TIMEZONE
PLANILHA_ID
FREQUENCIA_ANALISE
```

Não deve guardar tokens ou segredos.

### ANALISES IA

Uma linha por execução válida do Analista IA.

Colunas:

```text
CHAVE ANALISE
DATA REFERENCIA
GERADO EM
CONTA
SAUDE CONTA
CONFIANCA ANALISE
RESUMO EXECUTIVO
INVESTIMENTO TOTAL
CONVERSAS
CUSTO MEDIO CONVERSA
SCORE TECNICO MEDIO
QTD OBJETOS
FADIGA ALTA
FADIGA MODERADA
OBSERVAR
MELHORA
DADOS INSUFICIENTES
QTD PRIORIDADES
PRIORIDADE PRINCIPAL
ACAO PRINCIPAL
BRIEFING GESTOR
PARSER
```

A aba é append-only no conceito. A chave inclui conta + data de referência + timestamp da execução.

### PRIORIDADES IA

Uma linha por prioridade produzida na análise.

Colunas:

```text
CHAVE PRIORIDADE
CHAVE ANALISE
DATA REFERENCIA
CONTA
ORDEM
NIVEL
NOME OBJETO
ACAO RECOMENDADA
DIAGNOSTICO
MOTIVO
EVIDENCIAS
REAVALIAR EM DIAS
STATUS GESTOR
OBSERVACAO GESTOR
ATUALIZADO EM
```

`STATUS GESTOR` e `OBSERVACAO GESTOR` foram previstos para acompanhamento humano posterior.

### DASHBOARD

Painel inicial com:

- saúde atual;
- confiança da análise;
- score técnico médio;
- custo por conversa;
- investimento;
- conversas;
- quantidade de fadigas altas;
- quantidade de prioridades;
- resumo executivo mais recente;
- prioridade principal;
- ação principal;
- data da análise;
- timestamp da análise.

Gráficos iniciais:

1. evolução do score técnico;
2. evolução do custo por conversa;
3. fadiga alta versus quantidade de prioridades por análise.

Os gráficos usam diretamente a aba `ANALISES IA`.

## Workflow 09

Arquivo:

```text
workflows/09-historico-dashboard-sheets.json
```

Nome:

```text
META ADS | 09 | HISTÓRICO E DASHBOARD SHEETS
```

Fluxo:

```text
RECEBE ANÁLISE COMPLETA
        ↓
DEFINE CONTA E PLANILHA
       ↙               ↘
PREPARA HISTÓRICO   PREPARA PRIORIDADES
       ↓               ↓
SALVA ANÁLISE       SALVA PRIORIDADES
NO SHEETS           NO SHEETS
```

Há também um `TESTE MANUAL` com dados fictícios.

## Contrato de entrada

O workflow espera:

```json
{
  "pacote_analise": {
    "data_referencia": "2026-08-13",
    "performance": {
      "investimento_total": 150,
      "conversas_iniciadas": 15,
      "custo_medio_por_conversa": 10,
      "score_tecnico_medio": 46
    },
    "tendencia": {
      "quantidade_objetos": 3,
      "fadiga_alta": [],
      "fadiga_moderada": [],
      "observar": [],
      "melhora": [],
      "dados_insuficientes": []
    }
  },
  "status_analise_ia": "OK",
  "parser_usado": "CODE_MANUAL_V3",
  "analise_ia": {
    "resumo_executivo": "...",
    "saude_conta": "atencao",
    "confianca_analise": "alta",
    "prioridades": []
  },
  "briefing_gestor": "..."
}
```

## Por que não salvar apenas o briefing

Texto é bom para leitura humana, mas ruim para dashboard.

Por isso salvamos simultaneamente:

```text
texto para o gestor
+
campos estruturados para gráficos e filtros
```

Exemplo:

```text
SAUDE CONTA = ATENCAO
SCORE TECNICO MEDIO = 46
FADIGA ALTA = 2
QTD PRIORIDADES = 3
ACAO PRINCIPAL = REVISAR_CRIATIVO
```

O dashboard trabalha com esses campos, não com interpretação de texto.

## Próxima integração

O próximo passo é criar o orquestrador que preserve o pacote original dos motores 02/04, envie-o ao Analista IA 08 e depois entregue o pacote completo ao workflow 09.

```text
02 + 04
  ↓
ORQUESTRADOR
  ↓
08 IA
  ↓
MERGE pacote original + resposta IA
  ↓
09 SHEETS
```

Assim nenhum dado determinístico é perdido depois da chamada ao modelo.
