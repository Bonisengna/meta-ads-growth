# Estrutura de branches

## `main`

Base estável do repositório. Não é a branch de desenvolvimento diário.

## `n8n-operacional`

Sistema operacional atual baseado em n8n.

Estrutura principal:

```text
coleta-meta-ads/
performance/
tendencia-fadiga/
ia/
google-sheets/
arquivo/
```

A pasta `arquivo/` preserva versões anteriores, workflows originais e os módulos 05/06 de tracking/feedback que não fazem parte do fluxo operacional atual.

## `meta-ads-pro`

Trilha oficial de desenvolvimento do MVP SaaS **DescompliADS**.

Estrutura principal:

```text
backend/        FastAPI + API REST
supabase/       banco e persistência do SaaS
frontend/       Next.js
inteligencia/   camada analítica e IA
docs/           arquitetura, fases e planejamento
```

## Regra de uso

- mudanças do sistema n8n atual → `n8n-operacional`;
- mudanças do SaaS DescompliADS → `meta-ads-pro`;
- promoção deliberada de uma base estável → `main`.

O `meta-ads-pro` não deve manter cópias dos workflows operacionais como segunda fonte de verdade. Quando a integração n8n entrar no MVP, ela será tratada como uma integração do SaaS na fase correspondente.

## Roadmap do SaaS

1. Backend base;
2. Supabase;
3. Modelo de dados;
4. Integração dos dados existentes;
5. API do dashboard;
6. Frontend Next.js;
7. Inteligência e diagnósticos;
8. Melhorias e aprendizado.

## Segurança

Não versionar `.env` real, chaves do Supabase, tokens Meta, credenciais n8n ou secrets de produção.
