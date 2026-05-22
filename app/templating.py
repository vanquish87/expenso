"""Single shared Jinja2 Templates instance + currency / emoji filters."""
from __future__ import annotations

from fastapi.templating import Jinja2Templates

from .core.settings import settings


# Order matters: more specific keywords first. The matcher returns the first
# hit, so e.g. "BILLO'S FOOD" matches "food" before "billo" -> 🍽️.
_EMOJI_RULES = [
    # Food & drink
    ("ice cream", "🍦"),
    ("pizza", "🍕"),
    ("munch", "🍿"),
    ("café", "☕"),
    ("cafe", "☕"),
    ("restaurant", "🍽️"),
    ("groceries", "🛒"),
    ("snack", "🍪"),
    ("beverage", "🍹"),
    ("dairy", "🥛"),
    ("food", "🍽️"),
    # Transit / travel
    ("petrol", "⛽"),
    ("fuel", "⛽"),
    ("taxi", "🚖"),
    ("cab", "🚖"),
    ("metro", "🚇"),
    ("flight", "✈️"),
    ("travel", "✈️"),
    ("trip", "🧳"),
    # Utilities & bills
    ("electricity", "💡"),
    ("phone", "📱"),
    ("television", "📺"),
    ("internet", "📶"),
    ("water", "💧"),
    ("gas", "🔥"),
    ("rent", "🏠"),
    # NOTE: no generic "bill" rule on purpose — it would match "BILLO" as a
    # substring and steal the chip away from BILLO sub-categories. Specific
    # bills (electricity / phone / television / gas) already have their own
    # keywords above; a bare "BILL" category falls to the default 🏷️.
    ("utilities", "🔌"),
    # Personal care / health
    ("grooming", "💇"),
    ("personal care", "🧴"),
    ("salon", "💇"),
    ("medical", "💊"),
    ("medicine", "💊"),
    ("doctor", "🩺"),
    ("hospital", "🏥"),
    # Lifestyle
    ("sport", "🏃"),
    ("gym", "🏋️"),
    ("entertainment", "🎬"),
    ("movie", "🎬"),
    ("subscription", "🔁"),
    ("electronic", "💻"),
    ("shopping", "🛍️"),
    ("clothes", "👕"),
    ("books", "📚"),
    # Family / kids / pets
    ("school", "🏫"),
    ("education", "📚"),
    ("toy", "🧸"),
    ("kid", "👶"),
    ("baby", "👶"),
    ("family", "👨‍👩‍👧‍👦"),
    ("pet", "🐾"),
    # Money flow
    ("pocket", "👛"),
    ("salary", "💰"),
    ("income", "💰"),
    ("emi", "💳"),
    ("loan", "💳"),
    ("invest", "📈"),
    ("savings", "🐷"),
    # Vibe-tags
    ("ghoomna", "🚶"),  # Hindi: roam / outing
    ("gift", "🎁"),
    ("birthday", "🎂"),
    ("cake", "🎂"),
    ("lavish", "🥂"),
    ("luxury", "💎"),
    # Named bucket — last so specific sub-cats match their own keyword first.
    ("billo", "🐶"),
]

_DEFAULT_EMOJI = "🏷️"

# For the insights list (rule keys are fixed in insights_service.py).
_KIND_EMOJI = {
    "anomaly": "🚨",
    "mom": "📈",
    "concentration": "🎯",
    "runrate": "🔮",
    "weekend": "🎉",
    "biggest": "🏆",
    "empty": "✨",
}


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


def _emoji_for(v) -> str:
    """Pick an emoji based on keywords found in a category/sub-category name."""
    if not v:
        return _DEFAULT_EMOJI
    nm = str(v).lower()
    for kw, em in _EMOJI_RULES:
        if kw in nm:
            return em
    return _DEFAULT_EMOJI


def _kind_emoji(v) -> str:
    """Emoji for an insight `kind` (anomaly / mom / concentration / …)."""
    return _KIND_EMOJI.get(str(v), "💡")


templates = Jinja2Templates(directory=str(settings.TEMPLATES_DIR))
templates.env.filters["money"] = _money
templates.env.filters["intish"] = _intish
templates.env.filters["emoji"] = _emoji_for
templates.env.filters["kind_emoji"] = _kind_emoji
templates.env.globals["currency"] = settings.CURRENCY_SYMBOL
