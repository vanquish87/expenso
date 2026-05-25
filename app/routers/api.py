"""JSON API powering the analytics dashboard + the top-bar re-import button."""
from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from ..core.exceptions import ValidationError
from ..core.settings import settings
from ..dependencies import (
    get_analytics_service,
    get_import_service,
    get_insights_service,
)
from ..services.analytics_service import AnalyticsService
from ..services.import_service import ImportService
from ..services.insights_service import InsightsService

router = APIRouter(prefix="/api")


def _parse_date(s: Optional[str]) -> Optional[date]:
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        return None


@router.get("/analytics/summary")
def analytics_summary(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    top_n: int = 10,
    analytics: AnalyticsService = Depends(get_analytics_service),
):
    df = _parse_date(date_from)
    dt = _parse_date(date_to)
    return {
        "kpis": analytics.kpis(df, dt),
        "spend_by_group": analytics.spend_by_group(df, dt),
        "top_subcategories": analytics.top_subcategories(top_n, df, dt),
        "daily": analytics.daily_series(df, dt),
        "cumulative": analytics.cumulative_series(df, dt),
        "weekday": analytics.weekday_pattern(df, dt),
        "monthly": analytics.monthly_debit_credit(),
        "top_transactions": analytics.top_transactions(top_n, df, dt),
    }


@router.get("/analytics/insights")
def analytics_insights(
    insights: InsightsService = Depends(get_insights_service),
):
    return {"insights": insights.generate()}


# --- Drill-down endpoints powering the /analytics modal flow ---------------
# Level 1 (groups) is already in /analytics/summary -> spend_by_group.
# These three feed levels 2-4 on demand as the user opens each modal.


@router.get("/analytics/group/{group}/subs")
def analytics_subs_in_group(
    group: str,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    analytics: AnalyticsService = Depends(get_analytics_service),
):
    df, dt = _parse_date(date_from), _parse_date(date_to)
    items = analytics.subs_in_group(group, df, dt)
    total = sum(i["value"] for i in items)
    return {"group": group, "total": round(total, 2), "items": items}


@router.get("/analytics/category/{category}/months")
def analytics_months_for_category(
    category: str,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    analytics: AnalyticsService = Depends(get_analytics_service),
):
    df, dt = _parse_date(date_from), _parse_date(date_to)
    items = analytics.monthly_for_category(category, df, dt)
    total = sum(i["value"] for i in items)
    return {"category": category, "total": round(total, 2), "items": items}


@router.get("/analytics/category/{category}/month/{year_month}/transactions")
def analytics_transactions_in_month(
    category: str,
    year_month: str,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    analytics: AnalyticsService = Depends(get_analytics_service),
):
    df, dt = _parse_date(date_from), _parse_date(date_to)
    items = analytics.transactions_in_category_month(category, year_month, df, dt)
    total_debit = sum(i["debit"] for i in items)
    total_credit = sum(i["credit"] for i in items)
    return {
        "category": category,
        "year_month": year_month,
        "total_debit": round(total_debit, 2),
        "total_credit": round(total_credit, 2),
        "net": round(total_credit - total_debit, 2),
        "items": items,
    }


@router.post("/import/excel")
def reimport_xlsx(
    svc: ImportService = Depends(get_import_service),
):
    try:
        result = svc.reseed_from_xlsx(settings.SOURCE_XLSX)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"ok": True, **result}
