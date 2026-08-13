# Módulo de Rastreamento de Leads

Status: **planejado**.

## Objetivo

Ligar mídia ao resultado comercial real:

```text
anúncio → conversa → lead identificado → qualificado → agendamento → proposta → venda
```

O módulo deverá responder qual campanha, conjunto e anúncio originaram cada etapa e permitir calcular custo por qualificado, agendamento, proposta e venda.

## Princípio

O CRM/atendimento continua sendo dono dos dados pessoais. O módulo de Meta Ads não precisa duplicar nome e telefone; guarda principalmente IDs e eventos:

```text
lead_id
sessao_id
conta_anuncio
id_campanha
id_conjunto
id_anuncio
origem_atribuicao
confianca_atribuicao
eventos do funil
```

## Banco

Migration:

```text
database/004-cria-rastreamento-leads.sql
```

Ela cria:

### meta_lead_atribuicao

Uma atribuição primária por lead, com IDs de Meta Ads, origem da evidência, confiança e dados brutos de origem.

### meta_lead_eventos

Histórico imutável do funil:

```text
conversa_iniciada
lead_identificado
lead_qualificado
agendamento
proposta
venda
desqualificado
```

Não devemos apenas sobrescrever um campo de status. O histórico permite medir tempo entre etapas e reconstruir o funil.

## Atribuição inicial

Prioridade de evidência:

```text
1. IDs de campanha/conjunto/anúncio recebidos explicitamente
2. metadata/referral de origem quando disponível
3. UTM ou link rastreado
4. associação manual confirmada
5. desconhecida
```

Confiança:

```text
alta
media
baixa
desconhecida
```

Regra crítica: **não inventar atribuição**. Se não houver evidência, registrar `desconhecida`. Um lead não deve ser atribuído a um anúncio apenas porque entrou enquanto a campanha estava ativa.

## Contrato de entrada planejado

```json
{
  "lead_id": "LEAD_123",
  "sessao_id": "SESSAO_456",
  "evento": "lead_qualificado",
  "ocorrido_em": "2026-08-13T17:30:00-03:00",
  "score_qualificacao": 82,
  "atribuicao": {
    "conta_anuncio": "742175035567342",
    "id_campanha": "120000000000001",
    "id_conjunto": "120000000000002",
    "id_anuncio": "120000000000003",
    "origem_atribuicao": "meta_referral",
    "confianca_atribuicao": "alta",
    "chave_origem": "TOKEN_ORIGEM"
  }
}
```

Depois que o lead estiver atribuído, os próximos eventos usam o mesmo `lead_id` e não precisam repetir toda a origem.

## Workflow n8n planejado

Nome:

```text
META ADS | 05 | RASTREAMENTO DE LEADS
```

Estrutura:

```text
RECEBE EVENTO DO LEAD
        ↓
NORMALIZA IDENTIDADE DO LEAD
        ↓
VALIDA EVENTO DO FUNIL
        ↓
RESOLVE ATRIBUIÇÃO DO ANÚNCIO
        ↓
BUSCA ATRIBUIÇÃO EXISTENTE
        ↓
REGISTRA / ATUALIZA ATRIBUIÇÃO
        ↓
REGISTRA EVENTO DO FUNIL
        ↓
ATUALIZA MÉTRICAS DE QUALIDADE
```

## Separação de responsabilidades

```text
Rastreamento
lead → anúncio

Qualidade
lead → qualificado/agendado/venda

Performance
impressões/cliques/conversas/custos

Motor de Decisão
performance + tendência + fadiga + qualidade
```

## Views já planejadas

A migration cria:

```text
v_meta_lead_funil
```

Uma linha consolidada por lead.

E:

```text
v_meta_ads_funil_diario
```

Agrupada por data e IDs de Meta Ads, com:

```text
leads atribuídos
leads identificados
leads qualificados
agendamentos
propostas
vendas
desqualificados
valor de vendas
```

## Métricas futuras

Ao cruzar essa view com `meta_ads_metricas_diarias` teremos:

```text
custo por lead identificado
custo por lead qualificado
custo por agendamento
custo por proposta
custo por venda
taxa de qualificação
taxa de agendamento
taxa de venda
receita atribuída
```

Exemplo:

```text
Anúncio A
20 conversas × R$ 5 = R$ 100
2 qualificados → R$ 50 por qualificado

Anúncio B
10 conversas × R$ 8 = R$ 80
7 qualificados → R$ 11,43 por qualificado
```

O anúncio com conversa mais cara pode ser muito melhor para o negócio.

## Implantação

### A — Identidade

Definir o `lead_id` oficial compartilhado entre atendimento, CRM e módulo Meta Ads.

### B — Origem

Preservar no primeiro contato toda evidência de origem antes de transformar o payload.

### C — Eventos

Os workflows de atendimento enviam evento sempre que o lead avançar ou for desqualificado.

### D — Métricas

Cruzar `v_meta_ads_funil_diario` com `meta_ads_metricas_diarias`.

### E — Qualidade

Alimentar a futura Fase 4 e o Motor de Decisão com qualificação, agendamento e venda.

## Regras

- não duplicar o cadastro completo do lead;
- não atribuir apenas por horário aproximado;
- não tratar conversa como lead qualificado;
- não apagar eventos antigos quando o status mudar;
- não deixar IA inferir a origem sem evidência;
- não misturar dados de teste com dados reais.

## Ordem no roadmap

```text
FASE 1  Coleta diária
FASE 2  Performance
FASE 3  Tendência e fadiga
MÓDULO  Rastreamento de leads
FASE 4  Qualidade dos leads
FASE 5  Motor de decisão
```

Assim a Fase 4 começa com a atribuição já definida, sem redesenhar o banco.
