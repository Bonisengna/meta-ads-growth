# DescompliADS — MVP SaaS

Branch ativa: `meta-ads-pro`.

Esta branch contém exclusivamente a evolução do Meta Ads Growth para o SaaS DescompliADS.

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

1. Backend base — implementado e aguardando validação de deploy.
2. Supabase.
3. Modelo de dados.
4. Integração dos dados existentes.
5. API do dashboard.
6. Frontend Next.js.
7. Inteligência.
8. Melhorias e aprendizado.

## Branches

- `main`: base estável.
- `n8n-operacional`: sistema operacional atual em n8n.
- `meta-ads-pro`: desenvolvimento do MVP SaaS DescompliADS.

Não adicionar workflows operacionais do n8n diretamente nesta branch. Quando a integração com o SaaS for necessária, ela deve ser tratada como integração do produto e documentada na fase correspondente.
