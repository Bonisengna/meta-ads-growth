# Fase 2 — Motor de Performance

Status: em implementação.

Objetivo: calcular indicadores de performance de forma determinística antes da IA.

O motor deverá usar apenas registros da nova base diária identificados por `CHAVE REGISTRO`.

Indicadores previstos:

- custo por conversa;
- CTR;
- CTR de link;
- CPC;
- CPM;
- taxa clique → conversa;
- frequência;
- comparação com média da conta por nível e objetivo;
- score técnico de performance.

A Fase 2 não executará alterações automáticas de orçamento ou status. Ela apenas calcula e organiza os indicadores que alimentarão análises e decisões futuras.

Quando não houver dados diários, o workflow deverá retornar `SEM_DADOS_DIARIOS` sem falhar.