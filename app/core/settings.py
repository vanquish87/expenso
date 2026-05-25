"""Application settings — paths, currency, source workbook location.

Reads a ``.env`` file at project root on import (via python-dotenv) so the
user can pin their data directory, port, etc. without exporting shell vars.

Honored variables:

  EXPENSO_DATA_DIR     where categories.csv / entries.csv / budgets.csv live.
                       Can be relative (resolved against project root) or
                       absolute (e.g. ``D:/Backups/Expenso``). Default: ``./data``.
  EXPENSO_BACKUP_DIR   where rolling shutdown snapshots are written. Same
                       path rules as DATA_DIR. Default: ``./backups``.
  EXPENSO_BACKUP_COUNT how many most-recent backup folders to retain.
                       Older ones are pruned when a new one is written.
                       0 = unlimited. Default: 5.
  EXPENSO_SOURCE_XLSX  the workbook used by the first-run seed and the
                       Re-import button. Default: Desktop/Expense_Tracker_FY2026-27.xlsx.
  EXPENSO_HOST         uvicorn bind host. Default: 127.0.0.1.
  EXPENSO_PORT         uvicorn bind port. Default: 8000.
"""
from __future__ import annotations

import os
from pathlib import Path

# Resolve project root early so we can find .env regardless of cwd.
_PROJECT_ROOT = Path(__file__).resolve().parents[2]

try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=_PROJECT_ROOT / ".env")
except ImportError:  # pragma: no cover — python-dotenv is in requirements.txt
    pass


def _resolve_path(env_key: str, default_subdir: str) -> Path:
    """Honor an env var as a path; fall back to ``<project root>/<default_subdir>``.

    Relative paths are resolved against the project root so cwd doesn't
    matter; ``~`` is expanded; the result is always absolute.
    """
    raw = (os.environ.get(env_key) or "").strip().strip('"').strip("'")
    if not raw:
        return _PROJECT_ROOT / default_subdir
    p = Path(raw).expanduser()
    if not p.is_absolute():
        p = _PROJECT_ROOT / p
    return p.resolve()


def _resolve_data_dir() -> Path:
    return _resolve_path("EXPENSO_DATA_DIR", "data")


def _resolve_backup_dir() -> Path:
    return _resolve_path("EXPENSO_BACKUP_DIR", "backups")


def _resolve_backup_count() -> int:
    raw = (os.environ.get("EXPENSO_BACKUP_COUNT") or "").strip()
    if not raw:
        return 5
    try:
        n = int(raw)
        return max(0, n)
    except ValueError:
        return 5


class Settings:
    PROJECT_ROOT: Path = _PROJECT_ROOT
    APP_DIR: Path = _PROJECT_ROOT / "app"

    DATA_DIR: Path = _resolve_data_dir()
    CATEGORIES_CSV: Path = DATA_DIR / "categories.csv"
    ENTRIES_CSV: Path = DATA_DIR / "entries.csv"
    BUDGETS_CSV: Path = DATA_DIR / "budgets.csv"

    BACKUP_DIR: Path = _resolve_backup_dir()
    BACKUP_COUNT: int = _resolve_backup_count()

    TEMPLATES_DIR: Path = APP_DIR / "templates"
    STATIC_DIR: Path = APP_DIR / "static"

    SOURCE_XLSX: Path = Path(
        os.environ.get(
            "EXPENSO_SOURCE_XLSX",
            str(Path.home() / "Desktop" / "Expense_Tracker_FY2026-27.xlsx"),
        )
    ).expanduser()

    CURRENCY_SYMBOL: str = "Rs "
    DATE_FMT: str = "%Y-%m-%d"

    HOST: str = os.environ.get("EXPENSO_HOST", "127.0.0.1")
    PORT: int = int(os.environ.get("EXPENSO_PORT", "8000"))


settings = Settings()
