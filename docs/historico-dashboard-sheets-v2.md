# Histórico e Dashboard Sheets — V2

Versão recomendada para importação:

```text
workflows/09-historico-dashboard-sheets-v2.json
```

A V2 substitui `09-historico-dashboard-sheets.json` para novos testes.

Correção principal:

```text
DEFINE CONTA E PLANILHA
        ↓
gera uma única vez:
- DATA_REFERENCIA
- GERADO_EM
- CHAVE_ANALISE
        ↓
     bifurca
   ↙          ↘
ANALISE       PRIORIDADES
```

Assim a linha de `ANALISES IA` e todas as linhas correspondentes em `PRIORIDADES IA` usam exatamente a mesma `CHAVE ANALISE`.

A estrutura da planilha permanece a descrita em:

```text
docs/historico-dashboard-sheets.md
```

## Planilha atual

A planilha `RELATÓRIOS CAMPANHAS META` já possui:

```text
CAMPANHAS - 2026
CONJUNTOS - 2026
ANUNCIOS - 2026
CONFIG
ANALISES IA
PRIORIDADES IA
DASHBOARD
```

O dashboard foi validado com uma linha fictícia e depois limpo novamente. Ele inicia sem dados exibindo estado neutro e passa a refletir automaticamente a última linha gravada em `ANALISES IA`.

Gráficos atuais:

```text
Evolução do Score Técnico
Evolução do Custo por Conversa
Alertas por Análise
```

Os gráficos usam diretamente `ANALISES IA` como fonte.

## Próximo passo

Criar um orquestrador que preserve o pacote de Performance/Tendência, chame o Analista IA 08 e entregue o resultado completo ao workflow 09 V2.
