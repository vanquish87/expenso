"""Rule-based insights — surface things worth noticing without any ML."""
from __future__ import annotations

import math
import statistics
from collections import defaultdict
from datetime import date
from typing import Dict, List, Optional

from ..domain.interfaces import CategoryRepository, EntryRepository


def _month_start(d: date) -> date:
    return d.replace(day=1)


def _prev_month_start(d: date) -> date:
    if d.month == 1:
        return d.replace(year=d.year - 1, month=12, day=1)
    return d.replace(month=d.month - 1, day=1)


class InsightsService:
    def __init__(self, entries: EntryRepository, categories: CategoryRepository) -> None:
        self._entries = entries
        self._categories = categories

    def _parent_of(self, name: str) -> str:
        c = self._categories.find_by_name(name)
        if c is None:
            return "(uncategorised)"
        if c.is_group:
            return c.name
        return c.parent or "(uncategorised)"

    def generate(self, today: Optional[date] = None) -> List[Dict]:
        today = today or date.today()
        all_entries = self._entries.list()
        if not all_entries:
            return [{"kind": "empty", "title": "No data yet", "detail": "Add entries to see insights."}]

        out: List[Dict] = []

        # 1) anomalous days (z-score) within last 60 days
        recent_cutoff = today.fromordinal(today.toordinal() - 60)
        recent = [e for e in all_entries if e.date >= recent_cutoff]
        daily: Dict[date, float] = defaultdict(float)
        for e in recent:
            daily[e.date] += e.debit
        if len(daily) >= 5:
            vals = list(daily.values())
            mean = statistics.fmean(vals)
            stdev = statistics.pstdev(vals) or 1.0
            ranked = sorted(
                ((d, v, (v - mean) / stdev) for d, v in daily.items() if v > 0),
                key=lambda t: t[2],
                reverse=True,
            )
            for d, v, z in ranked[:2]:
                if z >= 2.0:
                    out.append(
                        {
                            "kind": "anomaly",
                            "title": f"Heavy spend on {d.isoformat()}",
                            "detail": (
                                f"Rs {v:,.0f} vs {mean:,.0f} avg "
                                f"(z={z:.1f}). Recent 60-day window."
                            ),
                        }
                    )

        # 2) MoM delta
        this_m = _month_start(today)
        prev_m = _prev_month_start(this_m)
        this_total = sum(
            e.debit for e in all_entries if _month_start(e.date) == this_m
        )
        prev_total = sum(
            e.debit for e in all_entries if _month_start(e.date) == prev_m
        )
        if prev_total > 0 and this_total > 0:
            delta = this_total - prev_total
            pct = delta / prev_total * 100.0
            direction = "up" if delta >= 0 else "down"
            out.append(
                {
                    "kind": "mom",
                    "title": f"This month is {direction} {abs(pct):.0f}% vs last",
                    "detail": (
                        f"This month Rs {this_total:,.0f} · "
                        f"Last month Rs {prev_total:,.0f}"
                    ),
                }
            )

        # 3) top-group share
        agg: Dict[str, float] = defaultdict(float)
        total = 0.0
        for e in all_entries:
            agg[self._parent_of(e.category)] += e.debit
            total += e.debit
        if total > 0 and agg:
            top_group, top_val = max(agg.items(), key=lambda kv: kv[1])
            share = top_val / total * 100.0
            if share >= 25.0:
                out.append(
                    {
                        "kind": "concentration",
                        "title": f"{top_group} is {share:.0f}% of all spend",
                        "detail": (
                            f"Rs {top_val:,.0f} out of Rs {total:,.0f} all-time. "
                            "Consider setting a tighter budget here."
                        ),
                    }
                )

        # 4) run-rate projection for current month
        days_so_far = max(1, (today - this_m).days + 1)
        if this_total > 0:
            # naive projection: assume same daily run-rate continues to month end
            if today.month == 12:
                next_m = today.replace(year=today.year + 1, month=1, day=1)
            else:
                next_m = today.replace(month=today.month + 1, day=1)
            days_in_month = (next_m - this_m).days
            projected = this_total / days_so_far * days_in_month
            if projected > this_total:
                out.append(
                    {
                        "kind": "runrate",
                        "title": f"Projected month-end: Rs {projected:,.0f}",
                        "detail": (
                            f"At current pace ({days_so_far} of {days_in_month} days), "
                            f"month total tracks toward Rs {projected:,.0f}."
                        ),
                    }
                )

        # 5) weekend vs weekday share
        we = sum(e.debit for e in all_entries if e.date.weekday() >= 5)
        wd = sum(e.debit for e in all_entries if e.date.weekday() < 5)
        if we + wd > 0:
            we_share = we / (we + wd) * 100.0
            if we_share >= 40.0:
                out.append(
                    {
                        "kind": "weekend",
                        "title": f"Weekends are {we_share:.0f}% of spend",
                        "detail": "Two of seven days driving ≥40% of spend — typical for dining/leisure-led patterns.",
                    }
                )

        # 6) biggest single transaction (all-time)
        biggest = max(all_entries, key=lambda e: e.debit)
        if biggest.debit > 0:
            out.append(
                {
                    "kind": "biggest",
                    "title": f"Biggest single transaction: Rs {biggest.debit:,.0f}",
                    "detail": (
                        f"{biggest.date.isoformat()} · {biggest.category} · "
                        f"{biggest.narration or '(no narration)'}"
                    ),
                }
            )

        return out
