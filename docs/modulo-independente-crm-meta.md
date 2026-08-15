# Módulo Independente de CRM — Leads, Feedback e Públicos Meta

Status: **arquitetura definida; implementação n8n pendente**.

Este documento substitui o desenho anterior em que o rastreamento parecia depender de um CRM específico.

O módulo será um **HUB independente**. CRM, WhatsApp, formulário, planilha, ERP, aplicativo ou sistema próprio serão apenas fontes de eventos.

---

# 1. Objetivo

Criar uma camada neutra entre os sistemas do cliente e a Meta capaz de:

1. receber eventos do funil de qualquer origem;
2. manter um `lead_id` canônico dentro do Meta Ads Growth;
3. preservar a atribuição campanha → conjunto → anúncio quando houver evidência;
4. medir lead identificado, qualificado, agendamento, proposta e venda;
5. devolver eventos de qualidade para a Meta via Conversions API;
6. criar e manter públicos baseados em leads qualificados e clientes;
7. alimentar Performance, Tendência, Qualidade e Motor de Decisão.

O HUB não será um CRM. Ele não precisa gerenciar tarefas comerciais, pipeline, notas do corretor ou cadastro completo do cliente.

---

# 2. Princípio de independência

```text
CRM A ─────────┐
CRM B ─────────┤
WhatsApp ──────┤
Formulário ────┤
Planilha ──────┤
ERP ───────────┤
Sistema próprio┤
               ↓
      CONTRATO PADRONIZADO
               ↓
META ADS | 05 | HUB DE EVENTOS DE LEADS
               ↓
        BANCO CANÔNICO
          ↙          ↘
FEEDBACK META       PÚBLICOS META
   CAPI             CUSTOM AUDIENCE
```

Para integrar um novo sistema não alteramos o núcleo. Criamos apenas um adaptador que converte o payload de origem para o contrato do HUB.

---

# 3. Workflows planejados

## 05 — HUB DE EVENTOS DE LEADS

```text
META ADS | 05 | HUB DE EVENTOS DE LEADS
```

Responsável por receber, validar, normalizar e registrar eventos.

```text
RECEBE EVENTO DO SISTEMA
        ↓
AUTENTICA INTEGRAÇÃO
        ↓
NORMALIZA CONTRATO DO LEAD
        ↓
VALIDA EVENTO DO FUNIL
        ↓
NORMALIZA E PROTEGE IDENTIFICADORES
        ↓
RESOLVE LEAD CANÔNICO
        ↓
RESOLVE ATRIBUIÇÃO META
        ↓
REGISTRA EVENTO DO FUNIL
        ↓
PREPARA FEEDBACK META
        ↓
ATUALIZA ELEGIBILIDADE DE PÚBLICO
        ↓
RESPONDE À ORIGEM
```

## 06 — FEEDBACK PARA META

```text
META ADS | 06 | FEEDBACK PARA META
```

Responsável exclusivamente por enviar eventos elegíveis para a Conversions API.

```text
BUSCA EVENTOS CAPI PENDENTES
        ↓
DIVIDE EM LOTES
        ↓
MONTA PAYLOAD META
        ↓
ENVIA CONVERSÃO PARA DATASET
        ↓
VALIDA RESPOSTA
      ↙       ↘
 SUCESSO      ERRO
   ↓            ↓
MARCA        AGENDA
ENVIADO      NOVA TENTATIVA
```

## 07 — PÚBLICOS DE LEADS

```text
META ADS | 07 | PÚBLICOS DE LEADS
```

Responsável por sincronizar grupos elegíveis com Custom Audiences.

```text
BUSCA MEMBROS PENDENTES
        ↓
VALIDA PERMISSÃO DE USO
        ↓
MONTA LOTE DE HASHES
        ↓
ADICIONA / REMOVE NO PÚBLICO META
        ↓
REGISTRA RESULTADO DA SINCRONIZAÇÃO
```

---

# 4. Contrato universal de entrada

Exemplo completo:

```json
{
  "cliente": "cliente_001",
  "evento_externo_id": "crm-98342-status-qualified",
  "lead_externo_id": "98342",
  "sistema_origem": "crm_do_cliente",
  "sessao_id": "sessao_abc",
  "evento": "lead_qualificado",
  "ocorrido_em": "2026-08-13T18:30:00-03:00",
  "score_qualificacao": 82,
  "valor": null,
  "moeda": "BRL",
  "identidade": {
    "email": "cliente@exemplo.com",
    "telefone": "+5551999999999",
    "nome": "Nome",
    "sobrenome": "Sobrenome",
    "cidade": "Novo Hamburgo",
    "estado": "RS",
    "pais": "BR"
  },
  "meta": {
    "meta_lead_id": null,
    "fbc": null,
    "fbp": null,
    "ctwa_clid": null,
    "conta_anuncio": "742175035567342",
    "id_campanha": "120000000001",
    "id_conjunto": "120000000002",
    "id_anuncio": "120000000003",
    "origem_atribuicao": "meta_referral",
    "confianca_atribuicao": "alta"
  },
  "permissoes": {
    "pode_compartilhar_meta": true,
    "pode_usar_publico": true
  },
  "metadata": {}
}
```

Campos pessoais não devem ser inventados. Se um sistema só possui telefone, envia somente telefone.

---

# 5. Eventos internos do funil

O HUB trabalha com nomes próprios e estáveis:

```text
conversa_iniciada
lead_identificado
lead_qualificado
agendamento
proposta
venda
desqualificado
```

Esses nomes são independentes da nomenclatura de qualquer CRM e independentes dos nomes de evento da Meta.

Exemplos de adaptação:

```text
CRM A: WON
→ venda

CRM B: FECHADO
→ venda

Notion: Status = Comprou
→ venda
```

---

# 6. Event ID e idempotência

Todo evento recebido precisa de:

```text
evento_externo_id
```

Ele deve ser único para aquele cliente.

Exemplo:

```text
hubspot-8392-stage-qualified-20260813T183000
```

Se o mesmo webhook for entregue duas vezes, o segundo não cria novo evento.

Para envio à Meta também geramos um `event_id` estável, por exemplo:

```text
cliente_001|lead_98342|lead_qualificado|20260813T183000
```

Isso permite retry técnico sem transformar uma tentativa repetida em uma nova conversão lógica.

---

# 7. Identidade e matching

O módulo deve usar todos os identificadores legítimos disponíveis para aumentar a possibilidade de matching.

Exemplos suportados pela arquitetura:

```text
email
telefone
external_id
Meta lead_id
fbc
fbp
ctwa_clid
```

O SDK oficial da Meta possui suporte a dados de usuário e, nas versões atuais, o Parameter Builder normaliza e aplica SHA-256 a informações pessoais como e-mail e telefone.

## Política do HUB

1. receber identidade apenas quando necessária;
2. normalizar imediatamente;
3. aplicar SHA-256 aos campos aplicáveis;
4. persistir os hashes no módulo de mídia;
5. evitar armazenar e-mail e telefone em texto puro nesta camada;
6. preservar identificadores Meta não-PII necessários à atribuição.

A migration implementa isso em:

```text
meta_hub_identificadores
```

---

# 8. Atribuição

O HUB nunca deve deduzir anúncio apenas por proximidade de horário.

Prioridade:

```text
1. IDs Meta recebidos diretamente
2. meta_lead_id / referral / ctwa_clid quando disponíveis
3. fbc/fbp ou parâmetros de origem válidos
4. UTM/link rastreado
5. associação manual confirmada
6. desconhecida
```

Confiança:

```text
alta
media
baixa
desconhecida
```

Sem evidência suficiente:

```text
origem_atribuicao = desconhecida
confianca_atribuicao = desconhecida
```

---

# 9. Devolvendo qualidade para a Meta — Conversions API

A Conversions API cria uma conexão servidor → Meta para eventos de website, app, offline, mensagens e dados vindos de sistemas de negócio.

Para este projeto ela terá duas funções:

```text
MENSURAÇÃO
Saber que o lead virou qualificado/agendamento/venda.

OTIMIZAÇÃO
Dar à Meta sinais posteriores da jornada para que campanhas compatíveis possam aprender quais leads geram valor.
```

A Meta atualmente orienta o uso de **datasets + Conversions API** para eventos offline. A antiga Offline Conversions API foi descontinuada para novos uploads em offline event sets.

## Dataset

O cliente terá no HUB:

```text
dataset_id
conta_anuncio
graph_api_version
```

No Events Manager atual, datasets agrupam eventos de diferentes fontes. Quando um dataset deriva de um Pixel existente, o ID do dataset pode ser o mesmo ID do Pixel.

## Endpoint conceitual

```text
POST https://graph.facebook.com/{{GRAPH_API_VERSION}}/{{DATASET_ID}}/events
```

A versão da API deve ser variável de configuração. O projeto começa documentado para a geração atual da API, mas nunca deve espalhar uma versão fixa por vários nodes.

## Payload conceitual

```json
{
  "data": [
    {
      "event_name": "<EVENTO_META_CONFIGURADO>",
      "event_time": 1786656600,
      "event_id": "cliente_001|lead_98342|lead_qualificado|20260813T183000",
      "action_source": "<ORIGEM_COMPATIVEL_COM_O_EVENTO>",
      "user_data": {
        "em": ["<SHA256_EMAIL>"],
        "ph": ["<SHA256_TELEFONE>"],
        "external_id": ["<SHA256_ID_EXTERNO>"],
        "lead_id": "<META_LEAD_ID_SE_EXISTIR>",
        "fbc": "<FBC_SE_EXISTIR>",
        "fbp": "<FBP_SE_EXISTIR>"
      },
      "custom_data": {
        "etapa_interna": "lead_qualificado",
        "score_qualificacao": 82
      }
    }
  ]
}
```

O `action_source` não será hardcoded. Deve refletir a origem real e usar um valor permitido pela versão atual da Conversions API.

## Mapeamento configurável

Não vamos amarrar o código a nomes de eventos Meta.

Tabela:

```text
meta_hub_mapa_eventos_meta
```

Exemplo lógico:

```text
lead_identificado  → evento Meta configurado A
lead_qualificado   → evento Meta configurado B
agendamento        → evento Meta configurado C
venda              → evento Meta configurado D
```

Isso permite adaptar o cliente ao tipo de campanha, dataset e eventos efetivamente disponíveis na conta.

---

# 10. Conversion Leads e qualidade

Para **Lead Ads com Instant Forms**, a Meta documenta atualmente o performance goal:

```text
Maximize number of conversion leads
```

Essa configuração usa dados posteriores enviados via Conversions API para ajudar a plataforma a aprender quais leads têm maior probabilidade de converter.

Importante: isso não significa que qualquer campanha ou qualquer destino de mensagens possa otimizar da mesma forma.

A disponibilidade de otimização varia conforme:

```text
objetivo
conversion location
canal
performance goal
evento
configuração da conta
```

Para anúncios click-to-message/WhatsApp, o HUB ainda é útil para mensuração, públicos e sinais de negócio, mas antes de configurar um evento como objetivo de otimização devemos confirmar o que está disponível naquela conta no Ads Manager.

---

# 11. Outbox e retry

O evento do lead não deve depender da disponibilidade imediata da API da Meta.

Fluxo:

```text
Evento comercial acontece
        ↓
HUB grava evento
        ↓
HUB cria item na fila CAPI
        ↓
responde ao sistema de origem
        ↓
worker envia para Meta separadamente
```

Tabela:

```text
meta_hub_fila_capi
```

Status:

```text
pendente
enviando
enviado
erro
descartado
```

Assim uma indisponibilidade da Meta não interrompe o CRM, WhatsApp ou atendimento.

---

# 12. Públicos de leads qualificados

A segunda saída do módulo é audiência.

O HUB poderá manter, por cliente:

```text
QUALIFICADOS
AGENDADOS
CLIENTES
DESQUALIFICADOS
```

Nem todo grupo precisa ser usado para targeting. Alguns podem servir apenas como exclusão ou análise.

## Público de lista de clientes

Para Customer List Custom Audiences, o fluxo é:

```text
lead torna-se elegível
        ↓
confirma pode_usar_publico = true
        ↓
seleciona identificadores disponíveis
        ↓
normaliza
        ↓
SHA-256 local
        ↓
envia hashes para Custom Audience
        ↓
registra sincronização
```

A Meta exige que os dados da lista sejam hashados localmente antes da transmissão e que o anunciante tenha os direitos/permissões e base legal necessários para utilizar esses dados.

## Endpoint de membros

A API de Marketing possui a operação de usuários de Custom Audience. A implementação deverá usar a operação compatível com a versão corrente da API/SDK, e não copiar chamadas antigas com versão fixa.

A arquitetura mantém o ID em:

```text
meta_hub_publicos.meta_custom_audience_id
```

E controla os membros em:

```text
meta_hub_publico_membros
```

Isso permite:

```text
adicionar qualificado
remover se perder elegibilidade
retry de erro
auditar quem já foi sincronizado
```

---

# 13. Lookalike e Advantage+ Audience

Depois que um público de alta qualidade tiver tamanho e matching suficientes, ele poderá servir como fonte para estratégias de prospecção compatíveis com a conta, incluindo Lookalike ou como sinal/sugestão de audiência em experiências Advantage+.

O objetivo não é criar um público com todo mundo que iniciou conversa.

O sinal de maior valor deve vir de grupos como:

```text
lead_qualificado
agendamento
venda
```

Exemplo:

```text
1000 conversas baratas
    ↓
180 leads qualificados
    ↓
65 agendamentos
    ↓
12 vendas

Público ruim para aprendizado:
1000 conversas indistintas

Público mais valioso:
180 qualificados ou, quando houver escala suficiente, compradores
```

Não há garantia de que um grupo pequeno forme imediatamente uma audiência utilizável. O módulo registra os dados e deixa a plataforma informar disponibilidade/tamanho/matching.

---

# 14. Exclusões

Também poderemos manter públicos para exclusão, quando fizer sentido para a estratégia:

```text
clientes existentes
leads já vendidos
leads já em atendimento
```

Exemplo:

```text
Campanha de aquisição
EXCLUI clientes existentes
```

A utilização depende da estratégia de campanha e das regras vigentes da Meta.

---

# 15. Privacidade e governança

O HUB terá dois gates independentes:

```text
pode_compartilhar_meta
pode_usar_publico
```

Eles não são uma declaração jurídica automática. Apenas registram a decisão/configuração recebida do cliente/integrador.

Regras obrigatórias:

- não enviar dados sem autorização/configuração aplicável;
- não usar Customer List Audience sem base adequada;
- não guardar token Meta em tabela do banco;
- tokens ficam em credenciais seguras do n8n/secret manager;
- não versionar tokens no GitHub;
- não guardar PII em logs de execução quando puder ser evitado;
- não misturar clientes;
- não misturar dados fictícios e produção;
- nunca atribuir anúncio sem evidência;
- registrar erro e resposta Meta para auditoria sem expor segredo.

---

# 16. Banco de dados

Migration:

```text
database/005-cria-hub-feedback-meta.sql
```

Principais tabelas:

```text
meta_hub_clientes
meta_hub_leads
meta_hub_identificadores
meta_hub_eventos
meta_hub_mapa_eventos_meta
meta_hub_fila_capi
meta_hub_publicos
meta_hub_publico_membros
```

View:

```text
v_meta_hub_funil
```

---

# 17. Integração com o restante do Meta Ads Growth

```text
META ADS | 01 | COLETA
       ↓
Métricas de mídia

META ADS | 05 | HUB DE LEADS
       ↓
Eventos comerciais
       ↓
┌──────────────────────────────┐
│  QUALIDADE DO LEAD           │
│  custo por qualificado       │
│  custo por agendamento       │
│  custo por venda             │
└──────────────────────────────┘
       ↓
MOTOR DE DECISÃO
       ↑
Performance + Tendência + Fadiga

Em paralelo:
HUB → 06 FEEDBACK META → Conversions API
HUB → 07 PÚBLICOS → Custom Audiences
```

---

# 18. Métricas que o módulo habilita

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
ROAS/retorno quando aplicável
```

E, principalmente:

```text
QUALIDADE POR CAMPANHA
QUALIDADE POR CONJUNTO
QUALIDADE POR ANÚNCIO
```

---

# 19. Exemplo de decisão futura

```text
ANÚNCIO A
100 conversas
R$ 5/conversa
10 qualificados
R$ 50/qualificado
1 venda

ANÚNCIO B
60 conversas
R$ 8/conversa
24 qualificados
R$ 20/qualificado
4 vendas
```

O Motor de Performance isolado pode favorecer A pelo custo de conversa.

O Motor de Decisão com o HUB deve perceber que B produz muito mais valor comercial.

---

# 20. Processo de implantação por cliente

## Etapa A — Cadastrar integração

Definir:

```text
chave_cliente
conta_anuncio
dataset_id
versao API
mapeamento de eventos
públicos desejados
```

## Etapa B — Criar adaptador

Converter o sistema do cliente para o contrato universal.

Pode ser:

```text
Webhook
API
polling
n8n subworkflow
planilha
fila
```

## Etapa C — Testar ingestão

Usar eventos fictícios.

Validar:

```text
idempotência
atribuição
hashes
funil
isolamento do cliente
```

## Etapa D — Testar CAPI

Usar o mecanismo de teste disponibilizado no Events Manager/Conversions API antes de enviar produção.

Confirmar:

```text
evento recebido
matching
campos válidos
sem duplicação lógica
```

## Etapa E — Ativar feedback

```text
enviar_feedback_meta = true
```

## Etapa F — Criar público de qualificados

Criar o Custom Audience na conta autorizada e salvar seu ID.

Depois:

```text
sincronizar_publico_qualificados = true
```

## Etapa G — Validar uso no Ads Manager

Antes de alterar campanha, confirmar quais performance goals, conversion locations e opções de audiência estão disponíveis naquela conta.

---

# 21. Configuração da versão da API

A versão Graph API será centralizada por cliente/configuração:

```text
graph_api_version
```

Na arquitetura inicial:

```text
v25.0
```

mas nenhum endpoint crítico deverá depender de versão escrita diretamente no código de vários nodes.

Quando houver upgrade:

```text
revisar release Meta
→ atualizar configuração
→ testar
→ promover
```

---

# 22. O que NÃO faremos

```text
Não criar um CRM paralelo.
Não depender de HubSpot, Kommo, RD ou outro fornecedor.
Não inferir origem por horário.
Não tratar conversa como qualificação.
Não enviar todo contato automaticamente para público.
Não subir PII bruta quando o fluxo exige hashing.
Não salvar access token no GitHub.
Não alterar campanhas automaticamente nesta fase.
```

---

# 23. Ordem de construção

```text
1. Aplicar migration 005 em ambiente de teste
2. Criar META ADS | 05 | HUB DE EVENTOS DE LEADS
3. Testar contrato com payload fictício
4. Criar META ADS | 06 | FEEDBACK PARA META
5. Testar no Events Manager
6. Criar META ADS | 07 | PÚBLICOS DE LEADS
7. Sincronizar público de teste/autorizado
8. Criar Fase 4 — Qualidade dos Leads
9. Integrar qualidade ao painel do gestor
10. Integrar tudo ao Motor de Decisão
```

---

# Referências oficiais consultadas

- Meta Business Help Center — About Conversions API
- Meta for Business — Lead Ads with Forms / Conversion Leads
- Meta for Business — Advantage+ Leads
- Meta Customer List Custom Audiences Terms
- Meta/Facebook Business SDK oficial — Conversions API
- Meta CAPI Parameter Builder oficial
- Meta Marketing API — workspace oficial no Postman

As APIs e recursos da Meta mudam por versão e por elegibilidade de conta. Antes da implementação produtiva, validar novamente os endpoints e recursos disponíveis na versão corrente.