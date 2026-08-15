# DescompliADS

Painel de inteligência para gestores de tráfego, focado inicialmente em campanhas do Meta Ads.

O DescompliADS transforma métricas em **diagnóstico, prioridades, recomendações e histórico de melhorias**. O produto não pretende substituir o Gerenciador de Anúncios, nem funcionar como CRM ou sistema de atendimento.

> Princípio do produto: **observar, analisar, recomendar e acompanhar**.

## Repositório

Repositório técnico atual:

**https://github.com/Bonisengna/meta-ads-growth**

O nome do repositório ainda reflete a origem do projeto. O produto passa a ser documentado como **DescompliADS**.

---

## O problema que o produto resolve

Um dashboard tradicional responde:

> O que aconteceu?

O DescompliADS deve avançar para:

- o que aconteceu;
- por que provavelmente aconteceu;
- onde está o problema;
- o que deve ser feito;
- se a melhoria aplicada funcionou.

A proposta é transformar acompanhamento de mídia em um processo contínuo:

```text
MÉTRICAS
   ↓
DIAGNÓSTICO
   ↓
RECOMENDAÇÃO
   ↓
MELHORIA
   ↓
VALIDAÇÃO
   ↓
APRENDIZADO
```

---

## Público inicial

O MVP é voltado para:

- gestores de tráfego;
- operação própria;
- gestores com vários clientes;
- acompanhamento de contas Meta Ads.

A arquitetura poderá evoluir posteriormente para múltiplos usuários, equipes e organizações.

---

## O que o DescompliADS fará

O MVP deverá permitir:

- acompanhar métricas de campanhas;
- comparar períodos;
- acompanhar campanhas, conjuntos e anúncios;
- receber análises produzidas por IA;
- identificar problemas e oportunidades;
- registrar melhorias recomendadas;
- acompanhar melhorias pendentes;
- registrar quando uma melhoria foi aplicada;
- comparar resultados antes e depois;
- criar histórico de decisões e aprendizados por campanha;
- facilitar a gestão de várias contas/clientes.

---

## O que NÃO entra no MVP

Inicialmente não faz parte do escopo:

- criação de campanhas;
- edição de campanhas;
- alteração de orçamento;
- upload de criativos;
- criação de públicos;
- edição de anúncios;
- substituição do Gerenciador de Anúncios;
- CRM;
- atendimento de leads;
- WhatsApp;
- gestão de conversas.

O DescompliADS será um sistema de **acompanhamento e inteligência**, não uma ferramenta de operação direta no Meta Ads.

---

## Arquitetura alvo

```text
META GRAPH API
      ↓
     n8n
      ↓
   SUPABASE
      ↓
FASTAPI / PYTHON
      ↓
   NEXT.JS
      ↓
 DESCOMPLIADS
```

### Meta Graph API

Fonte das informações de mídia, como:

- contas;
- campanhas;
- conjuntos de anúncios;
- anúncios;
- investimento;
- impressões;
- alcance;
- cliques;
- CTR;
- CPC;
- CPM;
- conversões;
- leads;
- conversas;
- demais métricas disponíveis.

### n8n

Continua sendo o motor de automação.

Responsabilidades planejadas:

- buscar dados da Meta Graph API;
- executar coletas periódicas;
- normalizar respostas;
- gravar dados;
- preparar contexto para IA;
- executar análises;
- gravar diagnósticos;
- gerar alertas;
- disparar processos automáticos.

O n8n não deve se tornar o backend principal do SaaS.

### Supabase

Camada prevista para:

- PostgreSQL;
- armazenamento de métricas;
- histórico;
- clientes;
- contas Meta;
- campanhas;
- análises de IA;
- recomendações;
- melhorias;
- alertas;
- autenticação futura.

### FastAPI

Backend do produto em Python.

Responsabilidades:

- fornecer API REST;
- centralizar regras de negócio;
- calcular indicadores;
- consolidar dados;
- comparar períodos;
- controlar acesso aos dados;
- preparar respostas para o frontend;
- futuramente executar análises estatísticas avançadas.

### Next.js

Frontend responsável por:

- dashboard;
- filtros;
- gráficos;
- navegação;
- clientes;
- campanhas;
- análises;
- melhorias;
- alertas;
- configurações.

---

## Estrutura técnica prevista

```text
DescompliADS/
├── frontend/
│   └── Next.js
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   │   ├── dashboard.py
│   │   │   ├── clients.py
│   │   │   ├── campaigns.py
│   │   │   ├── analyses.py
│   │   │   └── improvements.py
│   │   ├── models/
│   │   ├── services/
│   │   ├── database/
│   │   └── config/
│   ├── tests/
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── n8n/
│   └── fluxos e exportações
├── docs/
└── README.md
```

---

## Modelo inicial de dados

Tabelas previstas:

```text
clients
meta_accounts
campaigns
adsets
ads
campaign_metrics
adset_metrics
ad_metrics
ai_analyses
recommendations
improvements
alerts
```

Possíveis tabelas futuras:

```text
creatives
benchmarks
reports
users
organizations
```

---

## Hierarquia Meta Ads

O produto deve respeitar os três níveis:

```text
CAMPANHA
   ↓
CONJUNTO
   ↓
ANÚNCIO
```

A análise deve conseguir localizar em qual nível ocorreu a deterioração.

Exemplo:

```text
Campanha     → saudável
Conjunto     → saudável
Anúncio      → problema identificado
```

Em vez de apenas dizer que uma campanha piorou, o objetivo é chegar a diagnósticos como:

> O aumento do CPL está concentrado no anúncio CRIATIVO_03. Os demais anúncios mantiveram desempenho semelhante.

---

## Dashboard principal

Indicadores previstos para a visão geral:

- investimento;
- leads;
- CPL;
- CTR;
- CPC;
- conversas;
- custo por conversa.

Também deverá destacar rapidamente campanhas que precisam de atenção.

Os gráficos só devem existir quando ajudarem a responder uma pergunta de negócio.

---

## Comparação de períodos

Funcionalidade obrigatória do MVP.

Exemplo:

```text
Últimos 7 dias
      VS
7 dias anteriores
```

A comparação poderá mostrar variações de:

- investimento;
- leads;
- CPL;
- CTR;
- CPC.

A IA deverá interpretar o resultado, mas não substituir os cálculos determinísticos.

---

## Análises da IA

A IA é a camada de interpretação do produto.

Uma análise deve conseguir registrar:

```text
Campanha
Problema
Possíveis causas
Recomendação
Prioridade
```

As análises não devem ser sobrescritas. Cada execução deve gerar histórico.

Isso permitirá responder perguntas como:

> A IA já tinha detectado esse problema?

---

## Melhorias e experimentos

As recomendações poderão ser transformadas em melhorias acompanháveis.

Status previstos:

```text
Pendente
Em teste
Aplicada
Validando
Resolvida
Descartada
```

Cada melhoria deverá registrar uma hipótese e permitir comparar o resultado antes e depois da alteração.

Exemplo:

```text
Hipótese:
CTR caiu por fadiga criativa

Antes:
CTR 1,21%
CPL R$ 72

Depois:
CTR 1,78%
CPL R$ 51

Conclusão:
Hipótese confirmada
```

Esse histórico deverá formar a memória de aprendizado da conta.

---

## Endpoints planejados

Backend inicial:

```text
GET /
GET /health
GET /api/v1/health
```

Endpoints previstos para evolução do MVP:

```text
GET  /api/v1/dashboard
GET  /api/v1/clients
GET  /api/v1/campaigns
GET  /api/v1/campaigns/{id}
GET  /api/v1/analyses
GET  /api/v1/improvements

POST  /api/v1/improvements
PATCH /api/v1/improvements/{id}

POST /api/v1/analysis/run
POST /api/v1/sync/meta
```

---

# Como testar

Esta seção segue o planejamento atual do MVP. Os testes devem acompanhar a implementação das etapas; o documento de planejamento ainda não define comandos específicos de instalação ou execução local.

## 1. Backend base

Primeira validação prevista para a Etapa 1.

Com o backend FastAPI em execução, testar:

```http
GET /
GET /health
GET /api/v1/health
```

Resultado esperado:

- aplicação responde;
- serviço está disponível;
- endpoint de saúde retorna sucesso;
- configuração via `.env` foi carregada sem impedir a inicialização.

## 2. Supabase

Na Etapa 2, depois de configurar a conexão do FastAPI com o Supabase:

Testar:

- conexão com o banco;
- leitura de um registro;
- escrita de um registro;
- carregamento das variáveis de ambiente;
- comportamento da aplicação quando a configuração de banco estiver ausente ou inválida.

## 3. Modelo de dados

Depois da criação das tabelas da Etapa 3, conferir a existência e funcionamento de:

```text
clients
meta_accounts
campaigns
adsets
ads
campaign_metrics
adset_metrics
ad_metrics
ai_analyses
recommendations
improvements
alerts
```

Validar pelo menos:

- criação de registros;
- leitura dos registros;
- relacionamento entre cliente, conta, campanha, conjunto e anúncio;
- persistência das métricas históricas;
- persistência das análises sem sobrescrever histórico.

## 4. Integração n8n → dados

Na Etapa 4, adaptar os fluxos existentes para persistir dados no modelo do SaaS.

Validar o caminho:

```text
Meta Graph API
      ↓
n8n
      ↓
normalização
      ↓
Supabase
```

Conferir:

- campanhas recebidas;
- conjuntos recebidos;
- anúncios recebidos;
- métricas normalizadas;
- datas corretas;
- histórico preservado.

## 5. API do dashboard

Quando a Etapa 5 estiver implementada, testar:

```http
GET /api/v1/dashboard
GET /api/v1/clients
GET /api/v1/campaigns
GET /api/v1/campaigns/{id}
GET /api/v1/analyses
GET /api/v1/improvements
```

Exemplo planejado:

```http
GET /api/v1/dashboard?client_id=123&period=30d
```

Resposta esperada conceitualmente:

```json
{
  "spend": 18420,
  "leads": 387,
  "cpl": 47.60,
  "ctr": 1.82,
  "campaigns_attention": 3,
  "improvements_pending": 7
}
```

## 6. Comparação de períodos

Testar pelo menos:

```text
últimos 7 dias
VS
7 dias anteriores
```

Conferir se investimento, leads, CPL, CTR e CPC são calculados para os dois períodos e se as variações são apresentadas corretamente.

## 7. Análise de IA

Quando a camada de inteligência estiver conectada, fornecer dados conhecidos e verificar se a análise contém:

- problema identificado;
- possíveis causas;
- recomendação;
- prioridade.

A análise deve respeitar a hierarquia:

```text
Campanha → Conjunto → Anúncio
```

Também deve ser possível confirmar que cada nova execução cria histórico em vez de sobrescrever a anterior.

## 8. Melhorias

Quando os endpoints de melhoria existirem, testar o ciclo:

```text
Pendente
   ↓
Em teste
   ↓
Aplicada
   ↓
Validando
   ↓
Resolvida ou Descartada
```

Validar também o registro de:

- hipótese;
- métricas antes;
- data da alteração;
- métricas depois;
- conclusão.

## 9. Sincronização e análise manual

Quando os endpoints estiverem implementados, validar:

```http
POST /api/v1/sync/meta
POST /api/v1/analysis/run
```

O primeiro deverá iniciar/solicitar a sincronização de dados da Meta.

O segundo deverá iniciar/solicitar uma análise usando os dados já disponíveis.

Os contratos exatos de request/response ainda deverão ser definidos durante a implementação.

---

## Roadmap inicial

### Etapa 1 — Backend base

- [ ] criar FastAPI;
- [ ] endpoint `/health`;
- [ ] configurações via `.env`;
- [ ] Dockerfile;
- [ ] estrutura de testes;
- [ ] organização por rotas, serviços e modelos.

**Status no planejamento:** iniciado.

### Etapa 2 — Supabase

- [ ] conectar FastAPI ao Supabase;
- [ ] configurar variáveis de ambiente;
- [ ] criar cliente de banco;
- [ ] testar leitura e escrita.

### Etapa 3 — Modelo de dados

- [ ] criar tabelas iniciais do SaaS.

### Etapa 4 — Integração n8n

- [ ] adaptar os fluxos existentes para persistir dados no modelo do SaaS.

### Etapa 5 — API do dashboard

- [ ] `/dashboard`;
- [ ] `/clients`;
- [ ] `/campaigns`;
- [ ] `/campaigns/{id}`;
- [ ] `/analyses`;
- [ ] `/improvements`.

### Etapa 6 — Frontend

- [ ] construir dashboard em Next.js.

### Etapa 7 — Inteligência

- [ ] criar regras de diagnóstico da IA.

### Etapa 8 — Melhorias e aprendizado

- [ ] registrar melhorias;
- [ ] registrar antes/depois;
- [ ] registrar resultados e aprendizados.

---

## Princípio central

O DescompliADS não deve ser apenas mais um dashboard de Meta Ads.

A proposta é:

> Um painel para gestores de tráfego que transforma métricas do Meta Ads em diagnóstico, prioridades e histórico de melhorias.
