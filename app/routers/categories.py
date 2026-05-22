"""Category CRUD."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse

from ..core.exceptions import ConflictError, NotFoundError, ValidationError
from ..dependencies import get_category_service
from ..services.category_service import CategoryService
from ..templating import templates

router = APIRouter(prefix="/categories")


@router.get("", name="categories.index")
def index(
    request: Request,
    svc: CategoryService = Depends(get_category_service),
):
    return templates.TemplateResponse(
        "categories.html",
        {
            "request": request,
            "grouped": svc.grouped(),
            "groups": svc.groups(),
            "error": request.query_params.get("error"),
            "ok": request.query_params.get("ok"),
        },
    )


@router.post("", name="categories.create")
def create(
    name: str = Form(...),
    parent: Optional[str] = Form(None),
    svc: CategoryService = Depends(get_category_service),
):
    try:
        svc.create(name=name, parent=parent)
    except (ValidationError, ConflictError) as e:
        return RedirectResponse(f"/categories?error={e}", status_code=303)
    return RedirectResponse("/categories?ok=Created", status_code=303)


@router.post("/{category_id}/update", name="categories.update")
def update(
    category_id: str,
    name: str = Form(...),
    parent: Optional[str] = Form(None),
    svc: CategoryService = Depends(get_category_service),
):
    try:
        svc.update(category_id, name=name, parent=parent)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="category not found")
    except (ValidationError, ConflictError) as e:
        return RedirectResponse(f"/categories?error={e}", status_code=303)
    return RedirectResponse("/categories?ok=Updated", status_code=303)


@router.post("/{category_id}/delete", name="categories.delete")
def delete(
    category_id: str,
    svc: CategoryService = Depends(get_category_service),
):
    try:
        svc.delete(category_id)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="category not found")
    except ConflictError as e:
        return RedirectResponse(f"/categories?error={e}", status_code=303)
    return RedirectResponse("/categories?ok=Deleted", status_code=303)
