# Changelog

All notable changes to Expenso are tracked here. One section per release;
each release wraps up a coherent batch of work (≈ one development session).

**Format:** [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) —
sections are `Added`, `Changed`, `Fixed`, `Removed`.

**Versioning:** CalVer — `YYYY.MM.N` where **N** is the release-within-the-
month counter. CalVer instead of SemVer because Expenso is a single-user
app — "did this break my integration?" isn't a useful question when there
is no integration. The date *is* the version.

---

## How to ship a new version

When you've batched up a meaningful chunk of changes:

1. **Pick the new version** following CalVer (`YYYY.MM.N`):
   - Same month as the last release → increment **N**.
   - First release of a new month → start at **.1**.
2. **Bump** `__version__` in `app/__init__.py` to the new string.
3. **Move** everything under `## [Unreleased]` into a new section directly
   above it: `## [YYYY.MM.N] — YYYY-MM-DD`. Leave `[Unreleased]` empty for
   the next batch.
4. **Commit** with `docs(changelog): release YYYY.MM.N`.
5. **Tag** (optional but tidy):
   ```bash
   git tag v2026.05.1
   ```
   Tags let you `git checkout v2026.04.3` later to inspect or revert to
   a specific release.

---

## [Unreleased]

_(Nothing yet — next batch of changes lands here first.)_

---

## [2026.05.1] — 2026-05-25

The "protect the data + make analytics actually useful" release.

### Added

- 🛟 **Rolling shutdown backups.** Every clean server exit snapshots the
  data dir into `EXPENSO_BACKUP_DIR/expenso-backup-<timestamp>/`, keeping
  the newest `EXPENSO_BACKUP_COUNT` (default 5). New `scripts/backup.py`
  runs the same flow on demand. Two env vars in `.env.example`.
- 🛟 **Freeze-on-destructive-change.** If a backup attempt sees a CSV
  missing, fully wiped, or **> 50%** of rows removed (when there were
  more than 5 to start), it skips the new snapshot *and* skips pruning,
  so older known-good snapshots survive a wipe.
- 🔍 **Drill-down analytics** — five levels, stacked-modal navigation:
  - **L1** (page): groups donut + list, with date range filter at top
  - **L2** (modal): sub-categories inside one group
  - **L3** (modal): monthly bar chart for one sub
  - **L4** (modal): transactions in one (sub, month), day-grouped
  - **L5** (modal): view / edit / delete a single transaction
- 🔍 Three new JSON endpoints under `/api/analytics/*` feeding L2–L4.
- 🎨 **1,000+ emoji icon picker** — replaces the inline ~80-emoji grid
  on `/categories`. Eight sections (Smileys, People, Animals & Nature,
  Food & Drink, Activity, Travel & Places, Objects, Symbols) with a
  sticky tab strip; active tab follows your scroll position.
- 🔎 **Picker search box.** Auto-focused; live filters by Unicode CLDR
  name + a curated synonyms dict, so `pizza` 🍕, `car` 🚗, `biryani` 🍛,
  `billo` 🐶, `office` 💼 all match without you knowing the official
  Unicode name.

### Changed

- 🔁 **Renaming a category cascades** into `entries.csv` and `budgets.csv`.
  Previously the rename only touched `categories.csv`; every historical
  row referencing the old name became "(uncategorised)". Now references
  are rewritten atomically — including when you rename a group whose
  sub-categories already update their `parent` field.
- ⬇️ **Analytics modals navigate, they don't stack.** Opening L3 hides L2;
  the back arrow re-shows it. Backdrop click closes everything; X
  closes everything; Esc steps back one level.
- 🧠 **"Smart bits" insights moved to `/home`.** They were on the old
  analytics dashboard; the drill-down replacement is focused on
  follow-the-money, so the rules-based insights now live alongside the
  KPI strip and Recent Entries on the home page.

### Fixed

- 📊 Donut chart no longer hogs the modal — pinned `.drill__chart`
  containers to fixed pixel heights + `maintainAspectRatio: false`;
  legend font 11→10px.
- 📊 L4 transaction rows actually render now — `renderTxList()` built
  `<li><button>` correctly but never appended `<li>` to the day's
  `<ul>`. One-liner fix.
- 💰 Monthly Average no longer = Total Spend when no date range is set.
  Computes the data span from the summary `monthly` array; ~2-month
  span of Rs 411K reads as ~Rs 206K/month, not Rs 411K.
- 🐛 Browser-cache trap surfaced — added a `reportErr` handler so
  next time a JS load fails silently, the failure shows in the UI
  instead of leaving the page mysteriously blank.

### Removed

- Old `/analytics` dashboard layout — KPI strip, 6-chart grid (Spend
  by group, Top sub-categories, Daily, Cumulative, Weekday, Monthly
  D/C), top-10 transactions table, insights list. Their service
  methods are kept (still powering `/home`), but the analytics page
  itself is now the drill-down flow described above.

---

## [2026.05.0] — 2026-05-23

The "make it feel like a real app, not a CSV viewer" release.

### Added

- 👆 **Detail modal on `/entries`** — clean dialog with date, category,
  amount, narration. Pencil ✎ flips to inline edit form (same modal,
  dual-mode); 🗑 deletes with confirm.
- 🎨 **Per-category icon picker (initial).** Circle button next to each
  category on `/categories` opens a modal with ~80 hand-picked emojis;
  user pick overrides the auto-keyword matcher.
- 🎨 **`icon` column on `categories.csv`** — honored everywhere the
  category name renders.
- ⚡ **HTMX in-place updates** on `/entries` — Add / Delete / Filter
  swap only the ledger fragment; no full page reload, no scroll jump.
- 🌑 **AMOLED dark theme** with hamburger nav under 1024 px.
- ⚙️ **`.env` support** — `EXPENSO_DATA_DIR` points the CSV folder at
  any drive / synced folder.
- 🕐 **Timestamp column on `entries.csv`** so ledger order is
  deterministic within a date (xlsx row order preserved on import,
  newest-first manually).

### Changed

- 📅 Ledger grouped by date — day cards with circular icons, AMOLED
  black background, hover affordances throughout.
- 🧠 Auto-icon keyword matcher broadened — level tags (`L1 BASIC`,
  `L2 MUNCH`, `L3 LAVISH`) win over generic category words for more
  visual variety in long ladder hierarchies.
- 💰 Money formatting — trailing `.00` dropped for whole numbers;
  thousands separators in the ledger; right-aligned amount column.

### Fixed

- 🔢 Newest-first ordering end-to-end (within-day too, not just across).
- 🪟 Hamburger nav now overlays content instead of pushing it down.
- 📋 Form values preserved when Add fails validation.

---

## [2026.05.0-dev] — 2026-05-22

Initial scaffolding. Recorded for completeness; not a tagged release.

### Added

- FastAPI + Jinja + HTMX scaffold with `/`, `/categories`, `/entries`,
  `/budgets`, `/analytics`.
- CSV-backed repositories (atomic tempfile + rename, thread lock,
  never-deleted file invariant).
- Pydantic v2 domain models for Category / Entry / Budget.
- xlsx re-import flow (top-bar button) and first-run seed.
- Chart.js dashboard on `/analytics` (replaced in 2026.05.1).
- Rules-based insights service: anomaly days, MoM %, concentration,
  run-rate forecast, weekend share, biggest single buy.
- Money / emoji Jinja filters.
