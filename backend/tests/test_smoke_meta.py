import subprocess
import sys
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]


def test_smoke_meta_help_runs_from_backend_root() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/smoke_meta.py", "--help"],
        capture_output=True,
        text=True,
        check=False,
        cwd=BACKEND_ROOT,
    )

    assert result.returncode == 0
    assert "--list-accounts" in result.stdout
