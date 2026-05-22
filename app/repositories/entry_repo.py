"""CSV-backed EntryRepository.

Schema: id, date, timestamp, category, narration, debit, credit.

The ``timestamp`` column was added after the initial ship; on construction
this repo runs a one-shot migration that backfills timestamps for any CSV
that pre-dates the column (or has any row missing one). The migration
walks rows in file order and assigns ``date_midnight + N minutes`` per
date, so xlsx insertion order is preserved. It is atomic (tempfile +
os.replace) and never deletes the data CSV — see ``csv_base.py`` for the
durability invariant.
"""
from __future__ import annotations

import csv
import os
import tempfile
from datetime import date as _date, datetime, time, timedelta
from pathlib import Path
from typing import Optional

from ..core.settings import settings
from ..domain.models import Entry
from .csv_base import CsvRepository

FIELDS = ["id", "date", "timestamp", "category", "narration", "debit", "credit"]


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


def _parse_timestamp(s: Optional[str], fallback_date: _date) -> datetime:
    s = (s or "").strip()
    if not s:
        # If a row somehow slips through without one (e.g. a hand-edited
        # CSV), park it at noon of its date. The startup migration would
        # normally have replaced this with a sequential value.
        return datetime.combine(fallback_date, time(12, 0))
    return datetime.fromisoformat(s)


def _row_to_model(row: dict) -> Entry:
    d = _parse_date(row["date"])
    return Entry(
        id=row.get("id") or None,  # type: ignore[arg-type]
        date=d,
        timestamp=_parse_timestamp(row.get("timestamp"), d),
        category=row["category"],
        narration=row.get("narration") or "",
        debit=_parse_float(row.get("debit", "")),
        credit=_parse_float(row.get("credit", "")),
    )


def _model_to_row(e: Entry) -> dict:
    return {
        "id": e.id,
        "date": e.date.isoformat(),
        "timestamp": e.timestamp.isoformat(timespec="seconds"),
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
        self._migrate_legacy_csv()

    def _migrate_legacy_csv(self) -> None:
        """If the CSV header lacks ``timestamp`` (or any row has an empty one),
        rewrite the file once with sequential per-date timestamps in file order.

        Why this exists: an older build of Expenso wrote entries without a
        timestamp column. Once the column was introduced, every same-date row
        would otherwise read back with the same fallback noon timestamp and
        the ledger would lose xlsx insertion order. This pass restores order
        by walking the file top-to-bottom and stamping date+0min, date+1min,
        date+2min, … per date.
        """
        with self._lock:
            if not self._path.exists() or self._path.stat().st_size == 0:
                return
            with self._path.open(encoding="utf-8", newline="") as fh:
                reader = csv.DictReader(fh)
                fieldnames = reader.fieldnames or []
                rows = list(reader)
            if not rows:
                return
            needs = ("timestamp" not in fieldnames) or any(
                not (r.get("timestamp") or "").strip() for r in rows
            )
            if not needs:
                return

            per_date_count: dict[str, int] = {}
            for r in rows:
                d_str = (r.get("date") or "").strip()
                if not d_str:
                    continue
                n = per_date_count.get(d_str, 0)
                per_date_count[d_str] = n + 1
                ts = datetime.fromisoformat(d_str + "T00:00:00") + timedelta(minutes=n)
                r["timestamp"] = ts.isoformat(timespec="seconds")

            # Atomic rewrite, same pattern as csv_base (never deletes the data file).
            tmp_fd, tmp_path = tempfile.mkstemp(
                prefix=self._path.name + ".",
                suffix=".migrate.tmp",
                dir=str(self._path.parent),
            )
            try:
                with os.fdopen(tmp_fd, "w", encoding="utf-8", newline="") as fh:
                    writer = csv.DictWriter(fh, fieldnames=FIELDS, extrasaction="ignore")
                    writer.writeheader()
                    writer.writerows(rows)
                os.replace(tmp_path, self._path)
            except Exception:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
                raise
