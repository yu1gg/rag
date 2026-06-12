"""Script trigger routes -- Web entry trigger offline scripts."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from fastapi import APIRouter

from backend.app.core.response import error_response, success_response

router = APIRouter(prefix="/scripts", tags=["scripts"])

SCRIPT_DIR = Path(__file__).resolve().parents[4] / "scripts"
ALLOWED_SCRIPTS = {
    "collect_data",
    "clean_data",
    "chunk_data",
    "build_index",
    "run_evaluation",
}


@router.post("/{name}")
def trigger_script(name: str) -> dict:
    if name not in ALLOWED_SCRIPTS:
        return error_response(
            f"Unknown script: {name}, available: {', '.join(sorted(ALLOWED_SCRIPTS))}",
            code=404,
        )

    script_path = SCRIPT_DIR / f"{name}.py"
    if not script_path.exists():
        return error_response(f"Script file does not exist: {script_path}", code=404)

    try:
        result = subprocess.run(
            [sys.executable, "-m", f"backend.scripts.{name}"],
            capture_output=True,
            text=True,
            timeout=300,
            cwd=SCRIPT_DIR.parents[1],
        )
        return success_response({
            "script": name,
            "returncode": result.returncode,
            "stdout": (
                result.stdout[-2000:]
                if len(result.stdout) > 2000
                else result.stdout
            ),
            "stderr": (
                result.stderr[-1000:]
                if len(result.stderr) > 1000
                else result.stderr
            ),
        })
    except subprocess.TimeoutExpired:
        return error_response(f"Script {name} execution timed out (300s)", code=504)
    except Exception as exc:
        return error_response(f"Script {name} execution failed: {exc}", code=500)
