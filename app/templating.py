"""Single shared Jinja2 Templates instance + currency filter."""
from __future__ import annotations

from fastapi.templating import Jinja2Templates

from .core.settings import settings


def _money(v) -> str:
    try:
        return f"{settings.CURRENCY_SYMBOL}{float(v):,.2f}"
    except (TypeError, ValueError):
        return f"{settings.CURRENCY_SYMBOL}0.00"


templates = Jinja2Templates(directory=str(settings.TEMPLATES_DIR))
templates.env.filters["money"] = _money
templates.env.globals["currency"] = settings.CURRENCY_SYMBOL
