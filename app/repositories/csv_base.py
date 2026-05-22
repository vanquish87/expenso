"""Base CSV repository: atomic writes + RLock for thread safety.

Strategy:
 - Read on demand: cheap files, no need to keep an in-memory cache.
 - Write atomically: write to a sibling tempfile, then os.replace which
   is atomic on the same filesystem on both POSIX and Windows. Crash
   mid-write leaves the previous file intact.
 - RLock around every operation: FastAPI runs sync endpoints on a thread
   pool, so concurrent writes are real. Reentrant so a method may call
   another method that also takes the lock.
"""
from __future__ import annotations

import csv
import os
import tempfile
import threading
from pathlib import Path
from typing import Callable, Generic, Iterable, List, Optional, Type, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class CsvRepository(Generic[T]):
    """Generic CSV-backed repository for a single Pydantic model."""

    def __init__(
        self,
        path: Path,
        model: Type[T],
        fieldnames: List[str],
        row_to_model: Callable[[dict], T],
        model_to_row: Callable[[T], dict],
    ) -> None:
        self._path = path
        self._model = model
        self._fieldnames = fieldnames
        self._row_to_model = row_to_model
        self._model_to_row = model_to_row
        self._lock = threading.RLock()
        self._ensure_file()

    def _ensure_file(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            with self._lock:
                if not self._path.exists():
                    self._write_rows([])

    def _read_rows(self) -> List[T]:
        with self._lock:
            if not self._path.exists() or self._path.stat().st_size == 0:
                return []
            with self._path.open("r", encoding="utf-8", newline="") as fh:
                reader = csv.DictReader(fh)
                return [self._row_to_model(r) for r in reader if any(r.values())]

    def _write_rows(self, items: Iterable[T]) -> None:
        with self._lock:
            tmp_fd, tmp_path = tempfile.mkstemp(
                prefix=self._path.name + ".",
                suffix=".tmp",
                dir=str(self._path.parent),
            )
            try:
                with os.fdopen(tmp_fd, "w", encoding="utf-8", newline="") as fh:
                    writer = csv.DictWriter(fh, fieldnames=self._fieldnames)
                    writer.writeheader()
                    for item in items:
                        writer.writerow(self._model_to_row(item))
                os.replace(tmp_path, self._path)
            except Exception:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
                raise

    def list(self) -> List[T]:
        return self._read_rows()

    def get(self, id_: str) -> Optional[T]:
        for item in self._read_rows():
            if getattr(item, "id") == id_:
                return item
        return None

    def add(self, item: T) -> T:
        with self._lock:
            items = self._read_rows()
            items.append(item)
            self._write_rows(items)
        return item

    def update(self, item: T) -> T:
        with self._lock:
            items = self._read_rows()
            replaced = False
            for i, existing in enumerate(items):
                if getattr(existing, "id") == getattr(item, "id"):
                    items[i] = item
                    replaced = True
                    break
            if not replaced:
                raise KeyError(getattr(item, "id"))
            self._write_rows(items)
        return item

    def delete(self, id_: str) -> None:
        with self._lock:
            items = self._read_rows()
            new_items = [it for it in items if getattr(it, "id") != id_]
            if len(new_items) == len(items):
                raise KeyError(id_)
            self._write_rows(new_items)

    def replace_all(self, items: Iterable[T]) -> None:
        with self._lock:
            self._write_rows(list(items))
