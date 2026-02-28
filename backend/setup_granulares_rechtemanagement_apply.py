"""
setup_granulares_rechtemanagement_apply.py
==========================================
Idempotentes Setup-Script für das granulare Rechtemanagement in Produktion.

Führt folgende Schritte aus:
  1. Alembic-Migration 0008_add_role_permissions auf `head` bringen
  2. Standard-Berechtigungen (DEFAULT_PERMISSIONS) in die Datenbank seeden

Idempotenz:
  - Alembic überspringt bereits angewendete Migrationen automatisch.
  - seed_default_permissions() überspringt bereits vorhandene Einträge
    (is_explicit=True) – es werden nur fehlende Einträge angelegt.

Ausführen (im Backend-Container oder mit Zugang zur DB):
  python3 setup_granulares_rechtemanagement_apply.py

  # Mit --overwrite: bestehende Einträge mit DEFAULT_PERMISSIONS überschreiben
  python3 setup_granulares_rechtemanagement_apply.py --overwrite

Voraussetzungen:
  - Umgebungsvariable DATABASE_URL gesetzt (oder .env-Datei vorhanden)
  - Alembic ist installiert und alembic.ini liegt im Backend-Verzeichnis
"""

from __future__ import annotations

import argparse
import asyncio
import os
import subprocess
import sys


def _locate_backend_dir() -> str:
    """
    Find the directory that contains alembic.ini.
    - When run from project root: <project>/backend/
    - When run inside the Docker container: /app/ (i.e. same dir as script)
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Check if alembic.ini is in the same directory (container case)
    if os.path.isfile(os.path.join(script_dir, "alembic.ini")):
        return script_dir
    # Otherwise look in the adjacent backend/ subdirectory
    backend_dir = os.path.join(script_dir, "backend")
    if os.path.isfile(os.path.join(backend_dir, "alembic.ini")):
        return backend_dir
    raise RuntimeError(
        f"Could not find alembic.ini in {script_dir!r} or {backend_dir!r}. "
        "Please run this script from the project root or the backend directory."
    )


def _run_migration() -> None:
    """Run alembic upgrade head idempotently."""
    backend_dir = _locate_backend_dir()

    print("── Schritt 1: Alembic-Migration ────────────────────────────────")
    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        cwd=backend_dir,
        capture_output=True,
        text=True,
    )
    if result.stdout:
        print(result.stdout.rstrip())
    if result.stderr:
        print(result.stderr.rstrip(), file=sys.stderr)
    if result.returncode != 0:
        print(f"FEHLER: alembic upgrade head schlug fehl (exit code {result.returncode})", file=sys.stderr)
        sys.exit(1)
    print("Migration erfolgreich abgeschlossen (oder bereits aktuell).")
    print()


async def _seed_permissions(overwrite: bool) -> None:
    """Seed default permissions into the database."""
    # Import here so path is already set up correctly
    from app.database import AsyncSessionLocal
    from app.services.permissions_service import seed_default_permissions

    print("── Schritt 2: Standard-Berechtigungen seeden ───────────────────")
    async with AsyncSessionLocal() as session:
        inserted = await seed_default_permissions(session, overwrite=overwrite)

    if overwrite:
        print(f"{inserted} Einträge angelegt / aktualisiert (--overwrite aktiv).")
    else:
        print(f"{inserted} neue Einträge angelegt (bestehende übersprungen).")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Granulares Rechtemanagement – Produktions-Setup"
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Bestehende Berechtigungs-Einträge mit DEFAULT_PERMISSIONS überschreiben.",
    )
    parser.add_argument(
        "--skip-migration",
        action="store_true",
        default=False,
        help="Alembic-Migration überspringen (nur Seeding ausführen).",
    )
    args = parser.parse_args()

    # Ensure backend/app is importable
    backend_dir = _locate_backend_dir()
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)

    print("=" * 60)
    print("Granulares Rechtemanagement – Produktions-Setup")
    print("=" * 60)
    print()

    if not args.skip_migration:
        _run_migration()
    else:
        print("Migration übersprungen (--skip-migration).")
        print()

    asyncio.run(_seed_permissions(overwrite=args.overwrite))

    print("=" * 60)
    print("Setup abgeschlossen.")
    print("=" * 60)


if __name__ == "__main__":
    main()
