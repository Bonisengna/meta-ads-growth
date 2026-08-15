# Teste da Fase 2 — Motor de Performance

Workflow recomendado:

`workflows/02-motor-performance-v2.json`

A v2 inclui um caminho manual com dados fictícios. Esses dados não são gravados no Google Sheets e não alteram campanhas.

Fluxo de teste:

`TESTE MANUAL` → `GERA DADOS DE TESTE` → `CALCULA INDICADORES DE PERFORMANCE` → `CONSOLIDA RESUMO DE PERFORMANCE`

Resultados esperados aproximados:

- ANUNCIO_A: score 90
- ANUNCIO_B: score 28
- ANUNCIO_C: score 20
- score técnico médio: 46

O caminho de produção roda às 05:00 e lê apenas registros com `CHAVE REGISTRO`. Sem campanhas recentes, o resultado correto é `SEM_DADOS_DIARIOS`.

O benchmark compara somente objetos do mesmo dia, conta, nível e objetivo. O score técnico varia de 0 a 100 e usa custo por conversa, CTR de link, CPC e taxa clique → conversa. Ele mede eficiência técnica e não qualidade comercial do lead.

A frequência é calculada por `impressões / alcance`. O índice de gasto atual compara o investimento do objeto com o investimento médio do grupo. Tendência temporal e fadiga ficam para a Fase 3.

A migration `database/002-cria-views-performance.sql` contém as views equivalentes para PostgreSQL/Supabase e ainda não foi aplicada em produção.