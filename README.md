# DescompliADS — MVP SaaS

Branch ativa: `meta-ads-pro`.

Esta branch contém exclusivamente a evolução do Meta Ads Growth para o SaaS DescompliADS.

## Acesso ao sistema

- [Abrir o DescompliADS](https://descompliads.caza85imoveis.com.br/)
- [Acompanhar gates, entregas e próximos passos](docs/ACOMPANHAMENTO_DO_PROJETO.md)

O acompanhamento acima é a fonte de verdade do projeto. Um gate seguinte só
entra em implementação depois que o anterior estiver marcado como concluído e
com suas evidências registradas.

## Estrutura

```text
backend/                  FastAPI + API REST
supabase/                 persistência e banco do SaaS
frontend/                 Next.js
inteligencia/             regras, análises e IA do produto
docs/
  arquitetura/
  fases/
  planejamento/
```

## Arquitetura alvo

```text
Meta Ads / integrações
        ↓
     Supabase
        ↓
FastAPI / API REST
        ↓
     Next.js
        ↓
   DescompliADS
```

## Próximas implementações — Configuração SaaS

A base de autenticação, isolamento por cliente, administradores do sistema,
credenciais protegidas e sincronização com a Meta já está implementada. Os
próximos itens recomendados para transformar a área de **Ajustes** em uma
estrutura SaaS completa são:

### Prioridade 1 — Administração e operação multi-cliente

- [ ] **Geral:** permitir configurar nome da empresa, logotipo, idioma, moeda,
  fuso horário e preferências de exibição.
- [ ] **Usuários:** convidar usuários, alterar funções, desativar acessos,
  reenviar convites e encerrar sessões.
- [ ] **Papéis e permissões:** consolidar os níveis `OWNER`, `ADMIN`, `ANALYST`
  e `VIEWER`, com uma matriz clara do que cada função pode visualizar ou alterar.
- [ ] **Clientes:** criar, editar e arquivar clientes sem apagar o histórico;
  vincular usuários e definir responsáveis por cada conta.
- [ ] **Onboarding:** criar um assistente com checklist para cadastrar o cliente,
  conectar a Meta, validar a conta de anúncios e realizar a primeira sincronização.
- [ ] **Meta Ads por cliente:** exibir teste de conexão, permissões encontradas,
  conta validada, moeda, fuso horário, última sincronização e ação
  **Sincronizar agora**.

### Prioridade 2 — Integrações e governança

- [ ] **Inteligência Artificial:** permitir selecionar modelo, testar a conexão,
  definir limite de uso e acompanhar consumo sem expor a chave no navegador.
- [ ] **Prompts privados:** manter criação, versão e alteração exclusivamente no
  ambiente dos desenvolvedores, sem formulário ou endpoint público no SaaS.
- [ ] **CRM:** configurar provedor, credenciais, etapas do funil e associação
  entre leads, vendas, receita e campanhas.
- [ ] **Webhooks:** cadastrar destinos, selecionar eventos, assinar requisições
  com segredo e registrar entregas, erros e novas tentativas.
- [ ] **Aplicativo Meta do sistema:** validar App ID, System User, versão da Graph
  API, validade do token e processo de rotação das credenciais de produção.
- [ ] **API e serviços:** apresentar estado dos serviços, limites de requisição e
  integrações ativas sem revelar segredos técnicos.
- [ ] **Auditoria:** registrar quem alterou usuários, clientes, permissões,
  integrações e configurações sensíveis.

### Prioridade 3 — Segurança, comercial e continuidade

- [ ] **Segurança da conta:** adicionar recuperação de senha, MFA, política de
  sessão e revisão dos dispositivos conectados.
- [ ] **Planos e limites:** definir planos, recursos disponíveis, quantidade de
  clientes, contas, usuários, histórico e sincronizações permitidas.
- [ ] **Assinatura e cobrança:** integrar cobrança, situação da assinatura,
  renovação, inadimplência e período de teste, quando o modelo comercial for definido.
- [ ] **Notificações:** avisar sobre token próximo do vencimento, falha de coleta,
  conta desatualizada, limite de uso e conclusão do onboarding.
- [ ] **Privacidade e ciclo de dados:** definir retenção, exportação, anonimização
  e exclusão controlada, preservando métricas históricas quando aplicável.
- [ ] **Backup e recuperação:** documentar restauração, rollback de deploy,
  rotação de segredos e resposta a incidentes.

### Regras permanentes

- Segredos nunca devem retornar ao frontend depois de salvos.
- Um usuário só pode acessar clientes aos quais esteja explicitamente vinculado.
- Entidades históricas devem ser marcadas como `ARCHIVED`, não apagadas.
- Qualquer alteração futura na Meta deve exigir autorização e aprovação humana.

A automação n8n operacional é mantida separadamente na branch `n8n-operacional`.

## Fases do MVP

1. Backend base — implementação inicial concluída; validação de deploy pendente.
2. Supabase — integração no código implementada; conexão com projeto exclusivo do DescompliADS pendente.
3. Modelo de dados.
4. Integração dos dados existentes.
5. API do dashboard.
6. Frontend Next.js.
7. Inteligência.
8. Melhorias e aprendizado.

## Fase atual

**Gate 2 — Confiabilidade da sincronização: em validação.**

O Gate 3 — Central operacional do gestor — está planejado, mas permanece
bloqueado até a conclusão formal do Gate 2. Consulte o
[acompanhamento oficial](docs/ACOMPANHAMENTO_DO_PROJETO.md) para ver entregas,
pendências, evidências e a regra de passagem entre gates.

## Branches

- `main`: base estável.
- `n8n-operacional`: sistema operacional atual em n8n.
- `meta-ads-pro`: desenvolvimento do MVP SaaS DescompliADS.

Não adicionar workflows operacionais do n8n diretamente nesta branch. Quando a integração com o SaaS for necessária, ela deve ser tratada como integração do produto e documentada na fase correspondente.
