# Guia 05/06 — HUB de Leads e Feedback para Meta

Status: **workflows implementados em `desenvolvimento` e aguardando configuração/teste no n8n, PostgreSQL/Supabase e Meta Events Manager**.

Este é o manual operacional dos módulos:

```text
META ADS | 05 | HUB DE EVENTOS DE LEADS
META ADS | 06 | FEEDBACK PARA META
```

Arquivos:

```text
workflows/05-hub-eventos-leads.json
workflows/06-feedback-para-meta.json

database/005-cria-hub-feedback-meta.sql
database/006-funcoes-hub-eventos-capi.sql
```

O objetivo é receber o avanço comercial de um lead de **qualquer sistema**, registrar o funil de forma padronizada e, quando autorizado/configurado, devolver eventos para a Meta por Conversions API.

---

# 1. Visão geral

```text
CRM / WhatsApp / ERP / formulário / planilha / sistema próprio
                         ↓
               POST evento padronizado
                         ↓
        META ADS | 05 | HUB DE EVENTOS DE LEADS
                         ↓
                   PostgreSQL
                   ↙         ↘
             FUNIL INTERNO   FILA CAPI
                                ↓
                 META ADS | 06 | FEEDBACK PARA META
                                ↓
                       Conversions API
                                ↓
                         Meta Dataset
```

A ingestão e o envio são separados de propósito.

O `05` **não depende da Meta estar disponível** para registrar o evento do lead.

O `06` lê uma fila e tenta enviar depois. Se houver falha de rede, token, permissão ou API, o evento comercial continua salvo no HUB.

---

# 2. O que cada workflow faz

## 05 — HUB DE EVENTOS DE LEADS

Responsabilidades:

```text
receber evento
validar contrato
normalizar campos
resolver cliente
resolver lead canônico
preservar atribuição conhecida
hash de identificadores
registrar evento do funil
criar fila CAPI quando permitido
marcar elegibilidade para público
responder ao sistema de origem
```

Eventos internos aceitos:

```text
conversa_iniciada
lead_identificado
lead_qualificado
agendamento
proposta
venda
desqualificado
```

O HUB não precisa saber se a origem foi Kommo, RD Station, Pipedrive, HubSpot, Notion, Evolution API ou outro sistema.

---

## 06 — FEEDBACK PARA META

Responsabilidades:

```text
buscar eventos CAPI pendentes
reservar lote sem duplicar processamento
montar endpoint Meta
adicionar Test Event Code quando configurado
enviar POST para a Conversions API
validar events_received
salvar resposta da Meta
repetir erros temporários
encerrar após limite de tentativas
```

A versão inicial processa até:

```text
20 eventos por execução
```

e roda a cada:

```text
10 minutos
```

O retry usa aproximadamente:

```text
1ª falha → +5 minutos
2ª falha → +30 minutos
3ª falha → +2 horas
4ª falha → +12 horas
5ª falha → descartado para revisão
```

`descartado` não significa apagar o evento. O evento original continua no HUB; somente o envio automático deixa de tentar.

---

# 3. Pré-requisitos

Antes de importar os workflows, precisamos de:

```text
n8n
PostgreSQL ou Supabase/PostgreSQL
acesso ao Meta Events Manager
dataset/pixel compatível com a integração
access token para a Conversions API
```

Também precisamos definir, por cliente:

```text
chave interna do cliente
Dataset ID
versão Graph API
quais eventos internos serão enviados à Meta
se o cliente autorizou feedback para Meta
```

Nunca grave no GitHub:

```text
access token
app secret
senha PostgreSQL
service role key
segredo do webhook
```

Esses valores devem ficar em credenciais/secret storage do ambiente.

---

# 4. Preparar o banco

Execute nesta ordem:

```text
1. database/005-cria-hub-feedback-meta.sql
2. database/006-funcoes-hub-eventos-capi.sql
```

A migration `005` cria as tabelas do HUB.

A `006` adiciona:

```text
action_source_padrao
meta_test_event_code
meta_hub_sha256()
meta_hub_receber_evento()
```

A função `meta_hub_receber_evento(jsonb)` concentra a parte crítica de idempotência, hashing, funil e criação da fila CAPI.

---

# 5. Cadastrar um cliente

Exemplo de ambiente de TESTE:

```sql
insert into public.meta_hub_clientes (
  chave_cliente,
  nome_cliente,
  conta_anuncio,
  dataset_id,
  graph_api_version,
  action_source_padrao,
  enviar_feedback_meta,
  sincronizar_publico_qualificados,
  meta_test_event_code
)
values (
  'CLIENTE_TESTE',
  'Cliente de Teste',
  'CONTA_TESTE',
  'COLOQUE_O_DATASET_ID',
  'v25.0',
  'other',
  true,
  false,
  'COLOQUE_O_TEST_EVENT_CODE'
)
on conflict (chave_cliente)
do update set
  dataset_id = excluded.dataset_id,
  graph_api_version = excluded.graph_api_version,
  action_source_padrao = excluded.action_source_padrao,
  enviar_feedback_meta = excluded.enviar_feedback_meta,
  meta_test_event_code = excluded.meta_test_event_code,
  atualizado_em = now();
```

Para um cliente real, use uma chave estável, por exemplo:

```text
imobiliaria_alpha
cliente_0042
rede_x_sul
```

Não use o nome da pessoa como chave técnica se ele puder mudar.

---

# 6. Mapear os eventos internos para eventos Meta

O HUB não fixa nomes de evento Meta no código.

Existe a tabela:

```text
meta_hub_mapa_eventos_meta
```

Exemplo de configuração de teste:

```sql
insert into public.meta_hub_mapa_eventos_meta (
  cliente_id,
  evento_interno,
  evento_meta,
  habilitado,
  observacao
)
select
  id,
  'lead_qualificado',
  'QUALIFIED_LEAD_TEST',
  true,
  'Evento customizado apenas para validar o transporte CAPI'
from public.meta_hub_clientes
where chave_cliente = 'CLIENTE_TESTE'
on conflict (cliente_id, evento_interno)
do update set
  evento_meta = excluded.evento_meta,
  habilitado = excluded.habilitado,
  observacao = excluded.observacao;
```

`QUALIFIED_LEAD_TEST` acima é **exemplo de evento customizado para teste de transporte**, não uma recomendação universal de evento de otimização.

Em produção, o mapeamento deve refletir a configuração efetivamente suportada no Events Manager e no tipo de campanha.

Exemplo conceitual:

```text
NOSSO EVENTO          EVENTO META CONFIGURADO

lead_qualificado  →   EVENTO_QUALIFICADO_DO_CLIENTE
agendamento       →   EVENTO_AGENDAMENTO_DO_CLIENTE
venda             →   Purchase ou evento configurado
```

Isso permite mudar a estratégia sem reescrever o workflow.

---

# 7. Importar o Workflow 05

Importe:

```text
workflows/05-hub-eventos-leads.json
```

Nome esperado:

```text
META ADS | 05 | HUB DE EVENTOS DE LEADS
```

Principais nodes:

```text
RECEBE EVENTO DO SISTEMA
TESTE MANUAL
GERA EVENTO DE TESTE
NORMALIZA CONTRATO DO LEAD
REGISTRA EVENTO NO HUB
FORMATA RESPOSTA DO HUB
É TESTE MANUAL?
RESPONDE EVENTO RECEBIDO
```

---

# 8. Configurar PostgreSQL no Workflow 05

Abra:

```text
REGISTRA EVENTO NO HUB
```

Selecione uma credencial PostgreSQL que tenha acesso às tabelas `meta_hub_*`.

A query utilizada é:

```sql
SELECT public.meta_hub_receber_evento($1::jsonb) AS resultado;
```

O workflow envia todo o evento como **um único parâmetro JSONB**.

Isso é proposital. Além de simplificar o contrato, evita problemas com valores contendo vírgulas e reduz risco de SQL injection por concatenação de strings.

---

# 9. Configurar autenticação do Webhook 05

O node:

```text
RECEBE EVENTO DO SISTEMA
```

está preparado para:

```text
POST /meta-ads-growth/v1/eventos
```

Configure uma credencial de **Header Auth**.

Exemplo conceitual:

```text
Header Name:
X-Meta-Hub-Key

Header Value:
SEGREDO_FORTE_DO_CLIENTE_OU_INTEGRACAO
```

Não coloque esse segredo no JSON do workflow.

Em produção, não publique o webhook sem autenticação.

Para multi-cliente mais avançado, poderemos evoluir para uma chave diferente por integração e rotação de segredo.

---

# 10. Contrato mínimo para qualquer sistema

Qualquer origem precisa converter seus dados para este formato mínimo:

```json
{
  "cliente": "imobiliaria_alpha",
  "evento_externo_id": "evt-000001",
  "lead_externo_id": "lead-123",
  "sistema_origem": "crm_qualquer",
  "evento": "lead_qualificado",
  "ocorrido_em": "2026-08-14T10:30:00-03:00"
}
```

Campos obrigatórios:

```text
cliente
evento_externo_id
lead_externo_id
evento
ocorrido_em
```

`sistema_origem` é altamente recomendado.

---

# 11. Contrato completo

Exemplo:

```json
{
  "cliente": "imobiliaria_alpha",
  "evento_externo_id": "kommo-98342-qualified",
  "lead_externo_id": "98342",
  "sistema_origem": "kommo",
  "sessao_id": "sessao-abc-123",
  "evento": "lead_qualificado",
  "ocorrido_em": "2026-08-14T10:30:00-03:00",
  "score_qualificacao": 82,
  "valor": null,
  "moeda": "BRL",

  "pode_compartilhar_meta": true,
  "pode_usar_publico": true,

  "action_source": "other",

  "identificadores": {
    "email": "cliente@example.com",
    "telefone": "5551999999999",
    "external_id": "98342"
  },

  "atribuicao": {
    "conta_anuncio": "742175035567342",
    "id_campanha": "120000000000001",
    "id_conjunto": "120000000000002",
    "id_anuncio": "120000000000003",
    "meta_lead_id": null,
    "fbc": null,
    "fbp": null,
    "ctwa_clid": null,
    "origem_atribuicao": "meta_referral",
    "confianca_atribuicao": "alta"
  },

  "metadata": {
    "cidade": "Novo Hamburgo",
    "produto": "Apartamento",
    "origem_status": "QUALIFICADO"
  }
}
```

---

# 12. Regras de identidade

## evento_externo_id

Deve identificar **um evento lógico**.

Exemplo:

```text
lead 123 foi qualificado uma vez
→ evento_externo_id = lead-123-qualified-1
```

Se o sistema repetir a chamada por timeout:

```text
retry 1 → lead-123-qualified-1
retry 2 → lead-123-qualified-1
retry 3 → lead-123-qualified-1
```

Não gere um ID novo a cada retry.

Isso é o que torna a integração idempotente.

---

## lead_externo_id

Deve identificar a mesma pessoa/oportunidade dentro da origem.

Exemplo:

```text
Kommo lead ID
Pipedrive deal/person ID
ID interno do atendimento
UUID do lead no sistema próprio
```

---

# 13. Identificadores e hashing

O Workflow 05 pode receber:

```text
email
telefone
external_id
```

A camada de banco grava os valores de matching como SHA-256.

Exemplo:

```text
email recebido
   ↓
trim + lowercase
   ↓
SHA-256
   ↓
meta_hub_identificadores.tipo = em
```

Telefone:

```text
+55 (51) 99999-9999
        ↓
5551999999999
        ↓
SHA-256
        ↓
tipo = ph
```

Envie telefone com código de país quando possível.

A tabela do HUB não foi desenhada para armazenar e-mail e telefone em texto puro.

Importante: o payload original pode aparecer no histórico de execução do n8n. Em produção, restrinja acesso e retenção de execuções conforme a política do projeto/cliente.

---

# 14. Permissões internas

Existem dois gates separados:

```text
pode_compartilhar_meta
pode_usar_publico
```

Eles não significam a mesma coisa.

Exemplo:

```text
pode_compartilhar_meta = true
pode_usar_publico = false
```

Resultado:

```text
tracking interno          SIM
feedback CAPI             SIM
Custom Audience futuro    NÃO
```

Se ambos forem falsos:

```text
tracking interno          SIM
feedback CAPI             NÃO
Custom Audience futuro    NÃO
```

Os defaults são conservadores.

---

# 15. Atribuição Meta

Nunca invente atribuição.

Quando houver evidência, envie:

```text
id_campanha
id_conjunto
id_anuncio
meta_lead_id
fbc
fbp
ctwa_clid
```

quando cada campo realmente existir no canal/origem.

Também informe:

```text
origem_atribuicao
confianca_atribuicao
```

Exemplo:

```json
{
  "origem_atribuicao": "meta_referral",
  "confianca_atribuicao": "alta"
}
```

Se não houver evidência:

```json
{
  "origem_atribuicao": "desconhecida",
  "confianca_atribuicao": "desconhecida"
}
```

Um lead não deve ser associado a um anúncio apenas porque chegou enquanto aquele anúncio estava ativo.

---

# 16. Testar o Workflow 05 sem CRM

Antes de executar o `TESTE MANUAL`, cadastre `CLIENTE_TESTE` e o mapeamento de evento.

Uma opção segura para validar apenas o HUB primeiro é:

```sql
update public.meta_hub_clientes
set enviar_feedback_meta = false
where chave_cliente = 'CLIENTE_TESTE';
```

Depois:

```text
1. Abra META ADS | 05 | HUB DE EVENTOS DE LEADS
2. Selecione a credencial PostgreSQL
3. Clique em TESTE MANUAL
4. Execute
5. Abra FORMATA RESPOSTA DO HUB
```

Esperado:

```json
{
  "status": "RECEBIDO",
  "ok": true,
  "cliente": "CLIENTE_TESTE",
  "lead_externo_id": "LEAD-TESTE-001",
  "evento": "lead_qualificado"
}
```

---

# 17. Conferir o banco depois do teste 05

Lead:

```sql
select *
from public.meta_hub_leads
where lead_externo_id = 'LEAD-TESTE-001';
```

Evento:

```sql
select *
from public.meta_hub_eventos
where evento_externo_id = 'TESTE-QUALIFICADO-001';
```

Identificadores:

```sql
select tipo, valor_hash
from public.meta_hub_identificadores
where lead_id = (
  select id
  from public.meta_hub_leads
  where lead_externo_id = 'LEAD-TESTE-001'
  limit 1
);
```

Você deverá enxergar hashes, não o e-mail/telefone de teste em texto puro.

---

# 18. Como um CRM/sistema chama o HUB

Exemplo usando `curl`:

```bash
curl -X POST "https://SEU-N8N/webhook/meta-ads-growth/v1/eventos" \
  -H "Content-Type: application/json" \
  -H "X-Meta-Hub-Key: SEU_SEGREDO" \
  -d '{
    "cliente": "imobiliaria_alpha",
    "evento_externo_id": "evt-qualificado-98342",
    "lead_externo_id": "98342",
    "sistema_origem": "crm_qualquer",
    "evento": "lead_qualificado",
    "ocorrido_em": "2026-08-14T10:30:00-03:00",
    "score_qualificacao": 82,
    "pode_compartilhar_meta": true,
    "identificadores": {
      "email": "cliente@example.com",
      "telefone": "5551999999999"
    }
  }'
```

A origem pode fazer isso via:

```text
webhook
HTTP Request
script Python
backend Node/Java/PHP
n8n de outro cliente
Make/Zapier
função serverless
```

O núcleo não muda.

---

# 19. Quando o HUB cria um evento para a Meta

Uma linha na `meta_hub_fila_capi` só é criada quando **todos** os gates principais permitem:

```text
cliente está ativo
+
enviar_feedback_meta = true
+
pode_compartilhar_meta = true
+
existe mapeamento do evento
+
mapeamento está habilitado
```

Se qualquer gate impedir o envio:

```text
o evento comercial continua salvo
mas nada é enviado à Meta
```

---

# 20. event_id da Conversions API

O HUB cria:

```text
event_id = chave_cliente | evento_externo_id
```

Exemplo:

```text
imobiliaria_alpha|evt-qualificado-98342
```

O mesmo evento lógico mantém o mesmo `event_id` mesmo quando o Workflow 06 faz retry.

Isso é importante para idempotência/deduplicação do lado da integração.

---

# 21. Preparar a Meta

A interface pode mudar, mas o caminho conceitual é:

```text
Meta Events Manager
      ↓
selecionar/criar fonte de dados / dataset
      ↓
Conversions API
      ↓
configuração manual ou opção compatível
```

Precisamos obter/configurar:

```text
Dataset ID
Access Token
Test Event Code para validação
```

Na estrutura atual da Meta, eventos de pixel, web e offline vêm sendo consolidados em datasets; quando um dataset é criado/consolidado a partir de um Pixel, o Dataset ID pode ser o mesmo ID do Pixel.

Não presuma isso olhando apenas o nome. Confirme o ID no Events Manager do cliente.

---

# 22. Dataset ID

Grave no cliente:

```sql
update public.meta_hub_clientes
set dataset_id = 'SEU_DATASET_ID'
where chave_cliente = 'imobiliaria_alpha';
```

Não coloque Dataset ID diretamente no node HTTP de forma fixa quando o projeto for multi-cliente.

O Workflow 06 lê esse campo por cliente.

---

# 23. Graph API version

O banco possui:

```text
graph_api_version
```

A configuração inicial do projeto usa:

```text
v25.0
```

mas o valor é parametrizado para permitir upgrade por cliente/ambiente sem reescrever nodes.

Sempre valide a versão suportada antes de uma atualização de produção.

---

# 24. Obter e guardar o Access Token

O access token da Conversions API é segredo.

Não grave em:

```text
meta_hub_clientes
Google Sheets
GitHub
sticky note
Code node
JSON exportado
```

No n8n, crie uma credencial para o node HTTP.

A implementação atual do Workflow 06 está preparada para **Query Auth**:

```text
Name:
access_token

Value:
TOKEN_FORNECIDO_PELA_META
```

Depois selecione essa credencial no node:

```text
ENVIA EVENTO PARA META
```

---

# 25. Importar o Workflow 06

Importe:

```text
workflows/06-feedback-para-meta.json
```

Nome esperado:

```text
META ADS | 06 | FEEDBACK PARA META
```

Nodes:

```text
PROCESSA FILA CAPI - 10 MIN
TESTE MANUAL
BUSCA E RESERVA FILA CAPI
PREPARA REQUISIÇÃO META
ENVIA EVENTO PARA META
CLASSIFICA RESPOSTA META
ATUALIZA FILA CAPI
```

Não ative ainda.

---

# 26. Configurar PostgreSQL no Workflow 06

Selecione a mesma base do HUB nos nodes:

```text
BUSCA E RESERVA FILA CAPI
ATUALIZA FILA CAPI
```

A busca usa:

```text
FOR UPDATE SKIP LOCKED
```

para reduzir o risco de duas execuções reservarem o mesmo item simultaneamente.

---

# 27. Test Event Code

Antes de enviar eventos reais, use a área de **Test Events** no Events Manager e obtenha o código de teste correspondente ao dataset.

Grave temporariamente:

```sql
update public.meta_hub_clientes
set meta_test_event_code = 'SEU_TEST_EVENT_CODE'
where chave_cliente = 'CLIENTE_TESTE';
```

Enquanto esse campo estiver preenchido, o Workflow 06 adiciona:

```json
{
  "test_event_code": "SEU_TEST_EVENT_CODE"
}
```

à requisição.

---

# 28. Como o dado é enviado para a Meta

O Workflow 06 monta uma requisição conceitualmente equivalente a:

```http
POST https://graph.facebook.com/v25.0/SEU_DATASET_ID/events?access_token=SEU_TOKEN
Content-Type: application/json
```

Exemplo de body:

```json
{
  "data": [
    {
      "event_name": "EVENTO_META_CONFIGURADO",
      "event_time": 1786714200,
      "event_id": "imobiliaria_alpha|evt-qualificado-98342",
      "action_source": "other",
      "user_data": {
        "em": ["SHA256_DO_EMAIL_NORMALIZADO"],
        "ph": ["SHA256_DO_TELEFONE_NORMALIZADO"],
        "external_id": ["SHA256_DO_ID_EXTERNO"]
      },
      "custom_data": {
        "meta_ads_growth_evento": "lead_qualificado",
        "score_qualificacao": 82,
        "currency": "BRL"
      }
    }
  ],
  "test_event_code": "SEU_TEST_EVENT_CODE"
}
```

O `access_token` não faz parte do body e não é versionado no workflow.

---

# 29. O que significa cada campo enviado à Meta

## event_name

É o nome do evento Meta definido no mapeamento do cliente.

```text
meta_hub_mapa_eventos_meta.evento_meta
```

Não use um nome apenas porque parece intuitivo. Configure o evento de acordo com o dataset e objetivo da campanha.

---

## event_time

Unix timestamp do momento em que **o evento comercial realmente aconteceu**.

Ele deriva de:

```text
ocorrido_em
```

Não usamos simplesmente o horário em que o Workflow 06 fez o POST.

---

## event_id

Identificador estável do evento lógico.

É reutilizado nos retries.

---

## action_source

Informa a origem da conversão/evento.

O projeto permite configurar um padrão por cliente e sobrescrever no evento quando houver uma origem mais correta.

Não invente `website`, `phone_call`, `business_messaging` ou outra origem apenas para melhorar matching. Use a origem correspondente ao evento real e à documentação aplicável.

---

## user_data

Dados de matching que ajudam a Meta a relacionar o evento a uma pessoa/conta quando permitido.

Nossa primeira versão pode incluir:

```text
em
ph
external_id
lead_id
fbc
fbp
```

Os campos disponíveis variam conforme a origem.

---

## custom_data

Dados de negócio associados ao evento.

Exemplos:

```text
score de qualificação
valor da venda
moeda
etapa interna
```

---

# 30. Exemplo de venda

Entrada no HUB:

```json
{
  "cliente": "imobiliaria_alpha",
  "evento_externo_id": "venda-98342-001",
  "lead_externo_id": "98342",
  "sistema_origem": "erp_imobiliario",
  "evento": "venda",
  "ocorrido_em": "2026-08-14T15:40:00-03:00",
  "valor": 245000,
  "moeda": "BRL",
  "pode_compartilhar_meta": true,
  "identificadores": {
    "email": "cliente@example.com",
    "telefone": "5551999999999"
  }
}
```

Se o mapa do cliente estiver habilitado e o evento estiver configurado corretamente, a fila CAPI carregará `value` e `currency` em `custom_data`.

---

# 31. Teste ponta a ponta 05 → 06 → Meta

## Etapa A — banco

Confirme:

```text
migrations 005 e 006 executadas
CLIENTE_TESTE cadastrado
Dataset ID preenchido
Test Event Code preenchido
enviar_feedback_meta = true
mapa lead_qualificado habilitado
```

---

## Etapa B — Workflow 05

Execute:

```text
TESTE MANUAL
```

Depois confira:

```sql
select
  event_id,
  evento_meta,
  status,
  tentativas,
  payload
from public.meta_hub_fila_capi
order by criado_em desc
limit 10;
```

Esperado antes do Workflow 06:

```text
status = pendente
```

---

## Etapa C — Workflow 06

Configure:

```text
PostgreSQL credential
Meta Query Auth credential
```

Execute:

```text
TESTE MANUAL
```

Abra:

```text
CLASSIFICA RESPOSTA META
```

O sucesso esperado é:

```text
HTTP 2xx
events_received >= 1
sucesso = true
```

Depois:

```sql
select
  event_id,
  status,
  tentativas,
  enviado_em,
  ultimo_erro,
  resposta_meta
from public.meta_hub_fila_capi
order by criado_em desc
limit 10;
```

Esperado:

```text
status = enviado
```

---

# 32. Validar no Events Manager

Com `meta_test_event_code` preenchido, abra a área de Test Events do dataset correspondente.

Confirme:

```text
evento apareceu
nome do evento correto
horário coerente
origem coerente
sem erros de payload
dados de matching aceitos
```

A resposta `events_received = 1` confirma que a API recebeu o evento; a inspeção no Events Manager é necessária para validar a configuração completa e diagnosticar qualidade/matching.

---

# 33. Passar de teste para produção

Somente depois do teste completo:

```sql
update public.meta_hub_clientes
set meta_test_event_code = null
where chave_cliente = 'imobiliaria_alpha';
```

Depois:

```text
1. envie um evento real controlado
2. confira fila CAPI
3. confira Events Manager
4. confira atribuição/matching
5. ative PROCESSA FILA CAPI - 10 MIN
6. publique/ative o Webhook 05
```

Não remova o Test Event Code antes de validar o fluxo inteiro.

---

# 34. CAPI recebida não significa otimização automática

Este é um ponto crítico.

```text
Meta recebeu o evento
≠
campanha está automaticamente otimizada para esse evento
```

O uso do evento para otimização depende de fatores como:

```text
objetivo da campanha
conversion location
performance goal
evento configurado
fonte de dados
regras/recursos disponíveis na conta
volume e matching
```

O HUB envia um sinal confiável. A configuração da campanha define se e como esse sinal entra na otimização.

---

# 35. Instant Forms e Conversion Leads

Para campanhas de Leads com **Instant Form**, a Meta atualmente oferece o performance goal de maximizar `conversion leads` e recomenda integrar dados posteriores de CRM/servidor via Conversions API para ensinar ao sistema o que representa um lead que realmente converte.

Nesse cenário, o nosso HUB pode funcionar como a camada que substitui a dependência de um CRM específico:

```text
Instant Form
     ↓
lead entra em qualquer sistema
     ↓
HUB recebe qualificação real
     ↓
CAPI devolve estágio/resultado
     ↓
Meta recebe feedback
```

A configuração de evento e performance goal deve ser feita de acordo com a orientação exibida pela Meta para a conta.

---

# 36. WhatsApp / mensagens: limite importante

A Meta informa que eventos de mensagens enviados pela Conversions API podem ajudar na mensuração de ações posteriores da jornada em Messenger, Instagram ou WhatsApp.

Porém, a documentação atual também diz que **a otimização usando messaging events está atualmente disponível apenas para eventos de compra no Messenger**.

Portanto, para leads provenientes de WhatsApp, não devemos prometer:

```text
"enviei lead_qualificado por CAPI, então a campanha de WhatsApp otimizará automaticamente para qualificados"
```

Na arquitetura atual, para WhatsApp usamos esses sinais imediatamente para:

```text
mensuração
atribuição
qualidade do anúncio
Motor de Decisão
relatórios
futuro público de qualificados
```

E habilitamos otimização Meta apenas quando houver um recurso/performance goal oficialmente compatível com aquele canal e evento.

---

# 37. Feedback CAPI e Custom Audience são coisas diferentes

```text
CAPI
→ enviar evento/conversão/resultado

Custom Audience
→ sincronizar pessoas elegíveis para um público
```

O Workflow 06 implementa a primeira parte.

O futuro:

```text
META ADS | 07 | PÚBLICOS DE LEADS
```

implementará a segunda.

Não reutilize automaticamente a mesma autorização para ambos. Por isso o HUB mantém:

```text
pode_compartilhar_meta
pode_usar_publico
```

separadamente.

---

# 38. Segurança e privacidade

Regras obrigatórias do projeto:

```text
não salvar token Meta no banco
não salvar token no GitHub
não expor webhook sem autenticação
não guardar email/telefone em texto puro no HUB
não inventar atribuição
não usar público sem autorização/base aplicável
não misturar teste e produção
```

Hash não deve ser tratado como licença para uso irrestrito de dados. O cliente/integrador continua responsável por possuir as permissões e base legal aplicáveis ao compartilhamento e uso dos dados.

---

# 39. Multi-cliente e tokens

O HUB 05 é naturalmente multi-cliente por:

```text
chave_cliente
```

O template inicial do Workflow 06 usa uma única credencial Query Auth no node HTTP.

Isso funciona quando o mesmo token/escopo técnico pode acessar os datasets configurados naquele deployment.

Se clientes exigirem tokens totalmente isolados, não grave os tokens na tabela `meta_hub_clientes`.

Use uma destas estratégias:

```text
A. um Workflow 06 por escopo de credencial
B. instâncias/ambientes isolados
C. futuro roteador de secrets/credentials
```

O desenho do banco permanece o mesmo.

---

# 40. Diagnóstico — evento não entrou na fila

Confira:

```sql
select
  chave_cliente,
  ativo,
  dataset_id,
  enviar_feedback_meta
from public.meta_hub_clientes;
```

Depois:

```sql
select
  evento_interno,
  evento_meta,
  habilitado
from public.meta_hub_mapa_eventos_meta;
```

E no lead:

```sql
select
  lead_externo_id,
  pode_compartilhar_meta,
  pode_usar_publico
from public.meta_hub_leads;
```

A causa normalmente estará em um dos gates.

---

# 41. Diagnóstico — Workflow 06 não encontra eventos

Confira:

```sql
select
  status,
  proxima_tentativa_em,
  tentativas,
  event_id
from public.meta_hub_fila_capi
order by criado_em desc;
```

O node busca apenas:

```text
pendente ou erro
+
proxima_tentativa_em vencida
+
cliente ativo
+
feedback habilitado
+
Dataset ID preenchido
```

---

# 42. Diagnóstico — HTTP 400 da Meta

Verifique primeiro:

```text
Dataset ID
Graph API version
access token
nome do evento
formatos event_time/action_source
user_data
custom_data
```

Abra o campo:

```text
ultimo_erro
```

e:

```text
resposta_meta
```

na fila CAPI antes de alterar o workflow.

---

# 43. Diagnóstico — events_received = 0

A versão atual só considera sucesso quando:

```text
HTTP 2xx
E
events_received >= 1
```

Se a Meta responder 2xx sem confirmar recebimento, o item permanece no fluxo de erro/retry para investigação.

---

# 44. Diagnóstico — evento recebido mas matching fraco

Revise a qualidade dos identificadores disponíveis:

```text
email
telefone com país
external_id
Meta lead ID quando disponível
fbc/fbp quando aplicáveis
outros sinais suportados pelo canal
```

Mais dados não significa inventar dados. Envie somente identificadores reais e permitidos.

---

# 45. Checklist antes de produção

## Banco

```text
[ ] migration 005 aplicada
[ ] migration 006 aplicada
[ ] cliente cadastrado
[ ] Dataset ID validado
[ ] mapa de eventos configurado
```

## Workflow 05

```text
[ ] importado
[ ] PostgreSQL configurado
[ ] Header Auth configurado
[ ] teste manual aprovado
[ ] retry do mesmo evento não duplica evento lógico
[ ] hashes conferidos
```

## Workflow 06

```text
[ ] importado
[ ] PostgreSQL configurado nos dois nodes
[ ] Query Auth Meta configurado
[ ] Test Event Code configurado
[ ] teste CAPI retorna events_received >= 1
[ ] evento aparece no Events Manager
[ ] fila muda para enviado
```

## Produção

```text
[ ] remover meta_test_event_code
[ ] validar primeiro evento real
[ ] ativar schedule 06
[ ] publicar/ativar webhook 05
[ ] acompanhar erros da fila
[ ] revisar retenção de execuções do n8n
```

---

# 46. Fluxo final

```text
SISTEMA DO CLIENTE
       ↓
lead qualificado / agendado / vendido
       ↓
POST /meta-ads-growth/v1/eventos
       ↓
05 | HUB DE EVENTOS DE LEADS
       ↓
PostgreSQL
  ↙          ↘
FUNIL       FILA CAPI
               ↓
06 | FEEDBACK PARA META
               ↓
Conversions API
               ↓
Events Manager / Dataset
               ↓
mensuração + sinais disponíveis para os recursos compatíveis da Meta
```

---

# 47. Próxima etapa

Depois de validar os módulos 05 e 06, implementar:

```text
META ADS | 07 | PÚBLICOS DE LEADS
```

com grupos como:

```text
qualificados
agendados
clientes
```

usando apenas leads com:

```text
pode_usar_publico = true
```

Essa etapa é separada do feedback CAPI e terá sua própria configuração de Custom Audiences, sincronização e auditoria.
