"""Category business logic: group/sub-cat hierarchy + safe delete."""
from __future__ import annotations

from typing import List, Optional

from ..core.exceptions import ConflictError, NotFoundError, ValidationError
from ..domain.interfaces import CategoryRepository, EntryRepository
from ..domain.models import Category
from ..templating import invalidate_category_icon_cache


class CategoryService:
    def __init__(self, repo: CategoryRepository, entries: EntryRepository) -> None:
        self._repo = repo
        self._entries = entries

    def list_all(self) -> List[Category]:
        return sorted(
            self._repo.list(),
            key=lambda c: (c.parent or "", c.parent is not None, c.name.lower()),
        )

    def groups(self) -> List[Category]:
        return [c for c in self._repo.list() if c.is_group]

    def sub_categories(self) -> List[Category]:
        return [c for c in self._repo.list() if not c.is_group]

    def grouped(self) -> List[dict]:
        items = self._repo.list()
        groups = [g for g in items if g.is_group]
        subs_by_parent: dict[str, List[Category]] = {}
        for s in items:
            if not s.is_group:
                subs_by_parent.setdefault(s.parent or "", []).append(s)
        for v in subs_by_parent.values():
            v.sort(key=lambda c: c.name.lower())
        out: List[dict] = []
        for g in sorted(groups, key=lambda c: c.name.lower()):
            out.append({"group": g, "subs": subs_by_parent.get(g.name, [])})
        orphan_keys = sorted(set(subs_by_parent) - {g.name for g in groups})
        for k in orphan_keys:
            out.append({"group": Category(name=k or "(uncategorised)"), "subs": subs_by_parent[k]})
        return out

    def get(self, category_id: str) -> Category:
        c = self._repo.get(category_id)
        if c is None:
            raise NotFoundError(f"category {category_id} not found")
        return c

    def create(self, name: str, parent: Optional[str], icon: Optional[str] = None) -> Category:
        name = (name or "").strip()
        parent = (parent or "").strip() or None
        icon = (icon or "").strip() or None
        if not name:
            raise ValidationError("name is required")
        if self._repo.find_by_name(name):
            raise ConflictError(f"category '{name}' already exists")
        if parent:
            p = self._repo.find_by_name(parent)
            if p is None:
                raise ValidationError(f"parent '{parent}' does not exist")
            if not p.is_group:
                raise ValidationError(f"parent '{parent}' is itself a sub-category")
        c = self._repo.add(Category(name=name, parent=parent, icon=icon))
        invalidate_category_icon_cache()
        return c

    def update(
        self,
        category_id: str,
        name: str,
        parent: Optional[str],
        icon: Optional[str] = None,
    ) -> Category:
        existing = self.get(category_id)
        new_name = (name or existing.name).strip()
        new_parent = (parent or "").strip() or None
        new_icon = (icon or "").strip() or None

        if new_name.lower() != existing.name.lower():
            clash = self._repo.find_by_name(new_name)
            if clash and clash.id != category_id:
                raise ConflictError(f"category '{new_name}' already exists")

        if new_parent:
            p = self._repo.find_by_name(new_parent)
            if p is None:
                raise ValidationError(f"parent '{new_parent}' does not exist")
            if p.id == category_id:
                raise ValidationError("a category cannot be its own parent")
            if not p.is_group:
                raise ValidationError(f"parent '{new_parent}' is itself a sub-category")

        if existing.is_group and not new_parent and new_name != existing.name:
            for s in self.sub_categories():
                if (s.parent or "") == existing.name:
                    s_new = Category(id=s.id, name=s.name, parent=new_name, icon=s.icon)
                    self._repo.update(s_new)

        updated = Category(id=category_id, name=new_name, parent=new_parent, icon=new_icon)
        result = self._repo.update(updated)
        invalidate_category_icon_cache()
        return result

    def delete(self, category_id: str) -> None:
        existing = self.get(category_id)
        if existing.is_group:
            children = [s for s in self.sub_categories() if (s.parent or "") == existing.name]
            if children:
                raise ConflictError(
                    f"cannot delete group '{existing.name}': has {len(children)} sub-categor"
                    f"{'ies' if len(children) != 1 else 'y'}"
                )
        live = sum(1 for e in self._entries.list() if e.category == existing.name)
        if live:
            raise ConflictError(
                f"cannot delete '{existing.name}': {live} entr"
                f"{'ies' if live != 1 else 'y'} reference it"
            )
        self._repo.delete(category_id)
        invalidate_category_icon_cache()
