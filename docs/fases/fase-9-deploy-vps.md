# Fase 9 — Deploy na VPS com EasyPanel

Este documento prepara a publicação do DescompliADS em dois serviços separados
no mesmo projeto do EasyPanel:

```text
Navegador
   ↓ HTTPS
frontend (Next.js, porta 3000)
   ↓ HTTPS
backend (FastAPI, porta 8000)
   ↓
Supabase + Meta Graph API
```

## Antes de publicar

- utilizar `descompliads.caza85imoveis.com.br` para o frontend e
  `api.descompliads.caza85imoveis.com.br` para o backend;
- apontar os registros DNS para o IPv4 da VPS;
- manter as portas 80 e 443 liberadas;
- confirmar que o repositório privado está acessível pelo EasyPanel;
- nunca copiar arquivos `.env` para o GitHub.

## Serviço do backend

No EasyPanel, crie um projeto `descompliads` e um serviço App `backend`.

- Source: GitHub;
- Repository: `Bonisengna/meta-ads-growth`;
- Branch: `meta-ads-pro`;
- Build Path: `/backend`;
- Builder: Dockerfile;
- Dockerfile: `Dockerfile`;
- Target port do domínio: `8000`;
- domínio: `api.descompliads.caza85imoveis.com.br` com HTTPS.

Cadastre as variáveis do `backend/.env.example` na área Environment. Para
produção, use obrigatoriamente:

```text
ENVIRONMENT=production
DEBUG=false
CORS_ALLOWED_ORIGINS=https://descompliads.caza85imoveis.com.br
```

As chaves `SUPABASE_SECRET_KEY`, `META_ACCESS_TOKEN` e `META_APP_SECRET` existem
somente neste serviço. Não devem ser usadas como argumentos de build, exibidas
em logs ou cadastradas no frontend.

Depois do deploy, valide:

```text
https://api.descompliads.caza85imoveis.com.br/health
https://api.descompliads.caza85imoveis.com.br/api/v1/health/meta
```

## Serviço do frontend

Crie outro serviço App chamado `frontend`.

- Source: GitHub;
- Repository: `Bonisengna/meta-ads-growth`;
- Branch: `meta-ads-pro`;
- Build Path: `/frontend`;
- Builder: Dockerfile;
- Dockerfile: `Dockerfile`;
- Target port do domínio: `3000`;
- domínio: `descompliads.caza85imoveis.com.br` com HTTPS.

Cadastre somente valores públicos:

```text
NEXT_PUBLIC_API_URL=https://api.descompliads.caza85imoveis.com.br
NEXT_PUBLIC_SUPABASE_URL=https://SEU-PROJETO.supabase.co
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=sb_publishable_...
```

Como variáveis `NEXT_PUBLIC_` entram no pacote gerado pelo Next.js, qualquer
alteração nelas exige um novo build/deploy do frontend.

## Supabase Auth

Em Authentication → URL Configuration:

```text
Site URL: https://descompliads.caza85imoveis.com.br
Redirect URLs:
https://descompliads.caza85imoveis.com.br/**
http://localhost:3000/**
```

Use endereço exato em produção. O localhost permanece apenas para desenvolvimento.
A chave publicável pode estar no navegador; a chave secreta nunca pode.

## Ordem segura de publicação

1. configurar e publicar o backend;
2. validar `/health` e `/api/v1/health/meta`;
3. configurar e publicar o frontend;
4. ajustar Site URL e Redirect URLs do Supabase;
5. entrar pelo domínio HTTPS;
6. confirmar `401` sem autenticação e `200` com autenticação;
7. habilitar Auto Deploy somente depois de todo o fluxo estar estável.

## Rollback

Se uma publicação falhar, abra Deployments no EasyPanel e retorne à implantação
anterior. Não altere nem apague as tabelas do Supabase durante um rollback da
aplicação.

## Analogia

O EasyPanel é o condomínio, o backend é a cozinha e o frontend é a recepção.
Cada serviço possui sua própria chave e sua própria porta. O proxy HTTPS funciona
como a portaria: recebe os visitantes pelo domínio certo e os encaminha sem
expor diretamente o interior da VPS.
