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
- filtros de 7, 14, 30, 90, 120 e 180 dias;
- filtros por cliente, conta e campanha;
- indicadores e comparação com período anterior;
- visão da estrutura importada;
- nenhuma escrita ou alteração na Meta.

## Recuperação e alteração de senha

O frontend usa o Supabase Auth para dois fluxos:

- **Esqueci minha senha:** envia um link seguro por e-mail e abre a tela para
  criar uma nova senha;
- **Alterar senha:** disponível para o usuário autenticado em
  `Ajustes → Geral`.

Antes de publicar, abra o painel do Supabase em
`Authentication → URL Configuration` e configure:

```text
Site URL
https://descompliads.caza85imoveis.com.br

Redirect URLs
https://descompliads.caza85imoveis.com.br/?password-recovery=1
http://localhost:3000/?password-recovery=1
```

Em `Authentication → Providers`, mantenha o provedor **Email** habilitado.
Para produção, configure também um servidor SMTP próprio em
`Authentication → SMTP Settings`; o envio padrão do Supabase é limitado e não
deve ser tratado como serviço de e-mail de produção.

Opcionalmente, habilite o aviso de segurança de senha alterada nos modelos de
notificação do Auth. O DescompliADS nunca recebe nem armazena a senha em suas
tabelas: a atualização é feita diretamente pelo Supabase Auth.

## Login com Google

O botão **Continuar com Google** também usa o Supabase Auth. Para habilitá-lo:

1. No Google Auth Platform, crie um cliente OAuth do tipo **Web application**.
2. Cadastre `https://descompliads.caza85imoveis.com.br` como origem JavaScript.
3. Cadastre como URI de redirecionamento o callback exibido em
   `Supabase → Authentication → Providers → Google`.
4. Preencha o Client ID e o Client Secret nessa mesma tela do Supabase e
   habilite o provedor.
5. Inclua `https://descompliads.caza85imoveis.com.br/dashboard` e
   `http://localhost:3000/dashboard` na lista de URLs permitidas do Supabase.

Use apenas os escopos `openid`, `userinfo.email` e `userinfo.profile`. O Client
Secret do Google deve permanecer no Supabase e nunca pode ser incluído em
variáveis `NEXT_PUBLIC_*` ou no repositório.

Usuários novos ainda precisam ser vinculados a um cliente e a uma função antes
de acessar dados. O Google confirma a identidade; as permissões continuam sendo
determinadas pelo backend do DescompliADS.

## Tipografia e legibilidade

O sistema tipográfico prioriza **DIN Neuzeit Grotesk** nos títulos e **Avenir**
nos textos. Como essas famílias são comerciais, o código usa pilhas seguras de
substituição até que as webfonts licenciadas sejam fornecidas:

- títulos: DIN Neuzeit Grotesk, DIN Neuzeit, DIN 2014, Manrope e Segoe UI;
- textos: Avenir Next, Avenir, Inter, Segoe UI e Arial.

Não adicione arquivos `.woff` ou `.woff2` obtidos sem licença. Para ativar as
fontes exatas em todos os dispositivos, use uma licença web válida para o
domínio `descompliads.caza85imoveis.com.br` e uma destas opções:

1. kit web oficial do fornecedor, referenciado no layout do Next.js; ou
2. arquivos webfont licenciados, hospedados em `public/fonts` e registrados com
   `@font-face`.

Por acessibilidade, o peso Light não é usado em tabelas, filtros, formulários ou
textos pequenos. Nesses componentes, o peso regular preserva contraste e
legibilidade; o Light deve ficar restrito a textos de apoio maiores.
