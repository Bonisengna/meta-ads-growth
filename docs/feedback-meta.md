# Feedback Meta e Públicos

Status: **guia de implementação do módulo independente de CRM**.

Documento principal:

```text
docs/modulo-independente-crm-meta.md
```

---

# 1. Workflows

```text
META ADS | 05 | HUB DE EVENTOS DE LEADS
META ADS | 06 | FEEDBACK PARA META
META ADS | 07 | PÚBLICOS DE LEADS
```

A ingestão é separada do envio à Meta. Se a Meta estiver indisponível, o HUB continua recebendo e registrando eventos.

---

# 2. Workflow 05 — HUB DE EVENTOS DE LEADS

Nodes planejados:

```text
RECEBE EVENTO DO SISTEMA
AUTENTICA INTEGRAÇÃO
NORMALIZA CONTRATO DO LEAD
VALIDA EVENTO DO FUNIL
PROTEGE IDENTIFICADORES
BUSCA CLIENTE DA INTEGRAÇÃO
BUSCA LEAD CANÔNICO
CRIA OU ATUALIZA LEAD
REGISTRA EVENTO DO FUNIL
PREPARA FILA CAPI
ATUALIZA ELEGIBILIDADE DE PÚBLICO
RESPONDE EVENTO RECEBIDO
```

Entrada sugerida:

```text
POST /meta-ads-growth/v1/eventos
```

Produção deve usar autenticação por integração/cliente. Nunca publicar webhook sem autenticação.

Campos mínimos:

```text
cliente
evento_externo_id
lead_externo_id
sistema_origem
evento
ocorrido_em
```

Eventos aceitos:

```text
conversa_iniciada
lead_identificado
lead_qualificado
agendamento
proposta
venda
desqualificado
```

O `evento_externo_id` torna o recebimento idempotente. Retry da origem não cria nova conversão lógica.

---

# 3. Identidade

Antes de persistir dados pessoais na camada de mídia:

```text
email → normalizar → SHA-256
telefone → normalizar → SHA-256
external_id → normalizar quando aplicável → SHA-256
```

Persistir hashes em:

```text
meta_hub_identificadores
```

Evitar e-mail e telefone em texto puro nesta camada.

Identificadores como `meta_lead_id`, `fbc`, `fbp` e `ctwa_clid` seguem as regras próprias da Meta e são preservados quando recebidos legitimamente.

---

# 4. Elegibilidade para CAPI

Criar item na fila apenas quando:

```text
cliente.enviar_feedback_meta = true
lead.pode_compartilhar_meta = true
mapeamento do evento está habilitado
```

O tracking interno continua funcionando mesmo quando o compartilhamento Meta está desligado.

---

# 5. Workflow 06 — FEEDBACK PARA META

Nodes:

```text
PROCESSA FILA CAPI
BUSCA EVENTOS PENDENTES
DIVIDE EVENTOS EM LOTES
MONTA USER DATA
MONTA EVENTO META
ENVIA PARA CONVERSIONS API
VALIDA RESPOSTA META
MARCA EVENTO ENVIADO
REGISTRA ERRO DE ENVIO
CALCULA NOVA TENTATIVA
```

Endpoint parametrizado:

```text
https://graph.facebook.com/{{$json.graph_api_version}}/{{$json.dataset_id}}/events
```

O token deve ficar em credencial segura do n8n/secret manager.

Não colocar access token:

```text
no JSON exportado
no GitHub
na tabela de clientes
em comentário do workflow
```

Body conceitual:

```json
{
  "data": [
    {
      "event_name": "EVENTO_META_CONFIGURADO",
      "event_time": 1786656600,
      "event_id": "cliente_001|lead_98342|lead_qualificado|20260813T183000",
      "action_source": "ORIGEM_VALIDA",
      "user_data": {
        "em": ["HASH_EMAIL"],
        "ph": ["HASH_TELEFONE"],
        "external_id": ["HASH_ID"],
        "lead_id": "META_LEAD_ID_SE_EXISTIR",
        "fbc": "FBC_SE_EXISTIR",
        "fbp": "FBP_SE_EXISTIR"
      },
      "custom_data": {
        "etapa_interna": "lead_qualificado",
        "score_qualificacao": 82
      }
    }
  ]
}
```

Remover campos vazios antes do POST.

`action_source` deve refletir a origem real e usar um valor permitido pela versão corrente da API.

---

# 6. Event ID

O mesmo evento lógico mantém o mesmo `event_id` em todas as tentativas.

Errado:

```text
retry 1 → UUID A
retry 2 → UUID B
retry 3 → UUID C
```

Correto:

```text
retry 1 → evento_123
retry 2 → evento_123
retry 3 → evento_123
```

---

# 7. Event time

Enviar o horário real da ação comercial.

```text
lead qualificou 16:42
CAPI ficou indisponível
retry 17:10

EVENT_TIME = 16:42
```

Não substituir pelo horário do retry.

---

# 8. Teste no Events Manager

Antes de produção:

1. confirmar `dataset_id`;
2. abrir Events Manager;
3. usar o recurso de Test Events disponível na conta;
4. obter o código de teste quando aplicável;
5. ligar `modo_teste` na configuração do HUB;
6. enviar evento fictício autorizado;
7. confirmar recebimento;
8. revisar parâmetros e matching;
9. desligar `modo_teste`;
10. habilitar produção.

O código de teste nunca deve permanecer fixo no workflow de produção.

---

# 9. Retry

Política inicial sugerida:

```text
1ª tentativa → imediata
2ª tentativa → +5 min
3ª tentativa → +30 min
4ª tentativa → +2 h
5ª tentativa → +12 h
```

Depois disso:

```text
status = erro
revisão manual
```

Não usar loop rápido contra a API.

Antes de reenviar eventos antigos, validar a janela temporal aceita pela versão atual da Conversions API para aquele tipo de evento.

---

# 10. Conversion Leads

Para campanhas de Leads com Instant Forms, a Meta oferece atualmente o performance goal de maximizar conversion leads quando dados posteriores são enviados pela integração de Conversions API.

Isso permite que a plataforma aprenda com o que o negócio considera um lead de maior qualidade.

Não assumir que o mesmo modo de otimização existe para todos os destinos.

Para WhatsApp/Messenger/outros canais:

```text
enviar eventos reais
medir qualidade
confirmar no Ads Manager quais objetivos/performance goals estão elegíveis
```

---

# 11. Workflow 07 — PÚBLICOS DE LEADS

Primeira versão:

```text
Custom Audience é criado/autorizado na conta Meta correta
       ↓
ID do público é salvo no HUB
       ↓
n8n sincroniza somente membros
```

Nodes:

```text
SINCRONIZA PÚBLICOS
BUSCA PÚBLICOS ATIVOS
BUSCA MEMBROS PENDENTES
VALIDA USO DO LEAD EM PÚBLICO
MONTA LOTE DE HASHES
ENVIA MEMBROS PARA META
VALIDA RESPOSTA META
ATUALIZA STATUS DO MEMBRO
```

---

# 12. Públicos iniciais

## QUALIFICADOS

```text
evento = lead_qualificado
pode_usar_publico = true
```

## AGENDADOS

```text
evento = agendamento
pode_usar_publico = true
```

## CLIENTES

```text
evento = venda
pode_usar_publico = true
```

## DESQUALIFICADOS

Não usar automaticamente para targeting.

Podem ser úteis futuramente para análise ou exclusão, desde que exista motivo estratégico e uso permitido.

---

# 13. Customer List Custom Audience

Fluxo:

```text
lead elegível
     ↓
identificadores permitidos
     ↓
normalização local
     ↓
SHA-256 local
     ↓
Custom Audience
```

A Meta exige que dados de Customer List Custom Audiences sejam hashados localmente antes da transmissão e que o anunciante possua direitos, permissões e base legal aplicável para o uso.

O HUB mantém dois gates diferentes:

```text
pode_compartilhar_meta
pode_usar_publico
```

Compartilhar evento de conversão e usar pessoa em público não são tratados como a mesma autorização interna.

---

# 14. Adicionar membros

A Marketing API possui operação de usuários de Custom Audience.

Conceitualmente:

```text
POST /<CUSTOM_AUDIENCE_ID>/users
```

com os identificadores hashados no formato suportado pela versão atual.

Na implementação final, validar o schema na versão Graph configurada em `meta_hub_clientes.graph_api_version`.

Não copiar exemplos antigos com versão fixa para produção.

---

# 15. Remover membros

Quando um membro deixar de ser elegível, usar a operação de remoção suportada pela versão corrente e registrar:

```text
status = removido
sincronizado_em
resposta/erro
```

Isso permite manter o público sincronizado ao longo do tempo.

---

# 16. Criação automática de audiência

Fora da primeira versão.

Primeiro vamos criar/autorizar o público na interface Meta e salvar seu ID.

Depois de estabilizado, poderemos automatizar a criação via Marketing API.

Motivos para começar manualmente:

```text
termos da conta correta
permissões por cliente
auditoria simples
evitar criação acidental de públicos
```

---

# 17. Lookalike / sinais Advantage+

Quando houver volume e matching suficientes, públicos de alta qualidade poderão servir como fontes/sinais para estratégias suportadas pela conta, como Lookalike ou sugestões de audiência Advantage+.

Prioridade de qualidade:

```text
CLIENTES
AGENDADOS
QUALIFICADOS
```

Não definir automaticamente “conversou = público de qualidade”.

A Meta deve informar se o público possui tamanho/matching suficiente para uso.

---

# 18. Ciclo de melhoria

```text
ANÚNCIO
  ↓
LEAD
  ↓
HUB
  ↓
QUALIFICAÇÃO
  ↓
EVENTO DE QUALIDADE
  ├──────────────→ 06 FEEDBACK CAPI
  │                     ↓
  │                  META
  │                     ↓
  │            melhor sinal de negócio
  │
  └──────────────→ 07 PÚBLICOS
                        ↓
                 QUALIFICADOS/CLIENTES
```

O Motor de Decisão usará os mesmos eventos internamente, independentemente de a Meta aceitar ou não o evento para otimização.

---

# 19. Permissões e multi-cliente

Para gerenciar contas de clientes, a Meta App deve possuir o nível de acesso e permissões exigidos pela versão corrente da Marketing API.

O projeto deve considerar:

```text
ads_read
ads_management
acesso aos ativos do cliente
credencial/token correto
```

Ao atuar em contas de terceiros, revisar Advanced Access e permissões antes de produção.

Cada cliente deve possuir configuração isolada.

Nunca usar um único `dataset_id`, público ou conta de anúncio por engano para todos.

---

# 20. Checklist

```text
[ ] cliente registrado
[ ] webhook autenticado
[ ] contrato validado
[ ] idempotência validada
[ ] hashing validado
[ ] dataset confirmado
[ ] credencial Meta configurada
[ ] evento de teste recebido pela Meta
[ ] retry validado
[ ] público de qualificados criado/autorizado
[ ] custom_audience_id salvo
[ ] membro de teste sincronizado
[ ] remoção testada
[ ] isolamento multi-cliente validado
[ ] logs revisados para evitar PII desnecessária
```

Somente depois disso habilitar produção.