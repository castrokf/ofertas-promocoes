from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from sqlalchemy.engine import make_url


PROJECT_ROOT = Path(__file__).resolve().parents[1]
os.environ["PYTHONPATH"] = (
    str(PROJECT_ROOT)
    if not os.getenv("PYTHONPATH")
    else f"{PROJECT_ROOT}{os.pathsep}{os.environ['PYTHONPATH']}"
)


def masked_database_url(value: str) -> str:
    try:
        url = make_url(value)
        return str(url.set(password="***" if url.password else None))
    except Exception:
        return "<invalid DATABASE_URL>"


def preflight() -> None:
    os.chdir(PROJECT_ROOT)
    database_url = os.getenv("DATABASE_URL", "")
    if not database_url:
        raise SystemExit("Missing DATABASE_URL. Set it to Render PostgreSQL Internal Database URL.")
    if any(marker in database_url.lower() for marker in ["cole_", "internal_database_url", "postgres:5432"]):
        raise SystemExit(
            "DATABASE_URL still looks like a placeholder or Docker local URL. "
            "Use the Render PostgreSQL Internal Database URL."
        )
    try:
        make_url(database_url)
    except Exception as exc:
        raise SystemExit(f"Invalid DATABASE_URL: {exc}") from exc

    if not os.getenv("SECRET_KEY") or os.getenv("SECRET_KEY") == "change-me-in-production":
        print("==> Warning: SECRET_KEY is not production-grade. Set a long random value.", flush=True)

    print(f"==> AutoTechDealsX startup: project root {PROJECT_ROOT}", flush=True)
    print(f"==> AutoTechDealsX startup: database {masked_database_url(database_url)}", flush=True)


def run_step(name: str, command: list[str]) -> None:
    print(f"==> AutoTechDealsX startup: {name}", flush=True)
    completed = subprocess.run(command, check=False)
    if completed.returncode != 0:
        print(f"==> Startup step failed: {name} exited with {completed.returncode}", flush=True)
        raise SystemExit(completed.returncode)


def main() -> None:
    preflight()
    port = os.getenv("PORT", "8000")
    run_step("database migrations", [sys.executable, "-m", "alembic", "upgrade", "head"])
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
