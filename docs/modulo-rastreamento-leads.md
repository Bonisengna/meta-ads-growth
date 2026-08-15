# Módulo de Rastreamento de Leads

Status: **substituído pela arquitetura independente de CRM**.

A especificação oficial a partir desta versão está em:

```text
docs/modulo-independente-crm-meta.md
```

O desenho anterior tratava principalmente da ligação `lead → anúncio → funil`.

O novo HUB mantém essa responsabilidade e acrescenta:

```text
entrada padronizada de qualquer sistema
+ rastreamento e atribuição
+ histórico do funil
+ feedback de qualidade para Meta via Conversions API
+ fila idempotente com retry
+ Customer Audiences de leads elegíveis
+ preparação para Lookalike / sinais de audiência
+ isolamento por cliente
+ regras de privacidade e hashing
```

Arquitetura atual:

```text
QUALQUER CRM / WHATSAPP / FORM / ERP / PLANILHA
                     ↓
        META ADS | 05 | HUB DE EVENTOS
                     ↓
        ┌────────────┴────────────┐
        ↓                         ↓
06 | FEEDBACK PARA META     07 | PÚBLICOS DE LEADS
        ↓                         ↓
Conversions API             Custom Audiences
```

Banco complementar:

```text
database/005-cria-hub-feedback-meta.sql
```

A migration `004-cria-rastreamento-leads.sql` permanece no histórico do projeto como primeira modelagem do tracking. Antes de aplicar migrations em produção, consolidaremos 004 e 005 para evitar estruturas redundantes.