"""Composition root: build singleton repos + services and hand them to FastAPI's DI.

Lives at app/ level (not inside core/) because it depends on every layer
below — keeping it here avoids import cycles and matches the typical
"composition root sits at the top" pattern.
"""
from __future__ import annotations

from functools import lru_cache

from .repositories.budget_repo import BudgetCsvRepository
from .repositories.category_repo import CategoryCsvRepository
from .repositories.entry_repo import EntryCsvRepository
from .services.analytics_service import AnalyticsService
from .services.budget_service import BudgetService
from .services.category_service import CategoryService
from .services.entry_service import EntryService
from .services.import_service import ImportService
from .services.insights_service import InsightsService


@lru_cache(maxsize=1)
def _category_repo() -> CategoryCsvRepository:
    return CategoryCsvRepository()


@lru_cache(maxsize=1)
def _entry_repo() -> EntryCsvRepository:
    return EntryCsvRepository()


@lru_cache(maxsize=1)
def _budget_repo() -> BudgetCsvRepository:
    return BudgetCsvRepository()


def get_category_service() -> CategoryService:
    return CategoryService(_category_repo(), _entry_repo())


def get_entry_service() -> EntryService:
    return EntryService(_entry_repo(), _category_repo())


def get_budget_service() -> BudgetService:
    return BudgetService(_budget_repo(), _category_repo(), _entry_repo())


def get_analytics_service() -> AnalyticsService:
    return AnalyticsService(_entry_repo(), _category_repo())


def get_insights_service() -> InsightsService:
    return InsightsService(_entry_repo(), _category_repo())


def get_import_service() -> ImportService:
    return ImportService(_category_repo(), _entry_repo(), _budget_repo())
