# Fase 2 — Saída para o Gestor

Status: **implementada em desenvolvimento e aguardando teste no n8n**.

## Workflow

```text
workflows/03-saida-gestor.json
```

## Objetivo

Transformar a saída técnica do `META ADS | 02 | MOTOR DE PERFORMANCE` em um briefing curto para o gestor.

Esta camada **não recalcula a performance** e **não executa alterações na Meta**. Ela apenas organiza e apresenta os resultados já calculados.

## Fluxo

Produção:

```text
MOTOR DE PERFORMANCE
        ↓
RECEBE MOTOR DE PERFORMANCE
        ↓
CLASSIFICA RESULTADOS PARA O GESTOR
        ↓
MONTA PAINEL DO GESTOR
        ↓
PREPARA MENSAGEM PARA TELEGRAM
        ↓
ENVIA PAINEL AO GESTOR
```

Teste:

```text
TESTE MANUAL
        ↓
GERA RESUMO DE TESTE
        ↓
CLASSIFICA RESULTADOS PARA O GESTOR
        ↓
MONTA PAINEL DO GESTOR
        ↓
PREPARA MENSAGEM PARA TELEGRAM
        ↓
ENVIA PAINEL AO GESTOR
```

## Classificações

### DESTAQUE

```text
score >= 70
+ amostra mínima
```

Indica boa eficiência técnica. Nesta fase o sistema apenas recomenda manter e acumular evidência. Não aumenta orçamento automaticamente.

### SAUDÁVEL

```text
score entre 55 e 69
+ amostra mínima
```

Indica resultado tecnicamente saudável.

### OBSERVAR

```text
score entre 40 e 54
+ amostra mínima
```

Indica que ainda não há motivo claro para intervenção, mas o objeto merece acompanhamento.

### ATENÇÃO

```text
score < 40
+ amostra mínima
```

Indica que o gestor deve revisar o objeto antes de aumentar investimento.

### DADOS INSUFICIENTES

A primeira regra de amostra da versão inicial é:

```text
conversas >= 2
OU
cliques no link >= 20
```

Quando nenhum dos dois critérios é atingido, o sistema não usa o score para recomendar ação e classifica como `DADOS INSUFICIENTES`.

Esses limites são provisórios e deverão ser ajustados depois que houver histórico real suficiente.

## Saída do Telegram

Formato aproximado:

```text
PAINEL META ADS — 2026-08-12
Investimento: R$ 128,00
Conversas: 22
Custo médio/conversa: R$ 5,82
Score técnico médio: 46

DESTAQUES
1. Anúncio: ANUNCIO_A
Score 90 | 12 conversas | R$ 4,17/conversa | CTR link 2,50%
Ação: Manter. É candidato a teste de escala quando o Motor de Decisão estiver ativo.

ATENÇÃO
1. Anúncio: ANUNCIO_B
Score 28 | 7 conversas | R$ 6,00/conversa | CTR link 1,60%
Ação: Revisar criativo, público e oferta antes de aumentar investimento.

DADOS INSUFICIENTES
1. Anúncio: ANUNCIO_C
Score 20 | 1 conversa | R$ 36,00/conversa | CTR link 0,70%
Ação: Não tomar decisão ainda. Coletar mais dados.

FOCO DO GESTOR
Revisar primeiro: ANUNCIO_B.
```

## Saída estruturada

Além da mensagem, o workflow mantém o objeto:

```text
painel_gestor
```

com as listas:

```text
destaques
saudaveis
observar
atencao
dados_insuficientes
foco_do_gestor
```

Isso permitirá reutilizar a mesma saída futuramente em dashboard, banco de dados, e-mail, WhatsApp ou camada de IA.

## Comportamento sem dados

Se o Motor de Performance enviar:

```text
SEM_DADOS_DIARIOS
```

o workflow encerra sem enviar mensagem ao Telegram.

Isso evita alertas diários vazios quando não houver campanhas recentes.

## Como testar

1. Importar `workflows/03-saida-gestor.json` no n8n.
2. Conferir a credencial do Telegram no node `ENVIA PAINEL AO GESTOR`.
3. Manter o workflow desativado.
4. Executar pelo node `TESTE MANUAL`.
5. Conferir se o Telegram recebe o painel.
6. Confirmar as classificações esperadas:

```text
ANUNCIO_A → DESTAQUE
ANUNCIO_B → ATENÇÃO
ANUNCIO_C → DADOS INSUFICIENTES
```

7. Confirmar que o foco do gestor é `ANUNCIO_B`.

## Integração com o Motor de Performance

Depois que o teste manual for aprovado:

1. abrir `META ADS | 02 | MOTOR DE PERFORMANCE`;
2. adicionar um node `Execute Workflow` depois de `CONSOLIDA RESUMO DE PERFORMANCE`;
3. selecionar `META ADS | 03 | SAÍDA PARA O GESTOR`;
4. enviar os dados de entrada para o subworkflow;
5. testar a cadeia completa.

A saída do Motor já possui o campo `registros_performance`, que é a entrada esperada pelo workflow de gestor.

## Regra de segurança

Nesta fase nenhuma classificação significa autorização automática para alterar campanha.

```text
DESTAQUE != ESCALAR AUTOMATICAMENTE
ATENÇÃO != PAUSAR AUTOMATICAMENTE
```

As decisões de orçamento e status pertencem ao futuro Motor de Decisão.
