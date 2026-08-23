# DescompliADS — MVP SaaS

Branch ativa: `meta-ads-pro`.

Esta branch contém exclusivamente a evolução do Meta Ads Growth para o SaaS DescompliADS.

## Acesso ao sistema

- [Abrir o DescompliADS](https://descompliads.caza85imoveis.com.br/)

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

**Fase 10 — Frontend e inteligência**

O backend, a sincronização Meta, a observabilidade e a proteção por usuário e
cliente estão implementados. A primeira entrega da Fase 10 adiciona o frontend
Next.js autenticado e um dashboard visual somente leitura.

Documentação: `docs/fases/fase-10-frontend-inteligencia.md`.

## Branches

- `main`: base estável.
- `n8n-operacional`: sistema operacional atual em n8n.
- `meta-ads-pro`: desenvolvimento do MVP SaaS DescompliADS.

Não adicionar workflows operacionais do n8n diretamente nesta branch. Quando a integração com o SaaS for necessária, ela deve ser tratada como integração do produto e documentada na fase correspondente.
