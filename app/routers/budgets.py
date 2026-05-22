"""Budget CRUD + monthly status."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse

from ..core.exceptions import ConflictError, NotFoundError, ValidationError
from ..dependencies import get_budget_service, get_category_service
from ..services.budget_service import BudgetService
from ..services.category_service import CategoryService
from ..templating import templates

router = APIRouter(prefix="/budgets")


@router.get("", name="budgets.index")
def index(
    request: Request,
    bsvc: BudgetService = Depends(get_budget_service),
    csvc: CategoryService = Depends(get_category_service),
):
    return templates.TemplateResponse(
        "budgets.html",
        {
            "request": request,
            "status": bsvc.status(),
            "categories": csvc.list_all(),
            "error": request.query_params.get("error"),
            "ok": request.query_params.get("ok"),
        },
    )


@router.post("", name="budgets.create")
def create(
    category: str = Form(...),
    monthly_cap: float = Form(...),
    svc: BudgetService = Depends(get_budget_service),
):
    try:
        svc.create(category=category, monthly_cap=monthly_cap)
    except (ValidationError, ConflictError) as e:
        return RedirectResponse(f"/budgets?error={e}", status_code=303)
    return RedirectResponse("/budgets?ok=Created", status_code=303)


@router.post("/{budget_id}/update", name="budgets.update")
def update(
    budget_id: str,
    monthly_cap: float = Form(...),
    svc: BudgetService = Depends(get_budget_service),
):
    try:
        svc.update(budget_id, monthly_cap=monthly_cap)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="budget not found")
    except ValidationError as e:
        return RedirectResponse(f"/budgets?error={e}", status_code=303)
    return RedirectResponse("/budgets?ok=Updated", status_code=303)


@router.post("/{budget_id}/delete", name="budgets.delete")
def delete(
    budget_id: str,
    svc: BudgetService = Depends(get_budget_service),
):
    try:
        svc.delete(budget_id)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="budget not found")
    return RedirectResponse("/budgets?ok=Deleted", status_code=303)
