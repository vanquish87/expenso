"""Analytics service: aggregations powering the Chart.js dashboard."""
from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from typing import Dict, List, Optional

from ..domain.interfaces import CategoryRepository, EntryRepository
from ..domain.models import Entry


class AnalyticsService:
    def __init__(self, entries: EntryRepository, categories: CategoryRepository) -> None:
        self._entries = entries
        self._categories = categories

    def _scoped(
        self,
        date_from: Optional[date],
        date_to: Optional[date],
    ) -> List[Entry]:
        rows = self._entries.list()
        if date_from:
            rows = [r for r in rows if r.date >= date_from]
        if date_to:
            rows = [r for r in rows if r.date <= date_to]
        return rows

    def kpis(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> Dict:
        rows = self._scoped(date_from, date_to)
        total_debit = sum(r.debit for r in rows)
        total_credit = sum(r.credit for r in rows)
        days = {r.date for r in rows}
        avg_daily = (total_debit / len(days)) if days else 0.0
        biggest = max(rows, key=lambda r: r.debit, default=None)
        return {
            "total_debit": round(total_debit, 2),
            "total_credit": round(total_credit, 2),
            "net": round(total_credit - total_debit, 2),
            "n_entries": len(rows),
            "n_days": len(days),
            "avg_daily_debit": round(avg_daily, 2),
            "biggest_debit": (
                {
                    "amount": round(biggest.debit, 2),
                    "category": biggest.category,
                    "narration": biggest.narration,
                    "date": biggest.date.isoformat(),
                }
                if biggest
                else None
            ),
        }

    def _parent_of(self, name: str) -> str:
        c = self._categories.find_by_name(name)
        if c is None:
            return "(uncategorised)"
        if c.is_group:
            return c.name
        return c.parent or "(uncategorised)"

    def spend_by_group(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> List[Dict]:
        from ..templating import _cat_emoji
        rows = self._scoped(date_from, date_to)
        agg: Dict[str, float] = defaultdict(float)
        for r in rows:
            agg[self._parent_of(r.category)] += r.debit
        items = [
            {"label": k, "value": round(v, 2), "icon": _cat_emoji(k)}
            for k, v in agg.items() if v > 0
        ]
        items.sort(key=lambda x: x["value"], reverse=True)
        return items

    def subs_in_group(
        self,
        group: str,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> List[Dict]:
        """Spend per sub-category inside ``group`` for the date range.

        Also includes entries whose category name == the group itself
        (a record tagged directly to the group rather than a sub).
        """
        from ..templating import _cat_emoji
        rows = self._scoped(date_from, date_to)
        agg: Dict[str, float] = defaultdict(float)
        for r in rows:
            parent = self._parent_of(r.category)
            if parent == group or r.category == group:
                agg[r.category] += r.debit
        items = [
            {"label": k, "value": round(v, 2), "icon": _cat_emoji(k)}
            for k, v in agg.items() if v > 0
        ]
        items.sort(key=lambda x: x["value"], reverse=True)
        return items

    def monthly_for_category(
        self,
        category: str,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> List[Dict]:
        """Per-month debit totals for one sub-category within the range.

        Returns sorted ascending by ``YYYY-MM``; empty months are omitted
        (the chart on screen 3 of the reference shows zero-height bars
        for months without spend, which we render client-side from this
        gap-free list).
        """
        rows = self._scoped(date_from, date_to)
        agg: Dict[str, float] = defaultdict(float)
        for r in rows:
            if r.category != category:
                continue
            key = f"{r.date.year:04d}-{r.date.month:02d}"
            agg[key] += r.debit
        return [
            {"label": k, "value": round(v, 2)}
            for k, v in sorted(agg.items())
            if v > 0
        ]

    def transactions_in_category_month(
        self,
        category: str,
        year_month: str,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> List[Dict]:
        """Individual entries for ``category`` within ``year_month``
        (``YYYY-MM``), optionally further scoped by the outer date range.

        Sorted newest-first by (date, timestamp), matching the ledger.
        """
        rows = self._scoped(date_from, date_to)
        rows = [
            r for r in rows
            if r.category == category
            and f"{r.date.year:04d}-{r.date.month:02d}" == year_month
        ]
        rows.sort(key=lambda r: (r.date, r.timestamp), reverse=True)
        return [
            {
                "id": r.id,
                "date": r.date.isoformat(),
                "weekday": r.date.strftime("%A"),
                "day": r.date.strftime("%d"),
                "month_label": r.date.strftime("%B %Y"),
                "category": r.category,
                "narration": r.narration,
                "debit": round(r.debit, 2),
                "credit": round(r.credit, 2),
            }
            for r in rows
        ]

    def top_subcategories(
        self,
        n: int = 10,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> List[Dict]:
        rows = self._scoped(date_from, date_to)
        agg: Dict[str, float] = defaultdict(float)
        for r in rows:
            agg[r.category] += r.debit
        items = [{"label": k, "value": round(v, 2)} for k, v in agg.items() if v > 0]
        items.sort(key=lambda x: x["value"], reverse=True)
        return items[:n]

    def daily_series(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> List[Dict]:
        rows = self._scoped(date_from, date_to)
        if not rows:
            return []
        agg: Dict[date, float] = defaultdict(float)
        for r in rows:
            agg[r.date] += r.debit
        start = min(agg)
        end = max(agg)
        out: List[Dict] = []
        d = start
        while d <= end:
            out.append({"label": d.isoformat(), "value": round(agg.get(d, 0.0), 2)})
            d += timedelta(days=1)
        return out

    def cumulative_series(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> List[Dict]:
        daily = self.daily_series(date_from, date_to)
        running = 0.0
        out: List[Dict] = []
        for d in daily:
            running += d["value"]
            out.append({"label": d["label"], "value": round(running, 2)})
        return out

    def weekday_pattern(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> List[Dict]:
        rows = self._scoped(date_from, date_to)
        names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        agg = [0.0] * 7
        for r in rows:
            agg[r.date.weekday()] += r.debit
        return [{"label": names[i], "value": round(agg[i], 2)} for i in range(7)]

    def monthly_debit_credit(self) -> List[Dict]:
        rows = self._entries.list()
        agg: Dict[str, Dict[str, float]] = defaultdict(lambda: {"debit": 0.0, "credit": 0.0})
        for r in rows:
            key = f"{r.date.year:04d}-{r.date.month:02d}"
            agg[key]["debit"] += r.debit
            agg[key]["credit"] += r.credit
        return [
            {
                "label": k,
                "debit": round(v["debit"], 2),
                "credit": round(v["credit"], 2),
            }
            for k, v in sorted(agg.items())
        ]

    def top_transactions(
        self,
        n: int = 10,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> List[Dict]:
        rows = self._scoped(date_from, date_to)
        rows = sorted(rows, key=lambda r: r.debit, reverse=True)[:n]
        return [
            {
                "date": r.date.isoformat(),
                "category": r.category,
                "narration": r.narration,
                "amount": round(r.debit, 2),
            }
            for r in rows
        ]
