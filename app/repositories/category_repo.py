"""CSV-backed CategoryRepository."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from ..core.settings import settings
from ..domain.models import Category
from .csv_base import CsvRepository

FIELDS = ["id", "name", "parent"]


def _row_to_model(row: dict) -> Category:
    return Category(
        id=row.get("id") or None,  # type: ignore[arg-type]
        name=row["name"],
        parent=(row.get("parent") or None),
    )


def _model_to_row(c: Category) -> dict:
    return {"id": c.id, "name": c.name, "parent": c.parent or ""}


class CategoryCsvRepository(CsvRepository[Category]):
    def __init__(self, path: Optional[Path] = None) -> None:
        super().__init__(
            path or settings.CATEGORIES_CSV,
            Category,
            FIELDS,
            _row_to_model,
            _model_to_row,
        )

    def find_by_name(self, name: str) -> Optional[Category]:
        name = name.strip().lower()
        for c in self.list():
            if c.name.strip().lower() == name:
                return c
        return None
