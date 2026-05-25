"""Analytics page (HTML shell) — drill-down hydrates via /api/analytics/*."""
from __future__ import annotations

from fastapi import APIRouter, Request

from ..templating import templates

router = APIRouter(prefix="/analytics")


@router.get("", name="analytics.index")
def index(request: Request):
    return templates.TemplateResponse("analytics.html", {"request": request})
