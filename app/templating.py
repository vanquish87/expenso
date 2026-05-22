"""Single shared Jinja2 Templates instance + currency filter."""
from __future__ import annotations

from fastapi.templating import Jinja2Templates

from .core.settings import settings


def _money(v) -> str:
    """Format as currency. Whole numbers render without trailing .00."""
    try:
        n = float(v)
    except (TypeError, ValueError):
        return f"{settings.CURRENCY_SYMBOL}0"
    if n == int(n):
        return f"{settings.CURRENCY_SYMBOL}{int(n):,}"
    return f"{settings.CURRENCY_SYMBOL}{n:,.2f}"


def _intish(v) -> str:
    """Raw number for input/data-* values. Whole numbers render as int, else 2dp."""
    try:
        n = float(v)
    except (TypeError, ValueError):
        return "0"
    if n == int(n):
        return str(int(n))
    return f"{n:.2f}"


templates = Jinja2Templates(directory=str(settings.TEMPLATES_DIR))
templates.env.filters["money"] = _money
templates.env.filters["intish"] = _intish
templates.env.globals["currency"] = settings.CURRENCY_SYMBOL
