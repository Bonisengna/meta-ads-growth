# Fase 8 — Segurança da API

## Arquitetura

```text
usuário → Supabase Auth → Bearer token → FastAPI → cliente Supabase autenticado → RLS
```

O backend valida cada sessão com `auth.get_user()`. As consultas de leitura usam
o token do usuário, não a chave secreta. A chave `SUPABASE_SECRET_KEY` permanece
restrita às sincronizações e tarefas internas.

## Primeiro usuário e vínculo

1. No Supabase, abra **Authentication → Users** e crie ou convide o usuário.
2. Copie o UUID do usuário e o UUID do cliente autorizado.
3. No SQL Editor, crie o vínculo:

```sql
insert into public.user_client_access (user_id, client_id, role)
values ('USER_UUID', 'CLIENT_UUID', 'OWNER');
```

Sem esse vínculo, um token válido recebe listas vazias e não consegue acessar
IDs de outro cliente. Não use `user_metadata` para autorização.

## Configuração do backend

```env
SUPABASE_PUBLISHABLE_KEY=sb_publishable_...
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
RATE_LIMIT_REQUESTS=60
RATE_LIMIT_WINDOW_SECONDS=60
```

A chave publicável fica em **Project Settings → API Keys**. Ela identifica o
projeto, mas não substitui o Bearer token do usuário.

## Teste no Swagger

Obtenha uma sessão pelo Supabase Auth. No `/docs`, clique em **Authorize** e
informe o access token. Depois execute `GET /api/v1/clients`.

Resultados esperados:

- sem token: HTTP 401;
- token inválido/expirado: HTTP 401;
- token válido sem vínculo: lista vazia ou HTTP 404 para um ID;
- token válido com vínculo: somente os dados do cliente autorizado.

Para testar sem copiar o token e sem colocar a senha no histórico do terminal,
execute com a API local em funcionamento:

```powershell
cd C:\Projetos\meta-ads-growth\backend
.\.venv\Scripts\python.exe scripts\smoke_auth.py --email seu-email@exemplo.com
```

A senha é solicitada de forma oculta e o token permanece somente em memória.
O resultado esperado contém `anonymous_request: 401`,
`authenticated_request: 200` e apenas os clientes autorizados.

## CORS e rate limiting

Somente origens listadas em `CORS_ALLOWED_ORIGINS` recebem autorização do
navegador. O limite inicial é 60 requisições por IP a cada 60 segundos e
retorna HTTP 429 com `Retry-After`.

O limitador atual é em memória e serve para uma única instância. No deploy com
múltiplos processos, deve ser substituído por um armazenamento compartilhado,
como Redis, ou aplicado no proxy reverso.

## Produção

```env
ENVIRONMENT=production
DEBUG=false
CORS_ALLOWED_ORIGINS=https://app.seudominio.com
```

A aplicação recusa inicialização em produção se `DEBUG=true` ou se o CORS usar
`*`. `.env`, tokens e chaves secretas permanecem ignorados pelo Git.

## System User da Meta

Antes da VPS:

1. crie um System User no Business Manager;
2. atribua somente as contas de anúncios necessárias;
3. use `ads_read` para leitura e adicione `business_management` apenas quando a
   enumeração/gestão dos ativos realmente exigir;
4. gere um token dedicado ao backend;
5. armazene-o somente como `META_ACCESS_TOKEN` no ambiente da VPS;
6. registre responsável, data de criação, validade e próxima rotação;
7. valide o token novo antes de revogar o anterior;
8. execute `sync_meta_all.py` e `/health/meta` após cada rotação.

Nunca coloque o token em commit, frontend, URL, log ou print de diagnóstico.

## Analogia

Supabase Auth é a identificação, `user_client_access` é a lista de salas
permitidas e RLS é a fechadura de cada sala. CORS é a lista de recepções
autorizadas e o rate limit controla quantas pessoas passam pela catraca.
