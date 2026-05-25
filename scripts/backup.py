#!/usr/bin/env python
"""Stand-alone backup runner.

Equivalent to the snapshot the app writes automatically on shutdown — use
this when you want a backup *now* without restarting the server, or from
a cron / scheduled task.

Reads EXPENSO_DATA_DIR / EXPENSO_BACKUP_DIR / EXPENSO_BACKUP_COUNT from
the project's .env (same as the running app).

Usage:
    venv/Scripts/python.exe scripts/backup.py
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

# Make the `app` package importable when running this script directly,
# regardless of where it's invoked from.
_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))

from app.services.backup_service import run_backup  # noqa: E402
from app.core.settings import settings  # noqa: E402


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s :: %(message)s",
    )
    log = logging.getLogger("expenso.backup.cli")

    log.info("data dir   = %s", settings.DATA_DIR)
    log.info("backup dir = %s (keep %s)",
             settings.BACKUP_DIR,
             "unlimited" if settings.BACKUP_COUNT <= 0 else settings.BACKUP_COUNT)

    target = run_backup()
    if target is None:
        log.info("nothing to back up.")
        return 0
    log.info("done → %s", target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
