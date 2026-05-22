"""CSV-backed BudgetRepository."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from ..core.settings import settings
from ..domain.models import Budget
from .csv_base import CsvRepository

FIELDS = ["id", "category", "monthly_cap"]


def _row_to_model(row: dict) -> Budget:
    return Budget(
        id=row.get("id") or None,  # type: ignore[arg-type]
        category=row["category"],
        monthly_cap=float(row["monthly_cap"]),
    )


def _model_to_row(b: Budget) -> dict:
    return {
        "id": b.id,
        "category": b.category,
        "monthly_cap": f"{b.monthly_cap:.2f}",
    }


class BudgetCsvRepository(CsvRepository[Budget]):
    def __init__(self, path: Optional[Path] = None) -> None:
        super().__init__(
            path or settings.BUDGETS_CSV,
            Budget,
            FIELDS,
            _row_to_model,
            _model_to_row,
        )

    def find_by_category(self, category: str) -> Optional[Budget]:
        category = category.strip().lower()
        for b in self.list():
            if b.category.strip().lower() == category:
                return b
        return None
