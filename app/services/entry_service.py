"""Entry business logic: CRUD + filters."""
from __future__ import annotations

from datetime import date
from typing import List, Optional

from ..core.exceptions import NotFoundError, ValidationError
from ..domain.interfaces import CategoryRepository, EntryRepository
from ..domain.models import Entry


class EntryService:
    def __init__(self, repo: EntryRepository, categories: CategoryRepository) -> None:
        self._repo = repo
        self._categories = categories

    def _assert_category(self, name: str) -> None:
        if self._categories.find_by_name(name) is None:
            raise ValidationError(f"category '{name}' does not exist")

    def list_all(
        self,
        *,
        category: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        q: Optional[str] = None,
    ) -> List[Entry]:
        rows = self._repo.list()
        if category:
            rows = [r for r in rows if r.category == category]
        if date_from:
            rows = [r for r in rows if r.date >= date_from]
        if date_to:
            rows = [r for r in rows if r.date <= date_to]
        if q:
            q_low = q.strip().lower()
            rows = [
                r
                for r in rows
                if q_low in r.narration.lower() or q_low in r.category.lower()
            ]
        rows.sort(key=lambda r: (r.date, r.id), reverse=True)
        return rows

    def get(self, entry_id: str) -> Entry:
        e = self._repo.get(entry_id)
        if e is None:
            raise NotFoundError(f"entry {entry_id} not found")
        return e

    def create(
        self,
        *,
        date_: date,
        category: str,
        narration: str,
        debit: float,
        credit: float,
    ) -> Entry:
        self._assert_category(category)
        entry = Entry(
            date=date_,
            category=category,
            narration=narration or "",
            debit=debit or 0.0,
            credit=credit or 0.0,
        )
        return self._repo.add(entry)

    def update(
        self,
        entry_id: str,
        *,
        date_: date,
        category: str,
        narration: str,
        debit: float,
        credit: float,
    ) -> Entry:
        _ = self.get(entry_id)
        self._assert_category(category)
        updated = Entry(
            id=entry_id,
            date=date_,
            category=category,
            narration=narration or "",
            debit=debit or 0.0,
            credit=credit or 0.0,
        )
        return self._repo.update(updated)

    def delete(self, entry_id: str) -> None:
        _ = self.get(entry_id)
        self._repo.delete(entry_id)

    def recent(self, n: int = 10) -> List[Entry]:
        return self.list_all()[:n]
