# Fase 1 — Backend base

Status: **implementação inicial concluída na branch `desenvolvimento`; validação no ambiente de deploy ainda pendente**.

## Objetivo

Criar a base do backend Python/FastAPI do DescompliADS sem antecipar responsabilidades das fases seguintes.

Esta fase cobre:

- aplicação FastAPI;
- endpoints básicos de saúde;
- configuração por variáveis de ambiente;
- estrutura modular por rotas, serviços, modelos e persistência;
- testes automatizados;
- Dockerfile.

A conexão real com Supabase/PostgreSQL pertence à **Fase 2**.

## Estrutura criada

```text
backend/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── health.py
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py
│   ├── database/
│   │   └── __init__.py
│   ├── models/
│   │   └── __init__.py
│   └── services/
│       └── __init__.py
├── tests/
│   ├── __init__.py
│   └── test_health.py
├── .env.example
├── Dockerfile
├── pytest.ini
├── requirements.txt
└── requirements-dev.txt
```

## Endpoints implementados

```http
GET /
GET /health
GET /api/v1/health
```

### GET /

Identifica a API e informa versão e caminho da documentação.

Resposta esperada:

```json
{
  "name": "DescompliADS API",
  "version": "0.1.0",
  "status": "running",
  "docs": "/docs"
}
```

### GET /health

Health check básico, sem depender de serviços externos.

Exemplo:

```json
{
  "status": "ok",
  "app": "DescompliADS API",
  "version": "0.1.0",
  "environment": "development",
  "timezone": "America/Sao_Paulo"
}
```

O mesmo health check também está disponível em:

```http
GET /api/v1/health
```

## Dependências

Produção:

```text
fastapi[standard]==0.139.2
pydantic-settings==2.14.2
```

Desenvolvimento/testes:

```text
httpx==0.28.1
pytest==9.1.1
```

## Configuração

Copie:

```bash
cp .env.example .env
```

Variáveis iniciais:

```env
APP_NAME=DescompliADS API
APP_VERSION=0.1.0
ENVIRONMENT=development
DEBUG=true
API_V1_PREFIX=/api/v1
TIMEZONE=America/Sao_Paulo
```

O arquivo `.env` real não deve ser versionado.

## Como testar localmente

Entre no backend:

```bash
cd backend
```

Crie um ambiente virtual:

```bash
python -m venv .venv
```

No Linux/macOS:

```bash
source .venv/bin/activate
```

No Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Instale as dependências de desenvolvimento:

```bash
pip install -r requirements-dev.txt
```

Copie as configurações:

```bash
cp .env.example .env
```

No PowerShell:

```powershell
Copy-Item .env.example .env
```

Execute os testes:

```bash
pytest -q
```

Resultado esperado:

```text
3 passed
```

Inicie a API em desenvolvimento:

```bash
fastapi dev app/main.py
```

Teste no navegador:

```text
http://127.0.0.1:8000/
http://127.0.0.1:8000/health
http://127.0.0.1:8000/api/v1/health
http://127.0.0.1:8000/docs
```

## Como testar com Docker

Dentro de `backend/`:

```bash
docker build -t descompliads-api .
```

Execute:

```bash
docker run --rm -p 8000:8000 --env-file .env descompliads-api
```

Depois acesse:

```text
http://127.0.0.1:8000/health
```

## Validação já realizada

Foi executado um teste local da estrutura usando o FastAPI disponível no ambiente de validação.

Resultado:

```text
3 passed
```

Os três endpoints responderam corretamente nos testes automatizados.

Observação: o ambiente local de validação possuía uma versão diferente da versão atualmente fixada em `requirements.txt`. A instalação e execução com as versões pinadas deve ser repetida no ambiente de desenvolvimento/deploy antes de promover a Fase 1 para produção.

## Checklist

- [x] criar FastAPI;
- [x] criar `GET /`;
- [x] criar `GET /health`;
- [x] criar `GET /api/v1/health`;
- [x] configurações via `.env`;
- [x] `.env.example` sem segredos;
- [x] Dockerfile;
- [x] estrutura de testes;
- [x] organização por rotas;
- [x] organização por serviços;
- [x] organização por modelos;
- [x] pacote reservado para persistência;
- [x] testes locais da aplicação: 3/3 aprovados;
- [ ] instalar e testar as versões pinadas no ambiente de deploy;
- [ ] construir a imagem Docker no ambiente de deploy;
- [ ] publicar o backend em um ambiente acessível;

## Critério para encerrar a Fase 1

A Fase 1 poderá ser considerada concluída quando, no ambiente real de desenvolvimento/deploy:

1. `pip install -r requirements-dev.txt` concluir sem erros;
2. `pytest -q` retornar todos os testes aprovados;
3. a aplicação iniciar normalmente;
4. `/health` responder HTTP 200;
5. a imagem Docker construir e iniciar corretamente.

Depois disso, iniciaremos a **Fase 2 — Supabase**.
