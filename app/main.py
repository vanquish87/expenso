"""FastAPI app factory + entrypoint.

uvicorn target:  app.main:app
"""
from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from . import __version__
from .core.exceptions import ConflictError, ExpensoError, NotFoundError, ValidationError
from .core.settings import settings
from .dependencies import (
    _budget_repo,
    _category_repo,
    _entry_repo,
    get_import_service,
)
from .routers import analytics, api, budgets, categories, entries, home
from .templating import templates

log = logging.getLogger("expenso")


def _seed_if_empty() -> None:
    """If the data dir is empty AND the source xlsx is present, seed it.

    Keeps the "double-click, it just works" promise without surprising
    a user who already has data — we never overwrite a non-empty repo.
    """
    cats = _category_repo().list()
    ents = _entry_repo().list()
    if cats or ents:
        return
    if not settings.SOURCE_XLSX.exists():
        log.info("no data and no source xlsx — starting empty")
        return
    log.info("seeding from %s", settings.SOURCE_XLSX)
    result = get_import_service().reseed_from_xlsx(settings.SOURCE_XLSX)
    log.info("seeded: %s", result)


def create_app() -> FastAPI:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s :: %(message)s")

    app = FastAPI(title="Expenso", version=__version__, docs_url="/docs", redoc_url=None)

    app.mount("/static", StaticFiles(directory=str(settings.STATIC_DIR)), name="static")

    app.include_router(home.router)
    app.include_router(categories.router)
    app.include_router(entries.router)
    app.include_router(budgets.router)
    app.include_router(analytics.router)
    app.include_router(api.router)

    @app.exception_handler(NotFoundError)
    async def _nf(request: Request, exc: NotFoundError):
        if request.url.path.startswith("/api/"):
            return JSONResponse(status_code=404, content={"detail": str(exc)})
        return templates.TemplateResponse(
            "base.html",
            {"request": request, "error": f"Not found: {exc}"},
            status_code=404,
        )

    @app.exception_handler(ConflictError)
    async def _cf(request: Request, exc: ConflictError):
        if request.url.path.startswith("/api/"):
            return JSONResponse(status_code=409, content={"detail": str(exc)})
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(ValidationError)
    async def _vf(request: Request, exc: ValidationError):
        if request.url.path.startswith("/api/"):
            return JSONResponse(status_code=400, content={"detail": str(exc)})
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(ExpensoError)
    async def _ee(request: Request, exc: ExpensoError):
        return JSONResponse(status_code=500, content={"detail": str(exc)})

    @app.on_event("startup")
    def _on_startup() -> None:
        settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
        # Touch the repos so CSV files exist before we serve a request.
        _category_repo(); _entry_repo(); _budget_repo()
        _seed_if_empty()

    @app.get("/healthz", include_in_schema=False, response_class=HTMLResponse)
    def healthz() -> str:
        return "ok"

    return app


app = create_app()
