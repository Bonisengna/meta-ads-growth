# Supabase — DescompliADS

Área de persistência do MVP SaaS na branch `meta-ads-pro`.

## Fase 2

A integração base FastAPI ↔ Supabase já está implementada no código.

Estrutura atual:

```text
supabase/
├── README.md
└── migrations/
    └── 0001_app_health.sql
```

A migration `0001_app_health.sql` cria somente uma tabela técnica para validar leitura e escrita antes do modelo de negócio.

## Segurança

- o backend usa `SUPABASE_SECRET_KEY` via variável de ambiente;
- a chave real nunca deve ser commitada;
- frontend/Next.js não deve receber essa chave;
- `app_health` mantém RLS habilitado;
- `anon` e `authenticated` não recebem acesso à tabela técnica nesta fase.

## Projeto do banco

O DescompliADS deve utilizar um projeto Supabase próprio. Não reutilizar automaticamente bancos de outros sistemas nem as migrations antigas da branch `n8n-operacional`.

## Próxima etapa dentro do Supabase

Depois de selecionar/criar o projeto exclusivo do DescompliADS:

1. aplicar `migrations/0001_app_health.sql`;
2. configurar `SUPABASE_URL` e `SUPABASE_SECRET_KEY` no backend;
3. executar `python scripts/smoke_supabase.py`;
4. executar `python scripts/smoke_supabase.py --write`;
5. validar `GET /health/database`.

Documentação completa: `../docs/fases/fase-2-supabase.md`.
