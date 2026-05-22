# 💸 Expenso

A friendly little expense tracker that turns your **Expense_Tracker_FY2026-27.xlsx**
into a real web app — same columns (Date · Category · Narration · Debit · Credit),
plus charts, budgets, and a dashboard that actually tells you stuff. 🪄

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
| 🏷️ **Categories** | Make groups and sub-categories — add, rename, delete |
| 📝 **Entries** | Add a spend or income, filter by date / category / text |
| 🎯 **Budgets** | Set a monthly cap per category — see how close you are |
| 📊 **Analytics** | Fancy dashboard: doughnuts, lines, bars, top spends, insights |

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
├── categories.csv   ← your groups + sub-categories
├── entries.csv      ← every Date · Category · Narration · Debit · Credit row
└── budgets.csv      ← monthly caps you've set
```

Want to back up? Copy that folder. Want to start over? Delete it — the app
re-seeds from your spreadsheet on the next run. 🌱

> 🤓 *For the curious:* writes are atomic (tempfile + rename), so even if your
> laptop crashes mid-save, the previous file is intact. Concurrent edits are
> safe too — there's a lock around every write.

---

## 🧪 Verified math 🔢

Every analytics number in the dashboard was **cross-checked against the raw
CSV** on a fresh seed of your spreadsheet — totals, daily sums, cumulative,
weekday breakdown, group rollup, monthly debit/credit. All deltas: **Rs 0.00**. ✅

Insight numbers too: anomaly z-scores, MoM %, concentration share, run-rate
projection, biggest transaction — all match. 💯

---

## 🏗️ How it's built (for the curious dev)

```
app/
├── core/          ⚙️  settings + custom exceptions
├── domain/        📦  Pydantic models + Repository Protocols
├── repositories/  💾  CSV repos (atomic writes + thread lock)
├── services/      🧠  business logic (one job per file)
├── routers/       🌐  FastAPI controllers (thin)
├── templates/     🎨  Jinja HTML
└── static/        💅  CSS + vanilla JS + Chart.js (CDN)
```

- **FastAPI + uvicorn** server 🐍
- **Pydantic v2** for models
- **Jinja2** templates with a dark UI
- **Chart.js** for the dashboard
- **CSV** for storage (swap to SQLite later by writing one new repo class — the
  rest of the app won't notice 🪄)

---

## 🤝 The small print

- 🐍 Needs **Python 3.9+** installed (the launcher creates a venv for you)
- 📋 Source workbook: by default looks at
  `%USERPROFILE%\Desktop\Expense_Tracker_FY2026-27.xlsx`.
  Point elsewhere via `EXPENSO_SOURCE_XLSX=...`
- 🛡️ Default host is `127.0.0.1` (your laptop only — not exposed to the network).
  Override with `EXPENSO_HOST` / `EXPENSO_PORT` if you want.

Happy tracking! 🪙✨
