# Meta Ads Growth — n8n Operacional

Esta branch contém o sistema operacional atual baseado em n8n.

## Fluxo operacional

```text
Coleta Meta Ads
      ↓
Performance
      ↓
Tendência / Fadiga
      ↓
Analista IA
      ↓
Google Sheets / Dashboard
```

## Estrutura

```text
coleta-meta-ads/
performance/
tendencia-fadiga/
ia/
google-sheets/
arquivo/
```

Cada módulo contém o workflow recomendado, documentação e, quando aplicável, SQL de apoio.

`arquivo/` preserva versões anteriores e módulos que não fazem parte do fluxo operacional atual.

## Branches do repositório

- `main`: base estável.
- `n8n-operacional`: sistema operacional atual em n8n.
- `meta-ads-pro`: MVP SaaS DescompliADS.

## Regra de manutenção

Mudanças do sistema n8n devem ser desenvolvidas e validadas nesta branch antes de qualquer promoção para `main`.
