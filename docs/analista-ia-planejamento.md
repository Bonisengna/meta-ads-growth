# Analista IA — Planejamento

Status: planejado e em implementação na branch `desenvolvimento`.

## Escopo

Os módulos `05 | HUB DE EVENTOS DE LEADS` e `06 | FEEDBACK PARA META` ficam fora desta etapa.

O Analista IA recebe apenas dados produzidos pelas camadas atuais de mídia:

- `02 | MOTOR DE PERFORMANCE`;
- `04 | TENDÊNCIA E FADIGA`.

A saída do `03 | SAÍDA PARA O GESTOR` não será usada como entrada da IA para evitar analisar texto já interpretado.

## Objetivo

A IA não recalcula métricas e não executa ações na Meta. Ela deve:

1. interpretar os sinais determinísticos;
2. cruzar performance atual com tendência/fadiga;
3. priorizar problemas e oportunidades;
4. propor hipóteses de teste;
5. explicar o motivo usando números recebidos;
6. indicar o que ainda não possui evidência suficiente.

## Arquitetura

```text
02 MOTOR DE PERFORMANCE ─┐
                         ├─> PACOTE DE ANÁLISE ─> ANALISTA IA ─> SAÍDA ESTRUTURADA
04 TENDÊNCIA E FADIGA ───┘                              ↓
                                                   BRIEFING GESTOR
```

## Regras

- IA não inventa números;
- IA não usa `PAUSAR` ou `ESCALAR` como execução automática;
- recomendações críticas são sempre apresentadas como sugestão para o gestor;
- cálculos permanecem nos motores determinísticos;
- objetos com amostra insuficiente não recebem recomendação agressiva;
- a IA deve explicar cada recomendação com evidências do pacote recebido;
- o payload enviado ao modelo deve ser reduzido antes da chamada.

## Workflow

Arquivo planejado:

```text
workflows/08-analista-ia.json
```

O número 08 preserva 05/06 para o módulo independente de CRM e 07 para públicos, sem torná-los dependências desta análise.
