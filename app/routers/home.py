"""Home dashboard: KPIs + recent entries."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from ..dependencies import (
    get_analytics_service,
    get_entry_service,
    get_insights_service,
)
from ..services.analytics_service import AnalyticsService
from ..services.entry_service import EntryService
from ..services.insights_service import InsightsService
from ..templating import templates

router = APIRouter()


@router.get("/", name="home")
def home(
    request: Request,
    entries: EntryService = Depends(get_entry_service),
    analytics: AnalyticsService = Depends(get_analytics_service),
    insights: InsightsService = Depends(get_insights_service),
):
    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "kpis": analytics.kpis(),
            "recent": entries.recent(8),
            "insights": insights.generate()[:4],
        },
    )
