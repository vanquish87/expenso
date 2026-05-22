"""Domain exception hierarchy — routers translate these into HTTP responses."""
from __future__ import annotations


class ExpensoError(Exception):
    """Base for all expenso domain errors."""


class NotFoundError(ExpensoError):
    """Requested entity does not exist."""


class ValidationError(ExpensoError):
    """Input failed business-rule validation (distinct from pydantic shape errors)."""


class ConflictError(ExpensoError):
    """Operation refused because it would violate referential integrity."""
