# Branch meta-ads-pro

## Objetivo

A branch `meta-ads-pro` passa a ser a trilha oficial de desenvolvimento do MVP SaaS do **DescompliADS**.

Ela foi sincronizada a partir do estado atual da branch `desenvolvimento` após a implementação inicial da **Fase 1 — Backend base**.

## Regra de uso

A partir desta migração:

- `main` continua como branch estável do repositório;
- `desenvolvimento` preserva o histórico e a evolução dos fluxos anteriores do projeto Meta Ads Growth;
- `meta-ads-pro` concentra a evolução do MVP SaaS DescompliADS.

## Escopo do MVP SaaS nesta branch

As próximas fases devem ser desenvolvidas em `meta-ads-pro`:

1. Backend base;
2. Supabase;
3. Modelo de dados;
4. Integração n8n com o modelo SaaS;
5. API do dashboard;
6. Frontend Next.js;
7. Inteligência e diagnósticos;
8. Melhorias e aprendizado.

## Estado inicial da migração

A branch foi posicionada no mesmo commit que representava o estado atual de `desenvolvimento` após a Fase 1:

```text
2f30abde9d6ebce4ff3b179dc1f6a4b66600d4f0
```

Isso inclui, entre outros arquivos:

```text
backend/
README.md
docs/fase-1-backend.md
workflows/
database/
```

## Próximo passo

Antes de iniciar a Fase 2, validar o backend da Fase 1 em ambiente real de desenvolvimento/deploy.

Depois disso, a **Fase 2 — Supabase** deve ser implementada diretamente na branch `meta-ads-pro`.

## Segurança

Não versionar:

- `.env` real;
- chaves do Supabase;
- tokens Meta;
- credenciais n8n;
- secrets de produção.

Apenas arquivos de exemplo, como `.env.example`, devem permanecer no GitHub.
