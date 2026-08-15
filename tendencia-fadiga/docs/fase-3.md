# Fase 3 — Tendência e Fadiga

Status: **implementada em desenvolvimento e aguardando teste no n8n**.

## Workflow

```text
workflows/04-tendencia-fadiga.json
```

## Objetivo

Identificar deterioração recente de campanha, conjunto ou anúncio antes que uma média histórica esconda a perda de eficiência.

A Fase 3 não pausa, escala ou altera campanhas. Ela produz sinais estruturados para o gestor e para o futuro Motor de Decisão.

## Execução

Produção:

```text
ANÁLISE DE TENDÊNCIA - 05H20
        ↓
BUSCA HISTÓRICO DE CAMPANHAS
BUSCA HISTÓRICO DE CONJUNTOS
BUSCA HISTÓRICO DE ANÚNCIOS
        ↓
JUNTA HISTÓRICO DIÁRIO
        ↓
CALCULA TENDÊNCIAS E FADIGA
        ↓
CONSOLIDA ALERTAS DE FADIGA
```

Teste:

```text
TESTE MANUAL
        ↓
GERA HISTÓRICO DE TESTE
        ↓
CALCULA TENDÊNCIAS E FADIGA
        ↓
CONSOLIDA ALERTAS DE FADIGA
```

O caminho de produção roda às **05:20**, depois da coleta diária e do Motor de Performance.

## Janelas calculadas

Para cada objeto são calculados dados acumulados em:

```text
3 dias
7 dias
14 dias
30 dias
```

Também são calculados dois comparativos sem sobreposição:

```text
3 dias recentes
VS
7 dias imediatamente anteriores
```

E:

```text
7 dias recentes
VS
7 dias imediatamente anteriores
```

O primeiro serve como alerta rápido. O segundo ajuda a confirmar se a deterioração está se sustentando.

## Indicadores de tendência

O motor acompanha:

- CTR de link;
- CPC;
- custo por conversa;
- taxa clique → conversa;
- frequência média diária;
- investimento médio por dia;
- volume de conversas;
- cobertura de dias com dados.

## Frequência

A coleta diária possui alcance diário. Somar alcance de vários dias não representa alcance único do período.

Por isso, nesta fase usamos:

```text
frequencia_media_diaria = média de (impressões do dia / alcance do dia)
```

Isso serve como indicador de tendência, não como frequência exata do período completo.

Uma versão futura poderá consultar a Meta diretamente para obter a frequência exata de janelas completas.

## Score de fadiga

O score varia de `0` a `100`.

Pesos iniciais:

```text
Queda de CTR de link             até +20
Aumento de CPC                   até +15
Aumento de custo por conversa    até +30
Queda clique → conversa          até +15
Aumento de frequência            até +10
Confirmação na janela de 7 dias  até +10
                                  -------
Total                            até 100
```

Os pesos são iniciais e deverão ser calibrados depois que houver histórico real suficiente.

## Classificação

```text
70–100  FADIGA ALTA
45–69   FADIGA MODERADA
25–44   OBSERVAR
0–24    SAUDÁVEL ou MELHORA
```

Quando existe melhora relevante de custo por conversa ou CTR de link, o objeto pode ser classificado como:

```text
MELHORA
```

## Amostra mínima

A versão inicial exige:

```text
pelo menos 5 dias com dados nos últimos 7 dias
E
pelo menos 5 dias no baseline
E
pelo menos 1.000 impressões nos últimos 7 dias
```

Se isso não for atendido:

```text
DADOS INSUFICIENTES
```

A classificação evita decisões precipitadas sobre anúncios novos ou com pouco volume.

## Teste manual

O node `GERA HISTÓRICO DE TESTE` cria três anúncios fictícios com 30 dias de histórico:

```text
ANUNCIO_ESTAVEL
ANUNCIO_FADIGA
ANUNCIO_MELHORA
```

Resultado esperado aproximado:

```text
ANUNCIO_ESTAVEL
score de fadiga ≈ 0
classificação = SAUDÁVEL

ANUNCIO_FADIGA
score de fadiga ≈ 90
classificação = FADIGA ALTA

ANUNCIO_MELHORA
score de fadiga ≈ 0
classificação = MELHORA
```

## Saída estruturada

O node final entrega:

```text
status_tendencia
quantidade_objetos
fadiga_alta
fadiga_moderada
observar
saudaveis
melhora
dados_insuficientes
prioridade_fadiga
registros_tendencia
```

Cada registro de tendência contém as quatro janelas, variações percentuais, score e ação sugerida.

## Banco de dados

A versão SQL equivalente está em:

```text
database/003-cria-view-tendencia-fadiga.sql
```

Ela ainda não foi aplicada em produção.

## Próxima integração

Depois de validar o workflow no n8n, a saída de tendência deverá ser incorporada à próxima versão da saída do gestor.

O painel passará a combinar:

```text
Performance atual
+
Tendência
+
Fadiga
+
Qualidade do lead
```

A última camada será fornecida pelo módulo de rastreamento de leads planejado em `docs/modulo-rastreamento-leads.md`.
