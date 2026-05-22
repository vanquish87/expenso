// Analytics dashboard: pull /api/analytics/summary + /insights, render Chart.js charts.
(function () {
  const fmt = (v) => 'Rs ' + (Number(v) || 0).toLocaleString(undefined, { maximumFractionDigits: 0 });
  const palette = ['#6366f1', '#22d3ee', '#10b981', '#f59e0b', '#ef4444', '#a78bfa', '#f472b6', '#34d399', '#fbbf24', '#60a5fa', '#fb7185', '#c084fc'];

  const charts = {};
  function destroy(id) {
    if (charts[id]) { charts[id].destroy(); delete charts[id]; }
  }

  function setKpis(k) {
    const map = {
      total_debit: fmt(k.total_debit),
      total_credit: fmt(k.total_credit),
      net: fmt(k.net),
      avg_daily_debit: fmt(k.avg_daily_debit),
      n_entries: k.n_entries,
      n_days: k.n_days,
    };
    document.querySelectorAll('[data-kpi]').forEach((el) => {
      const key = el.getAttribute('data-kpi');
      if (key in map) el.textContent = map[key];
    });
  }

  function doughnut(id, items) {
    destroy(id);
    const ctx = document.getElementById(id);
    if (!ctx) return;
    charts[id] = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: items.map((d) => d.label),
        datasets: [{ data: items.map((d) => d.value), backgroundColor: items.map((_, i) => palette[i % palette.length]), borderWidth: 0 }],
      },
      options: {
        responsive: true,
        plugins: {
          legend: { position: 'right', labels: { color: '#cbd5e1', boxWidth: 12, font: { size: 11 } } },
          tooltip: { callbacks: { label: (c) => `${c.label}: ${fmt(c.parsed)}` } },
        },
        cutout: '60%',
      },
    });
  }

  function bar(id, items, color = '#6366f1', horizontal = false) {
    destroy(id);
    const ctx = document.getElementById(id);
    if (!ctx) return;
    charts[id] = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: items.map((d) => d.label),
        datasets: [{ data: items.map((d) => d.value), backgroundColor: color, borderRadius: 6, maxBarThickness: 28 }],
      },
      options: {
        indexAxis: horizontal ? 'y' : 'x',
        responsive: true,
        plugins: {
          legend: { display: false },
          tooltip: { callbacks: { label: (c) => fmt(c.parsed[horizontal ? 'x' : 'y']) } },
        },
        scales: gridScales(),
      },
    });
  }

  function line(id, items, color = '#22d3ee', filled = false) {
    destroy(id);
    const ctx = document.getElementById(id);
    if (!ctx) return;
    charts[id] = new Chart(ctx, {
      type: 'line',
      data: {
        labels: items.map((d) => d.label),
        datasets: [{ data: items.map((d) => d.value), borderColor: color, backgroundColor: color + '33', fill: filled, tension: 0.25, pointRadius: items.length > 30 ? 0 : 2 }],
      },
      options: {
        responsive: true,
        plugins: {
          legend: { display: false },
          tooltip: { callbacks: { label: (c) => fmt(c.parsed.y) } },
        },
        scales: gridScales(),
      },
    });
  }

  function monthly(id, items) {
    destroy(id);
    const ctx = document.getElementById(id);
    if (!ctx) return;
    charts[id] = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: items.map((m) => m.label),
        datasets: [
          { label: 'Debit', data: items.map((m) => m.debit), backgroundColor: '#ef4444', borderRadius: 6 },
          { label: 'Credit', data: items.map((m) => m.credit), backgroundColor: '#10b981', borderRadius: 6 },
        ],
      },
      options: {
        responsive: true,
        plugins: { legend: { position: 'top', labels: { color: '#cbd5e1' } } },
        scales: gridScales(),
      },
    });
  }

  function gridScales() {
    return {
      x: { ticks: { color: '#93a3c5', maxRotation: 0, autoSkip: true, maxTicksLimit: 12 }, grid: { color: 'rgba(255,255,255,0.05)' } },
      y: { ticks: { color: '#93a3c5', callback: (v) => fmt(v) }, grid: { color: 'rgba(255,255,255,0.05)' } },
    };
  }

  function renderTopTx(rows) {
    const tbody = document.querySelector('#top-tx tbody');
    if (!tbody) return;
    tbody.innerHTML = '';
    if (!rows.length) {
      tbody.innerHTML = `<tr><td colspan="4" class="muted">No transactions in range.</td></tr>`;
      return;
    }
    rows.forEach((r) => {
      const tr = document.createElement('tr');
      tr.innerHTML = `<td>${r.date}</td><td><span class="chip">${r.category}</span></td><td>${escapeHtml(r.narration || '—')}</td><td class="num num--debit">${fmt(r.amount)}</td>`;
      tbody.appendChild(tr);
    });
  }

  function renderInsights(items) {
    const ul = document.getElementById('insights-list');
    if (!ul) return;
    ul.innerHTML = '';
    if (!items || !items.length) {
      ul.innerHTML = `<li class="muted">No insights yet.</li>`;
      return;
    }
    items.forEach((ins) => {
      const li = document.createElement('li');
      li.className = `insight insight--${ins.kind}`;
      li.innerHTML = `<div class="insight__title">${escapeHtml(ins.title)}</div><div class="insight__detail">${escapeHtml(ins.detail)}</div>`;
      ul.appendChild(li);
    });
  }

  function escapeHtml(s) {
    return String(s ?? '').replace(/[&<>"']/g, (m) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[m]));
  }

  async function load(form) {
    const params = new URLSearchParams();
    if (form) {
      const fd = new FormData(form);
      for (const [k, v] of fd.entries()) if (v) params.set(k, v);
    }
    const [s, i] = await Promise.all([
      fetch('/api/analytics/summary?' + params.toString()).then((r) => r.json()),
      fetch('/api/analytics/insights').then((r) => r.json()),
    ]);
    setKpis(s.kpis);
    doughnut('chart-groups', s.spend_by_group);
    bar('chart-subs', s.top_subcategories, '#22d3ee', true);
    line('chart-daily', s.daily, '#6366f1', false);
    line('chart-cum', s.cumulative, '#10b981', true);
    bar('chart-weekday', s.weekday, '#f59e0b', false);
    monthly('chart-monthly', s.monthly);
    renderTopTx(s.top_transactions);
    renderInsights(i.insights);
  }

  function init() {
    const form = document.getElementById('range-form');
    if (form) form.addEventListener('submit', (ev) => { ev.preventDefault(); load(form); });
    load(form);
  }

  if (window.Chart) init();
  else window.addEventListener('load', init);
})();
