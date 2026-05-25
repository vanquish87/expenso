"""Snapshot the data dir to a timestamped folder inside BACKUP_DIR.

Rolling retention: at most ``EXPENSO_BACKUP_COUNT`` most-recent folders are
kept. The oldest are pruned (by mtime) when a new backup is written.

Triggered automatically on FastAPI shutdown (so any clean exit of the
server — start.bat, manual uvicorn + Ctrl+C, etc. — produces a snapshot).
Can also be invoked manually via ``python scripts/backup.py``.

Freeze-on-destructive-change: each shutdown compares the data dir against
the newest existing snapshot. The backup is *frozen* (no new snapshot,
prune skipped) if any of these is true for any CSV:

  - the file was in the snapshot but is missing in the data dir;
  - the file had rows in the snapshot but is now empty;
  - more than ``_FREEZE_REMOVAL_PCT`` of prior rows are gone AND the
    snapshot had more than ``_FREEZE_MIN_PRIOR_ROWS`` to start with.

Anything below those thresholds — small audit deletions, in-place edits,
pure additions — counts as a normal change and rolls a backup.
"""
from __future__ import annotations

import csv
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..core.settings import settings

log = logging.getLogger("expenso.backup")

_BACKUP_PREFIX = "expenso-backup-"

# Return values of _diff_against_latest().
_DIFF_FIRST = "first"            # no prior snapshot — back up
_DIFF_NONE = "none"              # data dir matches latest snapshot — skip
_DIFF_NORMAL = "normal"          # additions / modifications only — back up
_DIFF_DESTRUCTIVE = "destructive"  # row(s) or file(s) removed — FREEZE

# Freeze thresholds. A CSV losing rows is only flagged destructive when
# the loss is catastrophic, not the 2-9 row trims that happen during
# routine auditing.
_FREEZE_REMOVAL_PCT = 0.5       # > 50% of prior rows gone -> freeze
_FREEZE_MIN_PRIOR_ROWS = 5      # ...but only when prior had more than this
                                # (small files like budgets.csv don't trip
                                # the % rule; only a full wipe will).


def run_backup(
    data_dir: Optional[Path] = None,
    backup_root: Optional[Path] = None,
    keep: Optional[int] = None,
) -> Optional[Path]:
    """Copy every file in ``data_dir`` into a new timestamped folder under
    ``backup_root``, then prune older backups so at most ``keep`` remain.

    Returns the path of the freshly written backup folder, or None if no
    new backup was written (nothing changed, freeze triggered, etc.).
    """
    data_dir = data_dir or settings.DATA_DIR
    backup_root = backup_root or settings.BACKUP_DIR
    keep = keep if keep is not None else settings.BACKUP_COUNT

    if not data_dir.exists():
        log.info("backup skipped — data dir %s doesn't exist", data_dir)
        return None

    # Safety: don't recursively snapshot ourselves if the user pointed
    # BACKUP_DIR inside DATA_DIR.
    try:
        backup_root.resolve().relative_to(data_dir.resolve())
        log.warning("backup skipped — BACKUP_DIR (%s) is inside DATA_DIR (%s)",
                    backup_root, data_dir)
        return None
    except ValueError:
        pass  # not a subpath, all good

    kind = _diff_against_latest(data_dir, backup_root)
    if kind == _DIFF_DESTRUCTIVE:
        log.warning(
            "backup FROZEN — destructive change detected (row(s) or file(s) "
            "removed since last snapshot). Existing snapshots in %s preserved; "
            "prune skipped so the known-good state survives.",
            backup_root,
        )
        return None
    if kind == _DIFF_NONE:
        log.info("backup skipped — data dir matches latest snapshot")
        return None

    files = sorted(p for p in data_dir.iterdir() if p.is_file())
    if not files:
        log.info("backup skipped — data dir %s has no files", data_dir)
        return None

    backup_root.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    target = backup_root / f"{_BACKUP_PREFIX}{ts}"
    # If the same second is reused (rapid stop/start during tests),
    # append a counter so we never clobber an existing snapshot.
    base = target
    counter = 1
    while target.exists():
        counter += 1
        target = base.with_name(f"{base.name}-{counter}")

    target.mkdir(parents=True)
    for f in files:
        shutil.copy2(f, target / f.name)

    log.info("backup written → %s (%d files)", target, len(files))

    _prune(backup_root, keep)
    return target


def _read_ids(p: Path) -> set[str]:
    """Return the set of values from the first column ('id') of a CSV.

    Missing / unreadable file → empty set. Header row is skipped.
    """
    if not p.exists():
        return set()
    try:
        with p.open(newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            if header is None:
                return set()
            return {row[0] for row in reader if row}
    except OSError:
        return set()


def _latest_snapshot(backup_root: Path) -> Optional[Path]:
    if not backup_root.exists():
        return None
    snaps = [
        p for p in backup_root.iterdir()
        if p.is_dir() and p.name.startswith(_BACKUP_PREFIX)
    ]
    if not snaps:
        return None
    return max(snaps, key=lambda p: p.stat().st_mtime)


def _diff_against_latest(data_dir: Path, backup_root: Path) -> str:
    """Compare ``data_dir`` to the newest snapshot under ``backup_root``.

    See module docstring for the freeze rule. Returns one of:
    ``_DIFF_FIRST``, ``_DIFF_NONE``, ``_DIFF_NORMAL``, ``_DIFF_DESTRUCTIVE``.
    """
    latest = _latest_snapshot(backup_root)
    if latest is None:
        return _DIFF_FIRST

    backup_files = {p.name: p for p in latest.iterdir() if p.is_file()}
    data_files = {p.name: p for p in data_dir.iterdir() if p.is_file()}

    any_change = False

    for name, old in backup_files.items():
        new = data_files.get(name)
        if new is None:
            # A previously-tracked file is gone — wipe / rename / deletion.
            log.warning("destructive: %s present in last snapshot, missing in data dir", name)
            return _DIFF_DESTRUCTIVE

        if old.read_bytes() == new.read_bytes():
            continue  # identical, no change

        any_change = True

        # For CSVs, check whether the deletion crosses our freeze thresholds.
        if name.lower().endswith(".csv"):
            old_ids = _read_ids(old)
            new_ids = _read_ids(new)
            removed = old_ids - new_ids
            if not removed:
                continue  # additions / in-place edits only — safe

            # Full wipe of a previously-populated file.
            if old_ids and not new_ids:
                log.warning(
                    "destructive: %s wiped — all %d row(s) removed",
                    name, len(old_ids),
                )
                return _DIFF_DESTRUCTIVE

            # Catastrophic-fraction loss (only enforced once the file is
            # big enough that "% removed" is a meaningful signal).
            if len(old_ids) > _FREEZE_MIN_PRIOR_ROWS:
                pct = len(removed) / len(old_ids)
                if pct > _FREEZE_REMOVAL_PCT:
                    log.warning(
                        "destructive: %d of %d row(s) removed from %s (%.0f%%) "
                        "— above %.0f%% threshold",
                        len(removed), len(old_ids), name,
                        100 * pct, 100 * _FREEZE_REMOVAL_PCT,
                    )
                    return _DIFF_DESTRUCTIVE

    # New files in data_dir that weren't in the last snapshot are additive.
    if data_files.keys() - backup_files.keys():
        any_change = True

    return _DIFF_NORMAL if any_change else _DIFF_NONE


def _prune(backup_root: Path, keep: int) -> None:
    """Keep only the newest ``keep`` snapshots in ``backup_root``.

    ``keep <= 0`` means unlimited. Only folders matching our naming
    prefix are considered — any hand-created folder the user dropped
    into BACKUP_DIR is left alone.
    """
    if keep <= 0:
        return
    snapshots = [
        p for p in backup_root.iterdir()
        if p.is_dir() and p.name.startswith(_BACKUP_PREFIX)
    ]
    snapshots.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    for old in snapshots[keep:]:
        try:
            shutil.rmtree(old)
            log.info("backup pruned → %s", old)
        except OSError as e:
            log.warning("could not prune %s: %s", old, e)
