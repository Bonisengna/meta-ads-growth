# Fase 10 — Frontend e inteligência

## Primeira entrega

A primeira entrega cria um frontend Next.js somente leitura sobre a FastAPI já
protegida. A aplicação autentica no Supabase, envia o access token no header
Bearer e deixa a RLS limitar os clientes visíveis.

```text
Login Supabase
      ↓
Access token em sessão
      ↓
FastAPI autenticada
      ↓
RLS por user_client_access
      ↓
Dashboard do cliente permitido
```

O frontend nunca recebe `service_role`, chave secreta do Supabase, App Secret
ou token Meta. Apenas URL e chave publicável usam o prefixo `NEXT_PUBLIC_`.

## Funcionalidades

- login e logout;
- investimento, conversas, leads, CPL, CTR e CPC;
- comparação com o período anterior;
- períodos de 7, 14, 30, 90, 120, 180 e 360 dias;
- filtros por cliente, conta e campanha;
- contagem de campanhas, conjuntos e anúncios;
- campanhas ativas e arquivadas;
- layout responsivo;
- estado de erro quando a FastAPI estiver indisponível;
- nenhuma alteração automática na Meta.

## Segunda entrega

- evolução diária do investimento;
- ranking agregado de campanhas com entrega;
- custo por conversa por campanha;
- diagnósticos determinísticos com código e severidade;
- limites mínimos de volume para reduzir conclusões precipitadas;
- uma única resposta autenticada do dashboard, sem ampliar acesso no banco.

## Evolução visual para produção

- tema escuro inspirado em painéis operacionais;
- contraste reforçado para métricas e tabelas;
- cartões em camadas, navegação discreta e destaques por categoria;
- preservação da identidade coral da DescompliADS;
- imagem de referência usada apenas como direção visual, sem copiar marca ou
  componentes de terceiros.

## Navegação por rotas

As áreas principais possuem URLs próprias e podem ser abertas, atualizadas e
compartilhadas sem perder o contexto atual:

- `/dashboard`: visão geral e prioridades do período;
- `/campaigns`: métricas e rankings por estrutura;
- `/analyses`: diagnóstico do funil e decisões assistidas;
- `/settings`: conta, integrações e segurança.

Os filtros de período, cliente, conta e campanha são mantidos como parâmetros
da URL. A navegação respeita os botões voltar e avançar do navegador, e a rota
raiz redireciona para `/dashboard` preservando os filtros selecionados.

## Próximas entregas

1. ranking de conjuntos e anúncios;
2. recomendações explicáveis e priorizadas;
3. registro de aceite, rejeição e resultado;
4. IA para explicar e resumir, nunca para alterar campanhas sem aprovação.

## Analogia

O backend é a cozinha que prepara os dados e aplica as regras de acesso. O
frontend é o salão: organiza e apresenta o que já foi preparado. A inteligência
será o analista que explica o prato; ela não troca os ingredientes sem autorização.
