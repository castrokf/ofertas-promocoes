from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
os.environ["PYTHONPATH"] = (
    str(PROJECT_ROOT)
    if not os.getenv("PYTHONPATH")
    else f"{PROJECT_ROOT}{os.pathsep}{os.environ['PYTHONPATH']}"
)


def run_step(name: str, command: list[str]) -> None:
    print(f"==> AutoTechDealsX startup: {name}", flush=True)
    completed = subprocess.run(command, check=False)
    if completed.returncode != 0:
        print(f"==> Startup step failed: {name} exited with {completed.returncode}", flush=True)
        raise SystemExit(completed.returncode)


def main() -> None:
    port = os.getenv("PORT", "8000")
    run_step("database migrations", ["alembic", "upgrade", "head"])
    run_step("database seed", [sys.executable, "scripts/seed.py"])
    print("==> AutoTechDealsX startup: web server", flush=True)
    os.execvp(
        "gunicorn",
        [
            "gunicorn",
            "app.main:app",
            "-k",
            "uvicorn.workers.UvicornWorker",
            "--bind",
            f"0.0.0.0:{port}",
        ],
    )


if __name__ == "__main__":
    main()
