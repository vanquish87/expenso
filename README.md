# 💸 Expenso

A friendly little expense tracker that turns your **Expense_Tracker_FY2026-27.xlsx**
into a real web app — same columns (Date · Category · Narration · Debit · Credit),
plus a date-grouped ledger, charts, budgets, and a dashboard that actually tells
you stuff. 🪄

No database to install. No cloud account. Your data lives in plain **CSV files**
on your computer, so you can open them in Excel any time. 📂

---

## 🚀 Get started in 30 seconds

1. Double-click **`start.bat`** 🖱️ (or run `.\start.ps1` in PowerShell)
2. Wait a few seconds while it sets things up ⏳
3. Your browser opens to **http://127.0.0.1:8000/** 🎉

That's it. First run reads your spreadsheet and fills the app. Press `Ctrl+C` in
the black window to stop.

> 💡 Need to re-import from the spreadsheet later? Hit the **↻ Re-import** button
> in the top-right of any page.

---

## 🗺️ What's inside

| Where | What you can do |
| --- | --- |
| 🏠 **Home** | Quick KPIs + your latest entries + smart insights |
| 🏷️ **Categories** | Groups + sub-categories with **per-category icon picker** 🎨 |
| 📝 **Entries** | Day-grouped ledger; tap a row → detail modal with edit / delete |
| 🎯 **Budgets** | Set a monthly cap per category — see how close you are |
| 📊 **Analytics** | Chart.js dashboard: doughnuts, lines, bars, top spends, insights |

---

## ✨ Things that make it pleasant to use

- 📅 **Day-grouped ledger** — entries cluster under a date header showing the
  day's net (`-1,629`), with a circular emoji icon on every row.
- 👆 **Tap a row → detail modal** — click any ledger row, the whole entry
  pops up cleanly. Pencil ✎ flips it into an inline **edit form** without
  leaving the modal; Save/Cancel flip back. 🗑 deletes (with confirm).
- ⚡ **HTMX makes it snappy** — Add entry, Filter, Delete, Edit all update
  the ledger **in place**, no full page reload, no scroll jump.
- 🎨 **Pick any emoji per category** — on `/categories`, click the
  circular icon next to a name → grid of ~80 emojis pops up → pick one.
  Auto-detection still works (a `GROCERIES` category guesses 🛒) so you
  only customise when you want to.
- 🧠 **Auto-icons get clever** — `GROCERIES - L1 - BASIC` → 🥖,
  `GROCERIES - L2 - MUNCH` → 🍿, `RESTAURANTS - L3 - LAVISH` → 🥂,
  `BILLO'S POCKET` → 👛, …
- 📱 **Mobile / iPad ready** — at ≤ 1024 px the nav becomes a ☰ drawer,
  the entries form collapses into a tabbed card (Add / Filters), the
  ledger turns into stacked cards. AMOLED-friendly pure-black palette.
- 💾 **Your data, your folder** — point `EXPENSO_DATA_DIR` at any drive
  (external SSD, Dropbox, …) via `.env`. The CSV files themselves are
  **never deleted** by the app, only ever rewritten atomically.
- 🛟 **Rolling backups on every shutdown** — each Ctrl+C snapshots your
  data dir into a timestamped folder under `EXPENSO_BACKUP_DIR`, keeping
  the newest 5. A built-in **freeze** kicks in if it looks like data was
  wiped or mass-deleted, so older known-good snapshots can't be aged out
  by a disaster. 🔒

---

## 🧠 The smart bits

Expenso doesn't just show numbers — it points out things you'd otherwise miss:

- 🚨 **Anomaly days** — "Heavy spend on May 9 — Rs 80,835 vs Rs 8,237 average"
- 📈 **Month-over-month** — "This month is up 28% vs last"
- 🎯 **Concentration** — "FAMILY TRAVEL is 45% of all spend"
- 🔮 **Month-end forecast** — "At current pace, you'll hit Rs 325,662"
- 🎉 **Weekend share** — flagged when ≥ 40% of spend lands on Sat/Sun
- 🏆 **Biggest single buy** — that one transaction that bent the chart

All rules-based, no AI guesses, no data leaves your laptop. 🔒

---

## 🧾 How your data is stored

Three little CSV files inside `data/`:

```
data/
├── categories.csv   ← id, name, parent, icon
├── entries.csv      ← id, date, timestamp, category, narration, debit, credit
└── budgets.csv      ← id, category, monthly_cap
```

Each entry carries a **timestamp** alongside its date, so the ledger sorts
deterministically — newest entries on top within each day, no random shuffle.
Want to start over? Delete the folder — the app re-seeds from your
spreadsheet on the next run. 🌱 (Backups happen automatically — see
[Automatic backups](#-automatic-backups-survive-the-oops) below.)

> 🤓 *For the curious:* writes are atomic (tempfile + rename), so even if
> your laptop crashes mid-save, the previous file is intact. Concurrent
> edits are safe too — there's a lock around every write. The CSV files
> themselves are **never deleted** by the app — rows come and go, the
> durable file stays.

### 📍 Point data anywhere with `.env`

Want your data on an external drive, a synced folder (Dropbox / OneDrive),
or just outside the repo? Copy **`.env.example`** to **`.env`** and uncomment
the line:

```dotenv
# Windows
EXPENSO_DATA_DIR=D:/Backups/Expenso

# macOS / Linux
EXPENSO_DATA_DIR=~/Documents/Expenso
```

The folder is created on the first run if it doesn't exist. Your data
persists across app restarts — closing and reopening Expenso reads from
the same files. `.env` is gitignored so machine-specific paths stay yours. 🔒

Same `.env` file lets you override the source workbook, host, and port —
see [`.env.example`](.env.example) for all available variables.

---

## 🛟 Automatic backups — survive the *oops*

Every time the server exits cleanly (Ctrl+C in `start.bat`, manual
`uvicorn` exit, or `python scripts/backup.py` run by hand) Expenso copies
your whole data dir into a new timestamped folder:

```
<EXPENSO_BACKUP_DIR>/
├── expenso-backup-2026-05-25_142058/
│   ├── categories.csv
│   ├── entries.csv
│   └── budgets.csv
├── expenso-backup-2026-05-25_134412/
└── ... (newest 5 kept, oldest auto-pruned)
```

Two env vars control it — defaults shown work for everyone, override only
if you want backups on a different drive / synced folder:

```dotenv
EXPENSO_BACKUP_DIR=./backups   # default; point at Mega/OneDrive for off-machine copies
EXPENSO_BACKUP_COUNT=5         # how many snapshots to retain; 0 = unlimited
```

### 🧊 The "freeze" — your safety net against catastrophe

A naïve "newest N" rule has one nasty failure mode: if you accidentally
wipe entries one session, restart 5 times, the bad state is now in every
snapshot and the original is gone. So Expenso compares your data against
the latest snapshot on each shutdown and **freezes** the rotation — no
new backup, no prune — when it sees:

- a CSV that existed in the last snapshot is **missing** in your data dir, **or**
- a CSV is now **empty** (header-only) when it had rows before, **or**
- **more than 50%** of a CSV's prior rows are gone AND the file had > 5 rows.

Pure additions, in-place edits, and small audit deletions (2–9 rows out
of hundreds) all roll backups normally. Mass deletes / wipes / file-gone
events leave your safety net untouched — older snapshots survive the
incident so you always have something to restore from. 🪂

You'll see this in the shutdown log:

```
WARNING expenso.backup :: destructive: 67% of rows removed from entries.csv — above 50% threshold
WARNING expenso.backup :: backup FROZEN — existing snapshots preserved; prune skipped
```

### ♻️ Restoring after an *oops*

1. Stop the server.
2. Open `EXPENSO_BACKUP_DIR`, pick the newest `expenso-backup-…` folder
   (or an older one if the most-recent already contains the damage).
3. Copy the CSV(s) you lost back into `EXPENSO_DATA_DIR`.
4. Start the server again — next shutdown will see "data matches latest
   snapshot" and resume normal backups.

One-liner PowerShell to restore *everything* from the latest snapshot:

```powershell
$bk = (Get-ChildItem $env:EXPENSO_BACKUP_DIR -Directory -Filter 'expenso-backup-*' |
       Sort-Object Name -Descending | Select-Object -First 1).FullName
Copy-Item "$bk\*.csv" $env:EXPENSO_DATA_DIR -Force
```

### 📸 Snapshot on demand

Don't want to restart the server but want a snapshot *now*?

```powershell
venv\Scripts\python.exe scripts\backup.py
```

Same logic, same freeze rules, same rotation.

---

## 🧪 Verified math 🔢

Every analytics number in the dashboard was **cross-checked against the raw
CSV** on a fresh seed of your spreadsheet — totals, daily sums, cumulative,
weekday breakdown, group rollup, monthly debit/credit. All deltas: **Rs 0.00**. ✅

Insight numbers too: anomaly z-scores, MoM %, concentration share, run-rate
projection, biggest transaction — all match. 💯

---

## 🛠️ Tech stack (for the curious dev)

Everything ships from one folder. No npm. No build step. Refresh-and-go.

| Layer | Choice | Why |
| --- | --- | --- |
| 🐍 Backend | FastAPI + uvicorn | Fast, type-checked, batteries-included |
| 📦 Models | Pydantic v2 | Validates the wire and on-disk shape |
| 🎨 Templates | Jinja2 | Server-rendered HTML, no SPA tax |
| ⚡ Interactivity | **HTMX 2** (CDN) | In-place updates without a framework |
| 📊 Charts | **Chart.js 4** (CDN) | The analytics dashboard |
| 🎨 Icons | **Native emoji** 🛒🍽️🚖 | Zero asset shipping, OS-rendered |
| 💅 Styles | Hand-written CSS | ~700 lines, custom properties, no Tailwind |
| 📑 Workbook | openpyxl | Reads your xlsx for the seed importer |
| 💾 Storage | Plain CSV files | Open in Excel, grep with the terminal |

---

## 🏗️ How it's built

```
app/
├── core/          ⚙️  settings (loads .env) + custom exceptions
├── domain/        📦  Pydantic models + Repository Protocols
├── repositories/  💾  CSV repos (atomic writes + thread lock)
├── services/      🧠  business logic (one job per file)
├── routers/       🌐  FastAPI controllers — thin, HTMX-aware
├── templates/     🎨  Jinja HTML
│   └── partials/  🧩  fragments returned to HTMX (ledger, add form)
└── static/        💅  CSS + vanilla JS + Chart.js / HTMX (via CDN)
```

Services depend only on the **Repository Protocols** in `app/domain/interfaces.py`,
so swapping CSV → SQLite is a single new repo class away — the rest of the
app won't notice. 🪄

---

## 🤝 The small print

- 🐍 Needs **Python 3.9+** installed (the launcher creates a venv for you)
- 📋 Source workbook: by default looks at
  `%USERPROFILE%\Desktop\Expense_Tracker_FY2026-27.xlsx`.
  Point elsewhere via `EXPENSO_SOURCE_XLSX=...`
- 🛡️ Default host is `127.0.0.1` (your laptop only — not exposed to the network).
  Override with `EXPENSO_HOST` / `EXPENSO_PORT` if you want.
- 🌑 Pure-black AMOLED palette by default; the browser's native widgets
  (date picker, scrollbars) also render dark via `color-scheme: dark`.
- ♻️ HTMX is **optional** — the app works with JS disabled too. Forms
  fall back to plain POST + 303 redirects.

Happy tracking! 🪙✨
