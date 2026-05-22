"""Pydantic v2 domain models — the wire & on-disk shape of every entity."""
from __future__ import annotations

from datetime import date, datetime
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def _new_id() -> str:
    return uuid4().hex[:12]


class Category(BaseModel):
    """A category row: either a top-level group (parent is None) or a sub-category.

    The xlsx uses a 1-level hierarchy: GROUP / MAIN CATEGORY -> SUB-CATEGORY.
    We model both rows as Category with `parent` (= group name) None for groups.

    ``icon`` is an optional explicit emoji override. When set, it wins over the
    name-based keyword matcher in templating.py. Empty / None → auto-pick.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    id: str = Field(default_factory=_new_id)
    name: str = Field(min_length=1, max_length=80)
    parent: Optional[str] = None
    icon: Optional[str] = Field(default=None, max_length=16)

    @field_validator("name")
    @classmethod
    def _normalise_name(cls, v: str) -> str:
        return v.strip()

    @field_validator("parent")
    @classmethod
    def _normalise_parent(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.strip()
        return v or None

    @field_validator("icon")
    @classmethod
    def _normalise_icon(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.strip()
        return v or None

    @property
    def is_group(self) -> bool:
        return self.parent is None


class Entry(BaseModel):
    """A single ledger row: date, category (sub-category name), narration, debit/credit.

    `timestamp` is the precise insertion moment — date supplies the "when did
    this expense happen" axis, timestamp supplies the "in what order was it
    recorded" axis. Bulk imports assign sequential per-date timestamps so
    xlsx row order is preserved; manual creates default to wall-clock now.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    id: str = Field(default_factory=_new_id)
    date: date
    timestamp: datetime = Field(default_factory=datetime.now)
    category: str = Field(min_length=1, max_length=80)
    narration: str = Field(default="", max_length=200)
    debit: float = Field(default=0.0, ge=0)
    credit: float = Field(default=0.0, ge=0)

    @model_validator(mode="after")
    def _at_least_one_side(self) -> "Entry":
        if self.debit == 0 and self.credit == 0:
            raise ValueError("entry must have a non-zero debit or credit")
        if self.debit > 0 and self.credit > 0:
            raise ValueError("entry cannot have both debit and credit > 0")
        return self

    @property
    def signed_amount(self) -> float:
        return self.credit - self.debit


class Budget(BaseModel):
    """Monthly cap for a category (group OR sub-category)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    id: str = Field(default_factory=_new_id)
    category: str = Field(min_length=1, max_length=80)
    monthly_cap: float = Field(gt=0)
