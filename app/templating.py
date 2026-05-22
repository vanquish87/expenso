"""Single shared Jinja2 Templates instance + currency / emoji filters."""
from __future__ import annotations

from functools import lru_cache

from fastapi.templating import Jinja2Templates

from .core.settings import settings


# Order matters: more specific keywords first. The matcher returns the first
# hit, so e.g. "BILLO'S FOOD" matches "food" before "billo" -> 🍽️.
_EMOJI_RULES = [
    # Level / quality tags first — get matched BEFORE the general category
    # words ("groceries", "restaurant", "food"), so e.g. "GROCERIES - L1 -
    # BASIC" → 🥖 (not 🛒) and "RESTAURANTS - L3 - LAVISH" → 🥂 (not 🍽️).
    # That spreads visual variety across the typical L1/L2/L3 ladder.
    ("basic", "🥖"),
    ("lavish", "🥂"),
    ("luxury", "💎"),
    ("munch", "🍿"),

    # Specific food items (multi-word phrases before single tokens)
    ("ice cream", "🍦"),
    ("pizza", "🍕"),
    ("burger", "🍔"),
    ("biryani", "🍛"),
    ("kulcha", "🫓"),
    ("paratha", "🫓"),
    ("thali", "🍛"),
    ("samosa", "🥟"),
    ("dal", "🥘"),
    ("snack", "🍪"),
    ("dairy", "🥛"),
    ("milk", "🥛"),
    ("coffee", "☕"),
    ("café", "☕"),
    ("cafe", "☕"),
    ("tea", "🍵"),
    ("juice", "🧃"),
    ("lassi", "🥛"),
    # Generic eat-out / cook-at-home buckets (later so specifics win first).
    # "food" before "beverage" so "FOOD & BEVERAGE" → 🍽️ (a meal) instead
    # of 🍹 (a drink).
    ("restaurant", "🍽️"),
    ("dining", "🍽️"),
    ("groceries", "🛒"),
    ("grocery", "🛒"),
    ("food", "🍽️"),
    ("beverage", "🍹"),

    # Transit / travel — skipping generic "car" / "bus" because they're
    # substring-greedy: "car" matches "personal CARe", "bus" matches
    # "BUSiness". Specific modes (taxi / uber / scooter / bike / metro /
    # rickshaw / train / flight) cover the realistic categories.
    ("petrol", "⛽"),
    ("diesel", "⛽"),
    ("fuel", "⛽"),
    ("scooter", "🛵"),
    ("bike", "🏍️"),
    ("uber", "🚖"),
    ("ola", "🚖"),
    ("taxi", "🚖"),
    ("cab", "🚖"),
    ("rickshaw", "🛺"),
    ("auto", "🛺"),
    ("metro", "🚇"),
    ("train", "🚆"),
    ("flight", "✈️"),
    ("hotel", "🏨"),
    ("travel", "✈️"),
    ("trip", "🧳"),
    ("parking", "🅿️"),
    ("toll", "🛣️"),

    # Utilities & bills (specific bills first so they win over "utilities")
    ("electricity", "💡"),
    ("phone", "📱"),
    ("mobile", "📱"),
    ("recharge", "📱"),
    ("television", "📺"),
    ("netflix", "🎬"),
    ("prime", "📦"),
    ("hotstar", "📺"),
    ("internet", "📶"),
    ("broadband", "📶"),
    ("wifi", "📶"),
    ("water", "💧"),
    ("gas", "🔥"),
    ("rent", "🏠"),
    ("maintenance", "🔧"),
    ("repair", "🔧"),
    # NOTE: no generic "bill" rule on purpose — it would match "BILLO" as a
    # substring and steal the chip away from BILLO sub-categories. Specific
    # bills (electricity / phone / television / gas) already have their own
    # keywords above; a bare "BILL" category falls to the default 🏷️.
    ("utilities", "🔌"),

    # Personal care / health
    ("grooming", "💇"),
    ("personal care", "🧴"),
    ("haircut", "💇"),
    ("salon", "💇"),
    ("spa", "💆"),
    ("medical", "💊"),
    ("medicine", "💊"),
    ("pharmacy", "💊"),
    ("doctor", "🩺"),
    ("dentist", "🦷"),
    ("hospital", "🏥"),
    ("insurance", "🛡️"),

    # Lifestyle / leisure
    ("sport", "🏃"),
    ("gym", "🏋️"),
    ("yoga", "🧘"),
    ("entertainment", "🎬"),
    ("movie", "🎬"),
    ("concert", "🎤"),
    ("game", "🎮"),
    ("subscription", "🔁"),
    ("electronic", "💻"),
    ("laptop", "💻"),
    ("camera", "📷"),
    ("shopping", "🛍️"),
    ("clothes", "👕"),
    ("shoes", "👟"),
    ("books", "📚"),

    # Family / kids / pets / education
    ("school", "🏫"),
    ("tuition", "📚"),
    ("education", "📚"),
    ("toy", "🧸"),
    ("kid", "👶"),
    ("baby", "👶"),
    ("family", "👨‍👩‍👧‍👦"),
    ("pet", "🐾"),
    ("dog", "🐶"),
    ("cat", "🐱"),

    # Money flow
    ("pocket", "👛"),
    ("salary", "💰"),
    ("bonus", "🎉"),
    ("income", "💰"),
    ("freelance", "💼"),
    ("business", "💼"),
    ("emi", "💳"),
    ("credit card", "💳"),
    ("loan", "💳"),
    ("invest", "📈"),
    ("stock", "📈"),
    ("mutual fund", "📈"),
    ("savings", "🐷"),
    ("transfer", "🔁"),
    ("refund", "💸"),

    # Vibe-tags
    ("ghoomna", "🚶"),  # Hindi: roam / outing
    ("walk", "🚶"),
    ("outing", "🎈"),
    ("gift", "🎁"),
    ("birthday", "🎂"),
    ("anniversary", "💐"),
    ("flowers", "💐"),
    ("cake", "🎂"),
    ("party", "🎉"),

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


def _money_int(v) -> str:
    """Display-only integer money with thousands separators.

    Same as ``intish`` but with commas — "14,442" rather than "14442". Used
    in ledger row amounts / day totals / detail page where humans read the
    number; NOT for form value attrs (those still need plain digits the
    browser can parse, hence ``intish`` there).
    """
    try:
        n = float(v)
    except (TypeError, ValueError):
        return "0"
    if n == int(n):
        return f"{int(n):,}"
    return f"{n:,.2f}"


def _emoji_for(v) -> str:
    """Pick an emoji based on keywords found in a category/sub-category name."""
    if not v:
        return _DEFAULT_EMOJI
    nm = str(v).lower()
    for kw, em in _EMOJI_RULES:
        if kw in nm:
            return em
    return _DEFAULT_EMOJI


@lru_cache(maxsize=1)
def _category_icon_overrides() -> dict:
    """Mapping {category_name: icon} for categories that have an explicit
    user-picked emoji. Cached so we don't re-read the CSV on every render;
    invalidated by ``invalidate_category_icon_cache()`` whenever a category
    is created / updated / deleted."""
    # Late import — repos depend on core.settings which depends on us.
    from .repositories.category_repo import CategoryCsvRepository

    repo = CategoryCsvRepository()
    out: dict = {}
    for c in repo.list():
        if c.icon:
            out[c.name] = c.icon
    return out


def invalidate_category_icon_cache() -> None:
    """Drop the override cache so the next template render picks up the
    change. Called from CategoryService on create/update/delete."""
    _category_icon_overrides.cache_clear()


def _cat_emoji(v) -> str:
    """Resolve emoji for a category name, preferring the user-picked icon
    (from the Category row) over the keyword-matched default."""
    if v is None:
        return _DEFAULT_EMOJI
    name = str(v)
    override = _category_icon_overrides().get(name)
    if override:
        return override
    return _emoji_for(name)


def _kind_emoji(v) -> str:
    """Emoji for an insight `kind` (anomaly / mom / concentration / …)."""
    return _KIND_EMOJI.get(str(v), "💡")


templates = Jinja2Templates(directory=str(settings.TEMPLATES_DIR))
templates.env.filters["money"] = _money
templates.env.filters["intish"] = _intish
templates.env.filters["money_int"] = _money_int
templates.env.filters["emoji"] = _cat_emoji  # prefers user-picked, then keyword
templates.env.filters["emoji_kw"] = _emoji_for  # raw keyword matcher (no override lookup)
templates.env.filters["kind_emoji"] = _kind_emoji
templates.env.globals["currency"] = settings.CURRENCY_SYMBOL
