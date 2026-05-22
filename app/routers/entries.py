"""Entry CRUD with filters."""
from __future__ import annotations

from datetime import date as _date, datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse

from ..core.exceptions import NotFoundError, ValidationError
from ..dependencies import get_category_service, get_entry_service
from ..services.category_service import CategoryService
from ..services.entry_service import EntryService
from ..templating import templates

router = APIRouter(prefix="/entries")


def _parse_date(s: Optional[str]) -> Optional[_date]:
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        return None


def _parse_money(s: Optional[str]) -> float:
    """Form blanks come through as '' for type=number; treat them as 0."""
    s = (s or "").strip()
    if not s:
        return 0.0
    try:
        return float(s)
    except ValueError:
        return 0.0


def _is_htmx(request: Request) -> bool:
    """HTMX sets HX-Request: true on every request it triggers."""
    return request.headers.get("hx-request", "").lower() == "true"


def _render_ledger_root(
    request: Request,
    entries_svc: EntryService,
    *,
    filters: Optional[Dict[str, Optional[str]]] = None,
):
    """Render JUST the #ledger-root partial — used as HTMX response after
    Add / Delete / Filter so we swap only the ledger, not the whole page."""
    f = filters or {}
    rows = entries_svc.list_all(
        category=(f.get("category") or None),
        date_from=_parse_date(f.get("date_from")),
        date_to=_parse_date(f.get("date_to")),
        q=(f.get("q") or None),
    )
    return templates.TemplateResponse(
        "partials/_ledger_root.html",
        {"request": request, "rows": rows},
    )


def _render_add_form(
    request: Request,
    cats_svc: CategoryService,
    *,
    form: Optional[Dict[str, Any]] = None,
    inline_error: Optional[str] = None,
):
    """Render JUST the Add-entry form partial — used as HTMX response on
    validation error so the form re-renders in place with values + banner."""
    return templates.TemplateResponse(
        "partials/_add_form.html",
        {
            "request": request,
            "categories": cats_svc.list_all(),
            "today": _date.today().isoformat(),
            "form": form or {},
            "inline_error": inline_error,
        },
    )


def _humanize_error(e: Exception) -> str:
    """One-line, user-friendly message out of any exception we may raise.

    pydantic.ValidationError has a ``.errors()`` list with ``msg`` keys; the
    default ``str(e)`` is the multi-line debug form ("1 validation error for
    Entry / Value error, ..."). Pull just the message and strip the
    "Value error, " prefix pydantic adds for @model_validator raises.
    """
    if hasattr(e, "errors") and callable(getattr(e, "errors")):
        try:
            errs = e.errors()
            if errs:
                msgs = []
                for err in errs:
                    m = err.get("msg", "") if isinstance(err, dict) else ""
                    if m.startswith("Value error, "):
                        m = m[len("Value error, "):]
                    if m:
                        msgs.append(m)
                if msgs:
                    return "; ".join(msgs)
        except Exception:
            pass
    return str(e)


def _render_entries(
    request: Request,
    entries_svc: EntryService,
    cats_svc: CategoryService,
    *,
    error: Optional[str] = None,
    ok: Optional[str] = None,
    form: Optional[Dict[str, Any]] = None,
    filters: Optional[Dict[str, Optional[str]]] = None,
):
    """Single source of truth for /entries rendering.

    Used by GET index and by POST create-on-error so the page comes back
    with the user's typed values intact + an error banner — instead of
    a redirect that throws the form away.
    """
    f = filters or {}
    rows = entries_svc.list_all(
        category=(f.get("category") or None),
        date_from=_parse_date(f.get("date_from")),
        date_to=_parse_date(f.get("date_to")),
        q=(f.get("q") or None),
    )
    return templates.TemplateResponse(
        "entries.html",
        {
            "request": request,
            "rows": rows,
            "categories": cats_svc.list_all(),
            "filters": {
                "category": f.get("category") or "",
                "date_from": f.get("date_from") or "",
                "date_to": f.get("date_to") or "",
                "q": f.get("q") or "",
            },
            "today": _date.today().isoformat(),
            "error": error,
            "ok": ok,
            "form": form or {},
        },
    )


@router.get("", name="entries.index")
def index(
    request: Request,
    category: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    q: Optional[str] = None,
    entries: EntryService = Depends(get_entry_service),
    cats: CategoryService = Depends(get_category_service),
):
    filters = {"category": category, "date_from": date_from, "date_to": date_to, "q": q}
    # HTMX request → just the ledger partial (filter form swaps it in).
    if _is_htmx(request):
        return _render_ledger_root(request, entries, filters=filters)
    return _render_entries(
        request, entries, cats,
        error=request.query_params.get("error"),
        ok=request.query_params.get("ok"),
        filters=filters,
    )


@router.post("", name="entries.create")
def create(
    request: Request,
    date: str = Form(...),
    category: str = Form(...),
    narration: str = Form(""),
    debit: str = Form(""),
    credit: str = Form(""),
    svc: EntryService = Depends(get_entry_service),
    cats: CategoryService = Depends(get_category_service),
):
    form = {
        "date": date,
        "category": category,
        "narration": narration,
        "debit": debit,
        "credit": credit,
    }
    htmx = _is_htmx(request)

    def _error_response(msg: str):
        # HTMX → swap the Add-form partial (with banner + values).
        # Non-HTMX → re-render the full page with values preserved.
        if htmx:
            resp = _render_add_form(request, cats, form=form, inline_error=msg)
            # The form's hx-target is #ledger-root for success; on error
            # tell HTMX to swap the form's own wrapper instead.
            resp.headers["HX-Retarget"] = "#entry-add-form-wrap"
            resp.headers["HX-Reswap"] = "outerHTML"
            return resp
        return _render_entries(request, svc, cats, error=msg, form=form)

    d = _parse_date(date)
    if d is None:
        return _error_response("Invalid date")
    try:
        svc.create(
            date_=d,
            category=category,
            narration=narration,
            debit=_parse_money(debit),
            credit=_parse_money(credit),
        )
    except Exception as e:
        return _error_response(_humanize_error(e))

    # Success
    if htmx:
        return _render_ledger_root(request, svc)
    return RedirectResponse("/entries?ok=Created", status_code=303)


@router.post("/{entry_id}/update", name="entries.update")
def update(
    entry_id: str,
    date: str = Form(...),
    category: str = Form(...),
    narration: str = Form(""),
    debit: str = Form(""),
    credit: str = Form(""),
    svc: EntryService = Depends(get_entry_service),
):
    d = _parse_date(date)
    if d is None:
        return RedirectResponse("/entries?error=Invalid date", status_code=303)
    try:
        svc.update(
            entry_id,
            date_=d,
            category=category,
            narration=narration,
            debit=_parse_money(debit),
            credit=_parse_money(credit),
        )
    except NotFoundError:
        raise HTTPException(status_code=404, detail="entry not found")
    except Exception as e:
        from urllib.parse import quote
        return RedirectResponse(
            f"/entries?error={quote(_humanize_error(e))}",
            status_code=303,
        )
    return RedirectResponse("/entries?ok=Updated", status_code=303)


@router.post("/{entry_id}/delete", name="entries.delete")
def delete(
    request: Request,
    entry_id: str,
    svc: EntryService = Depends(get_entry_service),
):
    try:
        svc.delete(entry_id)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="entry not found")
    if _is_htmx(request):
        return _render_ledger_root(request, svc)
    return RedirectResponse("/entries?ok=Deleted", status_code=303)
