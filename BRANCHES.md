# Estrutura oficial de branches

A `main` é a base estável do repositório. Desenvolvimento ativo deve ocorrer nas branches especializadas.

```text
main
├── base estável
│
├── n8n-operacional
│   └── sistema operacional atual
│       ├── coleta Meta Ads
│       ├── performance
│       ├── tendência/fadiga
│       ├── IA
│       └── Google Sheets
│
└── meta-ads-pro
    └── MVP SaaS DescompliADS
        ├── FastAPI
        ├── Supabase
        ├── API
        ├── Next.js
        └── inteligência
```

## main

Finalidade: referência estável. Não deve ser usada como branch de desenvolvimento diário.

## n8n-operacional

Contém a implementação operacional baseada em n8n. Está organizada por módulos e mantém versões antigas e módulos fora do fluxo atual em `arquivo/`.

## meta-ads-pro

Contém exclusivamente a evolução do MVP SaaS DescompliADS: backend FastAPI, API REST, Supabase, frontend Next.js e camada de inteligência.

## Regra

Mudanças do sistema atual ficam em `n8n-operacional`. Mudanças do SaaS ficam em `meta-ads-pro`. A `main` recebe apenas versões que forem deliberadamente promovidas como base estável.
