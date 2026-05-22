"""CSV-backed EntryRepository."""
from __future__ import annotations

from datetime import date as _date, datetime
from pathlib import Path
from typing import Optional

from ..core.settings import settings
from ..domain.models import Entry
from .csv_base import CsvRepository

FIELDS = ["id", "date", "category", "narration", "debit", "credit"]


def _parse_date(s: str) -> _date:
    s = (s or "").strip()
    if not s:
        raise ValueError("entry date is empty")
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        return datetime.fromisoformat(s).date()


def _parse_float(s: str) -> float:
    s = (s or "").strip()
    return float(s) if s else 0.0


def _row_to_model(row: dict) -> Entry:
    return Entry(
        id=row.get("id") or None,  # type: ignore[arg-type]
        date=_parse_date(row["date"]),
        category=row["category"],
        narration=row.get("narration") or "",
        debit=_parse_float(row.get("debit", "")),
        credit=_parse_float(row.get("credit", "")),
    )


def _model_to_row(e: Entry) -> dict:
    return {
        "id": e.id,
        "date": e.date.isoformat(),
        "category": e.category,
        "narration": e.narration,
        "debit": f"{e.debit:.2f}",
        "credit": f"{e.credit:.2f}",
    }


class EntryCsvRepository(CsvRepository[Entry]):
    def __init__(self, path: Optional[Path] = None) -> None:
        super().__init__(
            path or settings.ENTRIES_CSV,
            Entry,
            FIELDS,
            _row_to_model,
            _model_to_row,
        )
