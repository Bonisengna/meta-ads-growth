# Configuração da Meta Marketing API

Guia para configurar com segurança as credenciais usadas pelo backend do
DescompliADS, validar o acesso e preparar a sincronização de dados.

## 1. Pré-requisitos

É necessário ter:

- conta no [Meta for Developers](https://developers.facebook.com/);
- aplicativo Meta com o produto ou caso de uso Marketing API;
- acesso de anunciante à conta de anúncios que será consultada;
- token com a permissão `ads_read`;
- ambiente Python do backend instalado e funcionando;
- conexão do backend com o Supabase já validada.

A coleção oficial da Meta também relaciona como pré-requisitos um aplicativo,
um token, permissões adequadas e acesso a uma conta de anúncios:
[Meta Marketing API no Postman](https://www.postman.com/meta/facebook-marketing-api/documentation/0zr4mes/facebook-marketing-api-mapi).

## 2. Localizar App ID e App Secret

1. Acesse [Meus aplicativos](https://developers.facebook.com/apps/).
2. Abra o aplicativo usado pelo DescompliADS.
3. Entre em **Configurações > Básico** (`Settings > Basic`).
4. Copie o **ID do aplicativo** para `META_APP_ID`.
5. Clique em **Mostrar** na **Chave secreta do aplicativo**.
6. Copie o valor para `META_APP_SECRET`.

O App Secret é uma credencial de servidor. Nunca:

- enviar por chat ou e-mail;
- colocar no frontend;
- inserir em URLs;
- registrar em logs;
- salvar em arquivos versionados pelo Git.

## 3. Gerar um token de desenvolvimento

Para o primeiro teste, gere um token de usuário pelo painel do aplicativo ou
pelo [Graph API Explorer](https://developers.facebook.com/tools/explorer/):

1. selecione o aplicativo correto;
2. gere um token de usuário;
3. solicite a permissão `ads_read`;
4. adicione `business_management` somente se necessário;
5. confirme que o usuário do token possui acesso à conta de anúncios.

Tokens de desenvolvimento podem expirar. Eles servem para validar a integração,
mas não devem ser tratados como credenciais permanentes de produção.

## 4. Permissões mínimas

### `ads_read`

É a permissão mínima para a fase atual. Permite consultar contas, campanhas,
conjuntos, anúncios e métricas disponíveis ao usuário do token.

### `business_management`

Pode ser necessária quando:

- a conta pertence a um portfólio empresarial;
- os ativos são administrados pelo Business Manager;
- a listagem de contas retorna vazia mesmo com acesso confirmado;
- o fluxo precisa consultar ativos empresariais relacionados.

Não solicitar `business_management` sem necessidade comprovada.

### `ads_management`

Não é necessária para as leituras atuais. Deve ser considerada apenas quando o
sistema passar a criar ou alterar campanhas na Meta.

## 5. Preencher o `backend/.env`

Na pasta `backend/`, copie `.env.example` para `.env` caso o arquivo ainda não
exista. O arquivo `.env` já está protegido pelo `.gitignore`.

Preencha:

```env
META_GRAPH_BASE_URL=https://graph.facebook.com
META_GRAPH_VERSION=v25.0
META_ACCESS_TOKEN=COLE_O_TOKEN_SOMENTE_AQUI
META_APP_ID=COLE_O_ID_DO_APLICATIVO
META_APP_SECRET=COLE_O_SEGREDO_SOMENTE_AQUI
META_REQUEST_TIMEOUT_SECONDS=30
```

Regras:

- não usar aspas;
- não deixar espaços ao redor do `=`;
- não adicionar comentários na mesma linha dos valores;
- nunca copiar o `.env` para o frontend;
- nunca executar `git add -f backend/.env`;
- reiniciar a FastAPI depois de modificar o arquivo.

## 6. Validar o token sem sincronização

Na pasta `backend/`, execute:

```powershell
.\.venv\Scripts\python.exe scripts\smoke_meta.py --validate
```

Esse comando:

- consulta o `debug_token` da Meta;
- não imprime o token;
- não grava dados no Supabase;
- não cria nem altera campanhas.

Resultado esperado:

```json
{
  "is_valid": true,
  "app_id": "ID_DO_APLICATIVO",
  "type": "USER",
  "expires_at": 0,
  "scopes": ["ads_read"]
}
```

Os valores podem variar. O ponto essencial é `"is_valid": true` e a presença
das permissões necessárias.

## 7. Listar contas acessíveis

Depois que o token for validado:

```powershell
.\.venv\Scripts\python.exe scripts\smoke_meta.py --list-accounts
```

Confirme que a conta desejada aparece no resultado. O identificador pode vir
como `account_id` sem prefixo ou como `id` iniciado por `act_`. O backend aceita
os dois formatos.

Esse comando é somente leitura e ainda não sincroniza dados com o Supabase.

## 8. Diagnóstico de erros comuns

| Problema | Causa provável | Ação recomendada |
| --- | --- | --- |
| `is_valid: false` | Token expirado, revogado ou inválido | Gerar outro token no aplicativo correto |
| App ID incompatível | Token gerado para outro aplicativo | Selecionar o mesmo aplicativo no Graph API Explorer |
| Erro de permissão | `ads_read` ausente | Gerar token incluindo `ads_read` |
| Lista de contas vazia | Usuário sem acesso ao ativo | Conferir acesso no Ads Manager e Business Manager |
| Lista vazia com acesso confirmado | Ativo empresarial não visível | Avaliar `business_management` |
| HTTP 400 | Parâmetro ou versão incompatível | Conferir mensagem e `META_GRAPH_VERSION` |
| HTTP 401 | Token inválido ou expirado | Validar novamente e substituir o token |
| HTTP 403 | Permissão ou acesso ao ativo insuficiente | Revisar scopes e função do usuário |
| Timeout | Rede ou indisponibilidade temporária | Testar conexão e repetir de forma controlada |

Nunca publicar a resposta completa de erros se ela contiver URLs com tokens ou
outros dados sensíveis.

## 9. Sincronizar hierarquia

Somente depois de validar o token e confirmar a conta:

```powershell
.\.venv\Scripts\python.exe scripts\smoke_meta.py --sync-account ACCOUNT_ID --client-id CLIENT_UUID
```

Onde:

- `ACCOUNT_ID` é o identificador da conta Meta, com ou sem `act_`;
- `CLIENT_UUID` é o UUID do cliente já existente no Supabase.

O processo usa `UPSERT`: registros existentes são atualizados e novos registros
são inseridos. Campanhas, conjuntos e anúncios ausentes ou não ativos passam a
`ARCHIVED`; nenhum histórico é apagado.

## 10. Coletar métricas diárias

Depois da sincronização da hierarquia:

```powershell
.\.venv\Scripts\python.exe scripts\smoke_meta.py --metrics ACCOUNT_ID --date 2026-08-15
```

As métricas usam `UPSERT` por entidade e data. Executar novamente para a mesma
data atualiza o registro existente, evitando duplicação.

## 11. System User em produção

Para produção, prefira um System User administrado no Meta Business Manager:

1. crie ou selecione um System User dedicado à integração;
2. conceda acesso somente às contas necessárias;
3. use apenas as permissões mínimas;
4. gere um token apropriado para o ambiente de produção;
5. armazene-o no gerenciador de secrets da VPS;
6. nunca copie o `.env` local diretamente para a VPS;
7. defina processo de rotação e revogação;
8. monitore falhas de autenticação e expiração.

O token de produção deve pertencer à integração, não depender da sessão pessoal
de um desenvolvedor e não ser reutilizado em outros sistemas.

## Checklist antes da primeira sincronização

- [ ] Aplicativo Meta correto selecionado.
- [ ] Marketing API habilitada.
- [ ] `META_APP_ID` e `META_APP_SECRET` configurados localmente.
- [ ] Token com `ads_read`.
- [ ] Token validado com `is_valid: true`.
- [ ] Conta desejada aparece em `--list-accounts`.
- [ ] Cliente correspondente já existe no Supabase.
- [ ] Testes automatizados do backend aprovados.
- [ ] Nenhum segredo aparece no Git ou nos logs.
