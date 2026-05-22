"""Application settings — paths, currency, source workbook location."""
from __future__ import annotations

import os
from pathlib import Path


class Settings:
    PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]
    APP_DIR: Path = PROJECT_ROOT / "app"

    DATA_DIR: Path = PROJECT_ROOT / "data"
    CATEGORIES_CSV: Path = DATA_DIR / "categories.csv"
    ENTRIES_CSV: Path = DATA_DIR / "entries.csv"
    BUDGETS_CSV: Path = DATA_DIR / "budgets.csv"

    TEMPLATES_DIR: Path = APP_DIR / "templates"
    STATIC_DIR: Path = APP_DIR / "static"

    SOURCE_XLSX: Path = Path(
        os.environ.get(
            "EXPENSO_SOURCE_XLSX",
            str(Path.home() / "Desktop" / "Expense_Tracker_FY2026-27.xlsx"),
        )
    )

    CURRENCY_SYMBOL: str = "Rs "
    DATE_FMT: str = "%Y-%m-%d"

    HOST: str = os.environ.get("EXPENSO_HOST", "127.0.0.1")
    PORT: int = int(os.environ.get("EXPENSO_PORT", "8000"))


settings = Settings()
