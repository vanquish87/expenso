"""Budget service: per-category caps with group-rollup against current month spend."""
from __future__ import annotations

from datetime import date
from typing import List, Optional

from ..core.exceptions import ConflictError, NotFoundError, ValidationError
from ..domain.interfaces import BudgetRepository, CategoryRepository, EntryRepository
from ..domain.models import Budget


class BudgetService:
    def __init__(
        self,
        repo: BudgetRepository,
        categories: CategoryRepository,
        entries: EntryRepository,
    ) -> None:
        self._repo = repo
        self._categories = categories
        self._entries = entries

    def list_all(self) -> List[Budget]:
        return sorted(self._repo.list(), key=lambda b: b.category.lower())

    def get(self, budget_id: str) -> Budget:
        b = self._repo.get(budget_id)
        if b is None:
            raise NotFoundError(f"budget {budget_id} not found")
        return b

    def create(self, category: str, monthly_cap: float) -> Budget:
        category = (category or "").strip()
        if not category:
            raise ValidationError("category is required")
        if monthly_cap <= 0:
            raise ValidationError("monthly_cap must be > 0")
        if self._categories.find_by_name(category) is None:
            raise ValidationError(f"category '{category}' does not exist")
        if self._repo.find_by_category(category):
            raise ConflictError(f"budget for '{category}' already exists")
        return self._repo.add(Budget(category=category, monthly_cap=float(monthly_cap)))

    def update(self, budget_id: str, monthly_cap: float) -> Budget:
        existing = self.get(budget_id)
        if monthly_cap <= 0:
            raise ValidationError("monthly_cap must be > 0")
        updated = Budget(id=existing.id, category=existing.category, monthly_cap=float(monthly_cap))
        return self._repo.update(updated)

    def delete(self, budget_id: str) -> None:
        _ = self.get(budget_id)
        self._repo.delete(budget_id)

    def _children_of(self, group_name: str) -> List[str]:
        return [
            c.name
            for c in self._categories.list()
            if (c.parent or "") == group_name
        ]

    def status(self, month: Optional[date] = None) -> List[dict]:
        """For each budget, current-month spend (with group rollup), cap, remaining, pct."""
        if month is None:
            month = date.today()
        y, m = month.year, month.month

        rows: List[dict] = []
        for b in self.list_all():
            cat = self._categories.find_by_name(b.category)
            names = [b.category]
            if cat and cat.is_group:
                names.extend(self._children_of(b.category))
            spend = sum(
                e.debit
                for e in self._entries.list()
                if e.category in names
                and e.date.year == y
                and e.date.month == m
            )
            remaining = b.monthly_cap - spend
            pct = (spend / b.monthly_cap * 100.0) if b.monthly_cap else 0.0
            rows.append(
                {
                    "budget": b,
                    "is_group": bool(cat and cat.is_group),
                    "spend": round(spend, 2),
                    "remaining": round(remaining, 2),
                    "pct": round(pct, 1),
                    "over": spend > b.monthly_cap,
                }
            )
        rows.sort(key=lambda r: r["pct"], reverse=True)
        return rows
