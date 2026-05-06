"""Smoke check for Render-style startup (lifespan runs bcrypt demo seed).

Run from apps/api:
  python check_render_startup.py

Imports ``app.main:app`` and opens ``TestClient`` so FastAPI lifespan executes once,
matching uvicorn startup when DATABASE_URL is available (SQLite/PG).
"""

from __future__ import annotations


def main() -> None:
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app):
        pass
    print("OK")


if __name__ == "__main__":
    main()
