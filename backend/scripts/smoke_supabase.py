import argparse
import json
import sys
from pathlib import Path

# Permite executar `python scripts/smoke_supabase.py` a partir de backend/.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database.supabase import SupabaseNotConfiguredError, get_supabase_client
from app.services.supabase_service import SupabaseService


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Valida a conexão do backend DescompliADS com o Supabase."
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Além da leitura, insere e remove um registro temporário em app_health.",
    )
    args = parser.parse_args()

    try:
        service = SupabaseService(get_supabase_client())
        result = {"read": service.read_health()}

        if args.write:
            result["write"] = service.write_probe()

        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except SupabaseNotConfiguredError as exc:
        print(f"ERRO: {exc}")
        return 2
    except Exception as exc:
        print(f"ERRO SUPABASE: {type(exc).__name__}: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
