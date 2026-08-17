# Frontend — Next.js

Primeira entrega da Fase 10 do DescompliADS: login Supabase e dashboard visual
somente leitura consumindo a FastAPI.

## Configuração local

Copie `.env.local.example` para `.env.local` e preencha somente valores
publicáveis:

```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
NEXT_PUBLIC_SUPABASE_URL=https://seu-projeto.supabase.co
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=sb_publishable_...
```

Nunca use `SUPABASE_SECRET_KEY`, `service_role`, `META_ACCESS_TOKEN` ou qualquer
outro segredo no frontend.

## Execução

```powershell
pnpm install
pnpm dev
```

Abra `http://localhost:3000`, entre com o usuário criado na Fase 8 e mantenha a
FastAPI local em `http://127.0.0.1:8000`.

## Escopo

- autenticação por e-mail e senha;
- sessão Supabase persistida no navegador;
- chamadas FastAPI com Bearer token;
- filtros de 7, 14, 30, 90 e 120 dias;
- filtros por cliente, conta e campanha;
- indicadores e comparação com período anterior;
- visão da estrutura importada;
- nenhuma escrita ou alteração na Meta.
