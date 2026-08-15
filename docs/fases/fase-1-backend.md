# Fase 1 — Backend base

Status: **implementação inicial concluída na branch `meta-ads-pro`; validação no ambiente de deploy ainda pendente**.

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
│   ├── main.py
│   ├── api/
│   │   └── health.py
│   ├── config/
│   │   └── settings.py
│   ├── database/
│   ├── models/
│   └── services/
├── tests/
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

Resposta esperada do health check:

```json
{
  "status": "ok",
  "app": "DescompliADS API",
  "version": "0.1.0",
  "environment": "development",
  "timezone": "America/Sao_Paulo"
}
```

## Configuração inicial

```env
APP_NAME=DescompliADS API
APP_VERSION=0.1.0
ENVIRONMENT=development
DEBUG=true
API_V1_PREFIX=/api/v1
TIMEZONE=America/Sao_Paulo
```

O `.env` real não deve ser versionado.

## Como testar localmente

```bash
cd backend
python -m venv .venv
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Instale as dependências:

```bash
pip install -r requirements-dev.txt
```

Copie o arquivo de ambiente:

```bash
cp .env.example .env
```

PowerShell:

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

Inicie a API:

```bash
fastapi dev app/main.py
```

Teste:

```text
http://127.0.0.1:8000/
http://127.0.0.1:8000/health
http://127.0.0.1:8000/api/v1/health
http://127.0.0.1:8000/docs
```

## Docker

```bash
docker build -t descompliads-api .
docker run --rm -p 8000:8000 --env-file .env descompliads-api
```

## Validação já realizada

Os testes locais da estrutura retornaram:

```text
3 passed
```

A validação final ainda deve ser repetida no ambiente real de desenvolvimento/deploy com as versões fixadas no projeto.

## Checklist

- [x] FastAPI;
- [x] `GET /`;
- [x] `GET /health`;
- [x] `GET /api/v1/health`;
- [x] configurações via `.env`;
- [x] `.env.example` sem segredos;
- [x] Dockerfile;
- [x] estrutura de testes;
- [x] organização por rotas, serviços e modelos;
- [x] pacote reservado para persistência;
- [x] testes locais 3/3 aprovados;
- [ ] testar as versões pinadas no ambiente de deploy;
- [ ] construir a imagem Docker no ambiente de deploy;
- [ ] publicar o backend em ambiente acessível.

## Critério de encerramento

A Fase 1 estará encerrada quando, no ambiente real de desenvolvimento/deploy:

1. as dependências instalarem sem erro;
2. `pytest -q` aprovar todos os testes;
3. a aplicação iniciar normalmente;
4. `/health` responder HTTP 200;
5. a imagem Docker construir e iniciar corretamente.

Depois disso, a **Fase 2 — Supabase** será desenvolvida diretamente na branch `meta-ads-pro`.
