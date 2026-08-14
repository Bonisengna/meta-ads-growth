# META ADS | 08 | ANALISTA IA

Status: **implementado em `desenvolvimento` e aguardando teste no n8n**.

## Escopo

O Analista IA usa apenas:

```text
02 | MOTOR DE PERFORMANCE
04 | TENDÊNCIA E FADIGA
```

Ficam fora desta etapa:

```text
05 | HUB DE EVENTOS DE LEADS
06 | FEEDBACK PARA META
07 | PÚBLICOS
```

O `03 | SAÍDA PARA O GESTOR` também não é usado como entrada porque já contém interpretação/apresentação. A IA deve analisar fatos estruturados dos motores, não texto previamente resumido.

## Arquivo

```text
workflows/08-analista-ia.json
```

## Contrato de entrada

O workflow espera um único item:

```json
{
  "performance": {
    "status_motor": "OK",
    "data_referencia": "2026-08-12",
    "investimento_total": 150,
    "conversas_iniciadas": 15,
    "custo_medio_por_conversa": 10,
    "score_tecnico_medio": 46,
    "melhores_resultados": [],
    "resultados_para_atencao": []
  },
  "tendencia": {
    "status_tendencia": "OK",
    "data_referencia": "2026-08-12",
    "fadiga_alta": [],
    "fadiga_moderada": [],
    "observar": [],
    "melhora": [],
    "dados_insuficientes": []
  }
}
```

## Fluxo

```text
RECEBE PACOTE DE ANÁLISE
        ↓
VALIDA E REDUZ PACOTE
        ↓
PACOTE PRONTO PARA IA?
        ↓ SIM
MONTA PROMPT DE ANÁLISE
        ↓
ANALISTA IA META ADS
   ↙             ↘
MODELO         PARSER
        ↓
VALIDA SAÍDA DA IA
        ↓
MONTA BRIEFING DO GESTOR
```

Existe também:

```text
TESTE MANUAL
   ↓
GERA PACOTE DE TESTE
```

para validar sem depender dos fluxos 02 e 04.

## Papel da IA

A IA pode:

- explicar o que os números sugerem;
- cruzar performance atual com fadiga/tendência;
- priorizar problemas;
- destacar oportunidades;
- criar hipóteses de teste;
- indicar quais dados ainda são insuficientes.

A IA não pode:

- recalcular métricas;
- inventar números;
- afirmar uma causa quando existe apenas correlação;
- pausar campanhas;
- aumentar orçamento;
- alterar anúncios;
- depender dos módulos 05/06 nesta versão.

## Ações permitidas na análise

```text
MANTER
OBSERVAR
REVISAR_CRIATIVO
REVISAR_PUBLICO
REVISAR_OFERTA
TESTAR_VARIACAO
CANDIDATO_ESCALA
REDUZIR_EXPOSICAO
```

`CANDIDATO_ESCALA` significa somente que o gestor deve avaliar a oportunidade. Não significa autorização para alterar orçamento.

## Saída estruturada

O Structured Output Parser exige um objeto com:

```text
resumo_executivo
saude_conta
confianca_analise
prioridades[]
oportunidades[]
riscos[]
hipoteses_teste[]
nao_fazer[]
```

Depois, `VALIDA SAÍDA DA IA` aplica uma segunda proteção determinística, limitando quantidade de prioridades e restringindo o conjunto de ações aceitas.

## Redução do payload

O node `VALIDA E REDUZ PACOTE` envia ao modelo apenas:

- totais principais da conta;
- até 5 melhores resultados;
- até 5 resultados para atenção;
- até 5 itens por classificação de tendência/fadiga.

A IA não recebe todas as linhas históricas das planilhas.

## Teste esperado

O teste manual contém:

```text
ANUNCIO_A
performance forte + tendência de melhora

ANUNCIO_B
performance fraca + fadiga alta

ANUNCIO_C
performance fraca + sinal de observação
```

A saída exata da IA não é determinística, mas estruturalmente esperamos:

- `ANUNCIO_B` entre as maiores prioridades;
- `ANUNCIO_A` como oportunidade ou manutenção/candidato a escala;
- `ANUNCIO_C` tratado com cautela;
- nenhuma ação automática;
- briefing final em português.

## Configuração no n8n

Depois de importar:

1. abrir `MODELO DE LINGUAGEM`;
2. selecionar a credencial do provedor/modelo;
3. manter temperatura baixa;
4. executar pelo `TESTE MANUAL`;
5. conferir `VALIDA FORMATO DA ANÁLISE`;
6. conferir `VALIDA SAÍDA DA IA`;
7. conferir `MONTA BRIEFING DO GESTOR`.

Não ativar integração automática antes do teste.

## Próxima integração

Depois da validação do Fluxo 08, criar uma camada de orquestração que reúna as saídas dos fluxos 02 e 04 em um único pacote:

```text
02 PERFORMANCE ─┐
                ├─> ORQUESTRADOR ─> 08 ANALISTA IA
04 TENDÊNCIA ───┘
```

A saída do Analista IA poderá então alimentar uma nova versão do painel do gestor/Telegram.

Essa integração deve manter 05/06 fora do caminho enquanto o módulo de leads não estiver sendo usado.
