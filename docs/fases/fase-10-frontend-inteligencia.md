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
- períodos de 7, 14, 30, 90 e 120 dias;
- filtros por cliente, conta e campanha;
- contagem de campanhas, conjuntos e anúncios;
- campanhas ativas e arquivadas;
- layout responsivo;
- estado de erro quando a FastAPI estiver indisponível;
- nenhuma alteração automática na Meta.

## Próximas entregas

1. métricas por campanha e série temporal;
2. ranking de campanhas, conjuntos e anúncios;
3. regras determinísticas de diagnóstico;
4. recomendações explicáveis e priorizadas;
5. registro de aceite, rejeição e resultado;
6. IA para explicar e resumir, nunca para alterar campanhas sem aprovação.

## Analogia

O backend é a cozinha que prepara os dados e aplica as regras de acesso. O
frontend é o salão: organiza e apresenta o que já foi preparado. A inteligência
será o analista que explica o prato; ela não troca os ingredientes sem autorização.
