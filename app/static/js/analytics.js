// Analytics drill-down: Groups → Sub-categories → Months → Transactions.
//
// Level 1 (groups) lives on the page; clicking a group opens the level-2
// modal, which can open level 3 on top, which can open level 4 on top.
// Each modal has its own backdrop and `data-drill-level`; we use that to
// manage a stack so the back-button / Esc / backdrop closes one level
// while the X button (data-modal-close-all) tears the whole stack down.
(function () {
  const fmt = (v) => 'Rs ' + (Math.round(Number(v) || 0)).toLocaleString();
  const palette = [
    '#6366f1', '#22d3ee', '#10b981', '#f59e0b', '#ef4444',
    '#a78bfa', '#f472b6', '#34d399', '#fbbf24', '#60a5fa',
    '#fb7185', '#c084fc', '#facc15', '#4ade80', '#38bdf8',
  ];

  // --- shared state --------------------------------------------------------
  const state = {
    dateFrom: '',
    dateTo: '',
    // Number of calendar months the current view covers. Set from the date
    // range when supplied; otherwise discovered from the data span at L1
    // load time so L2/L3 can divide totals by the same denominator.
    monthsInRange: 1,
    // remembered for the chain so the next level can scope itself
    group: '',
    category: '',
    yearMonth: '',
  };

  // --- chart helpers -------------------------------------------------------
  const charts = {};
  function destroy(id) { if (charts[id]) { charts[id].destroy(); delete charts[id]; } }

  function doughnut(id, items) {
    destroy(id);
    const ctx = document.getElementById(id);
    if (!ctx) return;
    if (!items.length) {
      const c = ctx.getContext('2d');
      c.clearRect(0, 0, ctx.width, ctx.height);
      return;
    }
    charts[id] = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: items.map((d) => (d.icon ? d.icon + ' ' : '') + d.label),
        datasets: [{
          data: items.map((d) => d.value),
          backgroundColor: items.map((_, i) => palette[i % palette.length]),
          borderWidth: 0,
        }],
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

  function bar(id, items, color = '#6366f1') {
    destroy(id);
    const ctx = document.getElementById(id);
    if (!ctx) return;
    if (!items.length) return;
    charts[id] = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: items.map((d) => d.label),
        datasets: [{ data: items.map((d) => d.value), backgroundColor: color, borderRadius: 6, maxBarThickness: 36 }],
      },
      options: {
        responsive: true,
        plugins: {
          legend: { display: false },
          tooltip: { callbacks: { label: (c) => fmt(c.parsed.y) } },
        },
        scales: {
          x: { ticks: { color: '#93a3c5', maxRotation: 0 }, grid: { color: 'rgba(255,255,255,0.05)' } },
          y: { ticks: { color: '#93a3c5', callback: (v) => fmt(v) }, grid: { color: 'rgba(255,255,255,0.05)' } },
        },
      },
    });
  }

  // --- list builders -------------------------------------------------------
  function listRow({ icon, label, amount, sub, level }) {
    const li = document.createElement('li');
    li.className = 'drill__row';
    li.setAttribute('role', 'button');
    li.tabIndex = 0;
    li.dataset.drillLevel = String(level);
    li.dataset.label = label;
    li.innerHTML = `
      <div class="drill__row-icon">${icon || '🏷️'}</div>
      <div class="drill__row-body">
        <div class="drill__row-label">${escapeHtml(label)}</div>
        ${sub ? `<div class="drill__row-sub">${escapeHtml(sub)}</div>` : ''}
      </div>
      <div class="drill__row-amount is-debit">${fmt(amount)}</div>
      <div class="drill__row-caret" aria-hidden="true">›</div>
    `;
    return li;
  }

  function renderL1List(ul, items) {
    ul.innerHTML = '';
    if (!items.length) {
      ul.innerHTML = '<li class="muted">No spend in this range.</li>';
      return;
    }
    items.forEach((g) => ul.appendChild(listRow({
      icon: g.icon, label: g.label, amount: g.value, level: 1,
    })));
  }

  function renderSubList(ul, items) {
    ul.innerHTML = '';
    if (!items.length) {
      ul.innerHTML = '<li class="muted">No sub-categories here.</li>';
      return;
    }
    items.forEach((s) => ul.appendChild(listRow({
      icon: s.icon, label: s.label, amount: s.value, level: 2,
    })));
  }

  function renderMonthList(ul, items) {
    ul.innerHTML = '';
    if (!items.length) {
      ul.innerHTML = '<li class="muted">No months with spend.</li>';
      return;
    }
    items.forEach((m) => ul.appendChild(listRow({
      icon: '📅', label: m.label, sub: prettyMonth(m.label),
      amount: m.value, level: 3,
    })));
  }

  function renderTxList(root, txs) {
    root.innerHTML = '';
    if (!txs.length) {
      root.innerHTML = '<p class="empty">No transactions in this month.</p>';
      return;
    }
    // Group by date (newest first since payload is already sorted desc).
    const byDate = new Map();
    txs.forEach((t) => {
      if (!byDate.has(t.date)) byDate.set(t.date, []);
      byDate.get(t.date).push(t);
    });
    byDate.forEach((rows, d) => {
      const dayNet = rows.reduce((s, r) => s + (r.credit - r.debit), 0);
      const day = document.createElement('article');
      day.className = 'day';
      const dt = new Date(d + 'T00:00:00');
      day.innerHTML = `
        <header class="day__head">
          <div class="day__num">${String(dt.getDate()).padStart(2, '0')}</div>
          <div class="day__meta">
            <div class="day__weekday">${rows[0].weekday}</div>
            <div class="day__month">${rows[0].month_label}</div>
          </div>
          <div class="day__total${dayNet > 0 ? ' is-credit' : ''}">${fmt(Math.abs(dayNet))}</div>
        </header>
        <ul class="day__entries"></ul>
      `;
      const ul = day.querySelector('.day__entries');
      rows.forEach((r) => {
        const li = document.createElement('li');
        li.className = 'row';
        const amount = r.debit > 0 ? r.debit : r.credit;
        const cls = r.debit > 0 ? 'is-debit' : 'is-credit';
        // Same shape as /entries rows: data-* attrs carry everything the
        // L5 modal needs, so opening it is zero-fetch.
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'row__link drill__tx-row';
        btn.dataset.entryId  = r.id;
        btn.dataset.date     = r.date;
        btn.dataset.category = r.category;
        btn.dataset.emoji    = _currentSubIcon;
        btn.dataset.narration = r.narration || '';
        btn.dataset.debit    = r.debit;
        btn.dataset.credit   = r.credit;
        btn.innerHTML = `
          <div class="row__icon">${_currentSubIcon}</div>
          <div class="row__body">
            <div class="row__cat">${escapeHtml(r.category)}</div>
            ${r.narration ? `<div class="row__narr">${escapeHtml(r.narration)}</div>` : ''}
          </div>
          <div class="row__amount ${cls}">₹ ${Math.round(amount).toLocaleString()}</div>
        `;
        li.appendChild(btn);
      });
      root.appendChild(day);
    });
  }

  // Icon used for L4 transaction rows — all rows in a level-4 modal share
  // one category, so we reuse the icon we already had at L3 open time.
  let _currentSubIcon = '🏷️';

  function prettyMonth(ym) {
    // "2026-04" -> "April 2026"
    const m = /^(\d{4})-(\d{2})$/.exec(ym);
    if (!m) return ym;
    const names = ['January','February','March','April','May','June','July','August','September','October','November','December'];
    return `${names[parseInt(m[2], 10) - 1]} ${m[1]}`;
  }

  function escapeHtml(s) {
    return String(s ?? '').replace(/[&<>"']/g, (m) => ({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' }[m]));
  }

  // --- monthly average -----------------------------------------------------
  // The denominator for "monthly average" everywhere. When a date range is
  // active we use it; otherwise we use the actual data span (number of
  // months with at least one entry, from /summary's `monthly` array).
  // Stored on state so L2/L3 modals can reuse it.
  function monthsBetween(a, b) {
    const da = new Date(a + 'T00:00:00');
    const db = new Date(b + 'T00:00:00');
    return Math.max(1, (db.getFullYear() - da.getFullYear()) * 12 + (db.getMonth() - da.getMonth()) + 1);
  }

  // --- API plumbing --------------------------------------------------------
  function rangeQS() {
    const p = new URLSearchParams();
    if (state.dateFrom) p.set('date_from', state.dateFrom);
    if (state.dateTo)   p.set('date_to',   state.dateTo);
    const s = p.toString();
    return s ? '?' + s : '';
  }

  async function getJson(url) {
    const r = await fetch(url);
    if (!r.ok) throw new Error(`${url} -> ${r.status}`);
    return r.json();
  }

  // --- modal stack ---------------------------------------------------------
  // Only one drill modal is visible at a time. We still keep a stack so
  // the back arrow / Esc / backdrop can re-show the previous level. X
  // (data-modal-close-all) tears everything down at once.
  const stack = [];

  function pushModal(modalId) {
    const m = document.getElementById(modalId);
    if (!m) return;
    // Hide whatever is currently on top before showing the new one.
    if (stack.length) {
      const prev = stack[stack.length - 1];
      prev.hidden = true;
      prev.setAttribute('aria-hidden', 'true');
    }
    m.hidden = false;
    m.setAttribute('aria-hidden', 'false');
    stack.push(m);
    document.body.classList.add('modal-open');
  }

  function popTop() {
    const top = stack.pop();
    if (!top) return;
    top.hidden = true;
    top.setAttribute('aria-hidden', 'true');
    if (stack.length) {
      // Re-show the previous level — its DOM is still populated so we
      // don't need to re-fetch (callers that need a refresh after edit /
      // delete do it explicitly before popping).
      const prev = stack[stack.length - 1];
      prev.hidden = false;
      prev.setAttribute('aria-hidden', 'false');
    } else {
      document.body.classList.remove('modal-open');
    }
  }

  function popAll() {
    while (stack.length) {
      const top = stack.pop();
      top.hidden = true;
      top.setAttribute('aria-hidden', 'true');
    }
    document.body.classList.remove('modal-open');
  }

  // --- Level 1: groups on the page -----------------------------------------
  async function loadL1(form) {
    if (form) {
      const fd = new FormData(form);
      state.dateFrom = fd.get('date_from') || '';
      state.dateTo   = fd.get('date_to')   || '';
    }
    const s = await getJson('/api/analytics/summary' + rangeQS());
    const groups = s.spend_by_group || [];
    const total = groups.reduce((acc, g) => acc + g.value, 0);

    // Anchor the denominator now — L2/L3 modals reuse it.
    state.monthsInRange = (state.dateFrom && state.dateTo)
      ? monthsBetween(state.dateFrom, state.dateTo)
      : Math.max(1, (s.monthly || []).length);

    document.querySelector('[data-l1-total]').textContent = fmt(total);
    document.querySelector('[data-l1-monthly]').textContent = fmt(total / state.monthsInRange);
    document.querySelector('[data-l1-count]').textContent = groups.length;

    doughnut('chart-l1', groups);
    renderL1List(document.getElementById('drill-l1-list'), groups);
  }

  // --- Level 2: sub-categories under one group -----------------------------
  async function openSub(group) {
    state.group = group;
    const data = await getJson(`/api/analytics/group/${encodeURIComponent(group)}/subs${rangeQS()}`);
    const items = data.items || [];
    const total = data.total || 0;

    // Use the icon of the first item (or fallback) for the modal title icon.
    const groupIcon = pickGroupIcon(group, items);
    document.querySelector('[data-sub-icon]').textContent = groupIcon;
    document.querySelector('[data-sub-title]').textContent = group;
    document.querySelector('[data-sub-total]').textContent   = fmt(total);
    document.querySelector('[data-sub-monthly]').textContent = fmt(total / state.monthsInRange);

    doughnut('chart-sub', items);
    renderSubList(document.getElementById('drill-sub-list'), items);
    pushModal('modal-sub');
  }

  // The group-level icon isn't in the subs payload directly — we already
  // have it from the L1 list. Fall back to the row that was clicked.
  let _lastGroupIcon = '🏷️';
  function pickGroupIcon(group, items) {
    return _lastGroupIcon;
  }

  // --- Level 3: months for one sub-category --------------------------------
  async function openMonth(category, icon) {
    state.category = category;
    _currentSubIcon = icon || '🏷️';
    const data = await getJson(`/api/analytics/category/${encodeURIComponent(category)}/months${rangeQS()}`);
    const items = data.items || [];
    const total = data.total || 0;

    document.querySelector('[data-month-icon]').textContent = icon || '🏷️';
    document.querySelector('[data-month-title]').textContent = category;
    document.querySelector('[data-month-total]').textContent   = fmt(total);
    document.querySelector('[data-month-monthly]').textContent = fmt(total / state.monthsInRange);

    bar('chart-month', items, '#ef4444');
    renderMonthList(document.getElementById('drill-month-list'), items);
    pushModal('modal-month');
  }

  // --- Level 4: transactions for (sub-category, month) ---------------------
  async function openTx(category, yearMonth) {
    state.yearMonth = yearMonth;
    await refreshTx();
    pushModal('modal-tx');
  }

  // Pull + paint L4 contents without touching the modal stack. Called on
  // open AND after any L5 edit/delete so the list reflects reality before
  // we peel back to it.
  async function refreshTx() {
    const category = state.category;
    const yearMonth = state.yearMonth;
    const data = await getJson(
      `/api/analytics/category/${encodeURIComponent(category)}/month/${yearMonth}/transactions${rangeQS()}`
    );
    const items = data.items || [];

    document.querySelector('[data-tx-title]').textContent =
      `${category} · ${prettyMonth(yearMonth)}`;
    document.querySelector('[data-tx-count]').textContent =
      `${items.length} result${items.length === 1 ? '' : 's'}`;
    document.querySelector('[data-tx-credit]').textContent = '₹ ' + Math.round(data.total_credit).toLocaleString();
    document.querySelector('[data-tx-debit]').textContent  = '₹ ' + Math.round(data.total_debit).toLocaleString();
    const net = data.net;
    const netEl = document.querySelector('[data-tx-net]');
    netEl.textContent = (net >= 0 ? '+' : '−') + '₹ ' + Math.round(Math.abs(net)).toLocaleString();
    netEl.className = net >= 0 ? 'is-credit' : 'is-debit';

    renderTxList(document.getElementById('drill-tx-list'), items);
  }

  // --- Level 5: one transaction view / edit / delete -----------------------
  const entryModal = () => document.getElementById('modal-entry');
  const entryDialog = () => entryModal().querySelector('.modal__dialog');
  let _currentEntryId = null;

  function setEntryMode(mode) { entryDialog().dataset.mode = mode; }

  function paintEntryView(d) {
    const debit  = parseFloat(d.debit)  || 0;
    const credit = parseFloat(d.credit) || 0;
    const isDebit = debit > 0;
    const shown   = isDebit ? debit : credit;

    entryModal().querySelector('[data-entry-icon]').textContent = d.emoji || '🏷️';
    entryModal().querySelector('[data-entry-cat]').textContent  = d.category || '';
    const amt = entryModal().querySelector('[data-entry-amount]');
    amt.textContent = '₹ ' + Math.round(shown).toLocaleString();
    amt.classList.toggle('is-debit',  isDebit);
    amt.classList.toggle('is-credit', !isDebit);

    const narrRow = entryModal().querySelector('[data-entry-narr-row]');
    const narr    = entryModal().querySelector('[data-entry-narr]');
    if (d.narration) { narr.textContent = d.narration; narrRow.hidden = false; }
    else { narrRow.hidden = true; }

    entryModal().querySelector('[data-entry-date]').textContent = fmtHumanDate(d.date);
  }

  function paintEntryForm(d) {
    const form = document.getElementById('drill-entry-edit-form');
    const isDebit = (parseFloat(d.debit) || 0) > 0;
    form.elements['date'].value      = d.date;
    form.elements['category'].value  = d.category;
    form.elements['narration'].value = d.narration || '';
    form.elements['debit'].value     = isDebit  ? d.debit  : '';
    form.elements['credit'].value    = !isDebit ? d.credit : '';
  }

  function fmtHumanDate(iso) {
    const d = new Date(iso + 'T00:00:00');
    if (Number.isNaN(d.getTime())) return iso;
    const wkdays = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];
    const dd = String(d.getDate()).padStart(2, '0');
    const mm = String(d.getMonth() + 1).padStart(2, '0');
    return `${wkdays[d.getDay()]}, ${dd}-${mm}-${d.getFullYear()}`;
  }

  function openEntry(rowBtn) {
    _currentEntryId = rowBtn.dataset.entryId;
    paintEntryView(rowBtn.dataset);
    paintEntryForm(rowBtn.dataset);
    setEntryMode('view');
    pushModal('modal-entry');
  }

  async function saveEntry(ev) {
    ev.preventDefault();
    if (!_currentEntryId) return;
    const form = document.getElementById('drill-entry-edit-form');
    const fd = new FormData(form);
    try {
      const r = await fetch(`/entries/${_currentEntryId}/update`, {
        method: 'POST',
        body: fd,
        // Use the HX header so the entries router gives us a plain-text
        // error body on validation failure (vs. a full HTML redirect we'd
        // then have to parse).
        headers: { 'HX-Request': 'true' },
      });
      if (!r.ok) throw new Error((await r.text()) || 'Save failed');
    } catch (e) {
      alert('Save failed: ' + (e.message || e));
      return;
    }
    await refreshTx();   // L4 list reflects the edit
    popTop();            // close L5; L4 (now refreshed) shows
    _currentEntryId = null;
  }

  async function deleteEntry() {
    if (!_currentEntryId) return;
    if (!confirm('Delete this entry?')) return;
    try {
      const r = await fetch(`/entries/${_currentEntryId}/delete`, {
        method: 'POST',
        headers: { 'HX-Request': 'true' },
      });
      if (!r.ok) throw new Error('Delete failed');
    } catch (e) {
      alert(e.message || String(e));
      return;
    }
    await refreshTx();
    popTop();
    _currentEntryId = null;
  }

  // --- click delegation: row clicks open the next level --------------------
  document.addEventListener('click', (e) => {
    // L1 / L2 / L3 drill rows
    const row = e.target.closest('.drill__row');
    if (row) {
      const lvl = parseInt(row.dataset.drillLevel, 10);
      const label = row.dataset.label;
      if (lvl === 1) {
        const ic = row.querySelector('.drill__row-icon');
        _lastGroupIcon = ic ? ic.textContent : '🏷️';
        openSub(label);
      } else if (lvl === 2) {
        const ic = row.querySelector('.drill__row-icon');
        openMonth(label, ic ? ic.textContent : '🏷️');
      } else if (lvl === 3) {
        openTx(state.category, label);
      }
      return;
    }
    // L4 transaction row -> open L5
    const txRow = e.target.closest('.drill__tx-row');
    if (txRow) { openEntry(txRow); return; }

    // L5 buttons
    if (e.target.closest('[data-entry-edit]'))   { setEntryMode('edit'); return; }
    if (e.target.closest('[data-entry-cancel]')) {
      // Re-paint form from the current dataset on the row that opened it,
      // so half-typed values are dropped. Easiest: just toggle modes.
      setEntryMode('view');
      return;
    }
    if (e.target.closest('[data-entry-delete]')) { deleteEntry(); return; }
  });

  // L5 edit form submission
  document.addEventListener('submit', (e) => {
    if (e.target.id === 'drill-entry-edit-form') saveEntry(e);
  });

  // --- modal close wiring (back / Esc / X) ---------------------------------
  document.addEventListener('click', (e) => {
    if (e.target.closest('[data-modal-close-all]')) { popAll(); return; }
    if (e.target.closest('[data-modal-close]'))     { popTop(); return; }
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && stack.length) popTop();
  });

  // --- init ----------------------------------------------------------------
  function init() {
    const form = document.getElementById('range-form');
    if (form) form.addEventListener('submit', (ev) => { ev.preventDefault(); loadL1(form).catch(reportErr); });
    loadL1(form).catch(reportErr);
  }

  // Surface any load failure in the UI (and the console) so the page never
  // silently renders empty cards — easier to debug than "nothing happening".
  function reportErr(e) {
    console.error('[analytics] failed:', e);
    const ul = document.getElementById('drill-l1-list');
    if (ul) ul.innerHTML = `<li class="muted">Load failed: ${escapeHtml(String(e && e.message || e))}. Check DevTools console.</li>`;
  }

  if (window.Chart) init();
  else window.addEventListener('load', init);
})();
