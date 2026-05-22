"""Analytics page (HTML shell) — charts hydrate via /api/analytics/*."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from ..dependencies import get_analytics_service
from ..services.analytics_service import AnalyticsService
from ..templating import templates

router = APIRouter(prefix="/analytics")


@router.get("", name="analytics.index")
def index(
    request: Request,
    analytics: AnalyticsService = Depends(get_analytics_service),
):
    return templates.TemplateResponse(
        "analytics.html",
        {"request": request, "kpis": analytics.kpis()},
    )
