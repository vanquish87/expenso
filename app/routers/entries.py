"""Entry CRUD with filters."""
from __future__ import annotations

from datetime import date as _date, datetime
from typing import Optional

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
    rows = entries.list_all(
        category=category or None,
        date_from=_parse_date(date_from),
        date_to=_parse_date(date_to),
        q=q or None,
    )
    return templates.TemplateResponse(
        "entries.html",
        {
            "request": request,
            "rows": rows,
            "categories": cats.list_all(),
            "filters": {
                "category": category or "",
                "date_from": date_from or "",
                "date_to": date_to or "",
                "q": q or "",
            },
            "today": _date.today().isoformat(),
            "error": request.query_params.get("error"),
            "ok": request.query_params.get("ok"),
        },
    )


@router.post("", name="entries.create")
def create(
    date: str = Form(...),
    category: str = Form(...),
    narration: str = Form(""),
    debit: float = Form(0.0),
    credit: float = Form(0.0),
    svc: EntryService = Depends(get_entry_service),
):
    d = _parse_date(date)
    if d is None:
        return RedirectResponse("/entries?error=Invalid date", status_code=303)
    try:
        svc.create(
            date_=d,
            category=category,
            narration=narration,
            debit=debit,
            credit=credit,
        )
    except ValidationError as e:
        return RedirectResponse(f"/entries?error={e}", status_code=303)
    except Exception as e:
        return RedirectResponse(f"/entries?error={e}", status_code=303)
    return RedirectResponse("/entries?ok=Created", status_code=303)


@router.post("/{entry_id}/update", name="entries.update")
def update(
    entry_id: str,
    date: str = Form(...),
    category: str = Form(...),
    narration: str = Form(""),
    debit: float = Form(0.0),
    credit: float = Form(0.0),
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
            debit=debit,
            credit=credit,
        )
    except NotFoundError:
        raise HTTPException(status_code=404, detail="entry not found")
    except ValidationError as e:
        return RedirectResponse(f"/entries?error={e}", status_code=303)
    except Exception as e:
        return RedirectResponse(f"/entries?error={e}", status_code=303)
    return RedirectResponse("/entries?ok=Updated", status_code=303)


@router.post("/{entry_id}/delete", name="entries.delete")
def delete(
    entry_id: str,
    svc: EntryService = Depends(get_entry_service),
):
    try:
        svc.delete(entry_id)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="entry not found")
    return RedirectResponse("/entries?ok=Deleted", status_code=303)
