# Expenso

A FastAPI expense tracker with local CSV storage, built on the
`Expense_Tracker_FY2026-27.xlsx` schema
(Date · Category · Narration · Debit · Credit, with a one-level
Group → Sub-category hierarchy).

## Quick start

Double-click **`start.bat`** (or run `.\start.ps1`).
The script creates a venv with Python 3.9, installs requirements,
opens [http://127.0.0.1:8000/](http://127.0.0.1:8000/), and starts
uvicorn. Safe to re-run.

First launch seeds `data/*.csv` from the workbook on your Desktop
(or wherever `EXPENSO_SOURCE_XLSX` points).

## Routes

| Route | What it does |
| --- | --- |
| `/` | Home dashboard — KPIs + recent entries + first 4 insights |
| `/categories` | Group / sub-category CRUD |
| `/entries` | Date · Category · Narration · Debit · Credit CRUD + filters |
| `/budgets` | Per-category monthly caps with group rollup |
| `/analytics` | Chart.js dashboard (6 KPIs + 6 charts + top txns + insights) |
| `/api/analytics/summary` | JSON aggregations powering the dashboard |
| `/api/analytics/insights` | Rule-based intelligence (anomalies, MoM, run-rate, …) |
| `/api/import/excel` | Re-seed from the source workbook (top-bar button) |
| `/healthz` | Liveness probe |

## Architecture (SOLID + layered MVC)

```
app/
├── core/          settings + exception types
├── domain/        Pydantic models + Repository Protocol (Dependency Inversion)
├── repositories/  CSV-backed repos with atomic writes + thread lock
├── services/      business logic (one job per file)
├── routers/       FastAPI controllers (thin)
├── templates/     Jinja views
└── static/        CSS + vanilla JS + Chart.js (CDN)
data/              categories.csv, entries.csv, budgets.csv (gitignored)
```

Services depend on the Repository Protocols in
[app/domain/interfaces.py](app/domain/interfaces.py), so swapping
CSV → SQLite is a single new class away.
