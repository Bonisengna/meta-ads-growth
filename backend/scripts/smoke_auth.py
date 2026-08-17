import argparse
import getpass
import json
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

# Permite executar `python scripts/smoke_auth.py` a partir de backend/.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from supabase import create_client

from app.config.settings import get_settings


def request_json(url: str, token: str | None = None) -> tuple[int, object]:
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(url, headers=headers, method="GET")
    try:
        with urlopen(request, timeout=15) as response:
            body = response.read().decode("utf-8")
            return response.status, json.loads(body)
    except HTTPError as exc:
        body = exc.read().decode("utf-8")
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            payload = {"detail": body}
        return exc.code, payload


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Valida autenticação Supabase e isolamento por cliente sem exibir o token."
    )
    parser.add_argument("--email", help="E-mail do usuário criado no Supabase Auth.")
    parser.add_argument(
        "--api-url",
        default="http://127.0.0.1:8000",
        help="URL local da FastAPI.",
    )
    args = parser.parse_args()

    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_publishable_key:
        print("ERRO: SUPABASE_URL e SUPABASE_PUBLISHABLE_KEY são obrigatórios no .env.")
        return 2

    email = args.email or input("E-mail: ").strip()
    password = getpass.getpass("Senha (não será exibida): ")
    endpoint = f"{args.api_url.rstrip('/')}/api/v1/clients?page=1&page_size=20"

    try:
        anonymous_status, _ = request_json(endpoint)
        auth_response = create_client(
            settings.supabase_url, settings.supabase_publishable_key
        ).auth.sign_in_with_password({"email": email, "password": password})
        token = auth_response.session.access_token if auth_response.session else None
        if not token:
            print("ERRO: o Supabase não retornou uma sessão autenticada.")
            return 1

        authenticated_status, payload = request_json(endpoint, token)
        items = payload.get("items", []) if isinstance(payload, dict) else []
        result = {
            "anonymous_request": anonymous_status,
            "authenticated_request": authenticated_status,
            "clients_visible": len(items),
            "client_names": [item.get("name") for item in items],
            "token_exposed": False,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if anonymous_status == 401 and authenticated_status == 200 else 1
    except (URLError, OSError) as exc:
        print(f"ERRO API: {type(exc).__name__}: {exc}")
        return 1
    except Exception as exc:
        print(f"ERRO AUTENTICAÇÃO: {type(exc).__name__}: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
