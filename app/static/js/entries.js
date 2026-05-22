// Entries page: clicking a ledger row opens the detail modal,
// populated from the row's data-* attrs. Modal has two modes:
//   data-mode="view"  → read-only details
//   data-mode="edit"  → form (pencil button toggles to this)
// Save/Cancel return to view mode; the X button (or backdrop / Esc)
// closes the whole modal.
(function () {
  const modal = document.getElementById('entry-detail-modal');
  if (!modal) return;
  const dialog = modal.querySelector('.modal__dialog');

  const elIcon     = modal.querySelector('[data-detail-icon]');
  const elCat      = modal.querySelector('[data-detail-cat]');
  const elAmount   = modal.querySelector('[data-detail-amount]');
  const elNarrRow  = modal.querySelector('[data-detail-narr-row]');
  const elNarr     = modal.querySelector('[data-detail-narr]');
  const elDate     = modal.querySelector('[data-detail-date]');
  const editForm   = document.getElementById('entry-detail-edit-form');
  const deleteForm = document.getElementById('entry-detail-delete-form');
  const editBtn    = modal.querySelector('[data-detail-edit]');
  const cancelBtn  = modal.querySelector('[data-detail-cancel]');

  const WEEKDAYS = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];
  let lastFocus = null;

  function fmtNumber(s) {
    const n = parseInt(parseFloat(s), 10);
    if (Number.isNaN(n)) return '0';
    return n.toLocaleString();
  }

  function fmtDate(iso) {
    // iso = "YYYY-MM-DD"; add T00:00:00 so JS doesn't interpret as UTC.
    const d = new Date(iso + 'T00:00:00');
    if (Number.isNaN(d.getTime())) return iso;
    const dd = String(d.getDate()).padStart(2, '0');
    const mm = String(d.getMonth() + 1).padStart(2, '0');
    return `${WEEKDAYS[d.getDay()]}, ${dd}-${mm}-${d.getFullYear()}`;
  }

  // --- mode swap ---------------------------------------------------------
  function setMode(mode) { dialog.dataset.mode = mode; }

  // --- view / form sync --------------------------------------------------
  function paintView(d) {
    const debitN  = parseFloat(d.debit)  || 0;
    const creditN = parseFloat(d.credit) || 0;
    const isDebit = debitN > 0;
    const shown   = isDebit ? debitN : creditN;

    elIcon.textContent = d.emoji || '🏷️';
    elCat.textContent  = d.category || '';
    elAmount.textContent = '₹ ' + fmtNumber(shown);
    elAmount.classList.toggle('is-debit',  isDebit);
    elAmount.classList.toggle('is-credit', !isDebit);
    if (d.narration) {
      elNarr.textContent = d.narration;
      elNarrRow.hidden = false;
    } else {
      elNarrRow.hidden = true;
    }
    elDate.textContent = fmtDate(d.date);
  }

  function paintForm(d) {
    const isDebit = (parseFloat(d.debit) || 0) > 0;
    editForm.elements['date'].value      = d.date;
    editForm.elements['category'].value  = d.category;
    editForm.elements['narration'].value = d.narration || '';
    editForm.elements['debit'].value     = isDebit  ? d.debit  : '';
    editForm.elements['credit'].value    = !isDebit ? d.credit : '';
  }

  function dataFromForm() {
    const debit  = editForm.elements['debit'].value;
    const credit = editForm.elements['credit'].value;
    return {
      date:      editForm.elements['date'].value,
      category:  editForm.elements['category'].value,
      narration: editForm.elements['narration'].value,
      debit, credit,
      // emoji stays from previous open — the user only changed text fields;
      // category may have changed so the new emoji might differ, but we'd
      // need a server lookup to know — leave as-is until next reload.
      emoji: elIcon.textContent,
    };
  }

  // --- open / close ------------------------------------------------------
  function open(rowBtn) {
    lastFocus = rowBtn;
    const d = rowBtn.dataset;
    paintView(d);
    paintForm(d);

    // Wire both forms (delete + edit) to this entry's id
    deleteForm.action = `/entries/${d.entryId}/delete`;
    editForm.action   = `/entries/${d.entryId}/update`;
    editForm.setAttribute('hx-post', `/entries/${d.entryId}/update`);
    // Ask HTMX to re-evaluate the new hx-post.
    if (window.htmx && typeof htmx.process === 'function') htmx.process(editForm);

    setMode('view');  // always start in view mode
    modal.hidden = false;
    modal.setAttribute('aria-hidden', 'false');
    document.body.classList.add('modal-open');
  }

  function close() {
    modal.hidden = true;
    modal.setAttribute('aria-hidden', 'true');
    document.body.classList.remove('modal-open');
    setMode('view');
    if (lastFocus && typeof lastFocus.focus === 'function') lastFocus.focus();
  }

  // --- bindings ----------------------------------------------------------
  // Row click → open modal (body-delegated so HTMX swaps don't unbind).
  document.body.addEventListener('click', (e) => {
    const row = e.target.closest('.row__link');
    if (!row) return;
    open(row);
  });

  // Pencil → switch to edit mode.
  if (editBtn) {
    editBtn.addEventListener('click', () => setMode('edit'));
  }

  // Cancel → restore form from current view (so half-edited values are
  // dropped), then swap back to view.
  if (cancelBtn) {
    cancelBtn.addEventListener('click', () => {
      // Re-read from current view (treated as the canonical state).
      paintForm({
        date:      _isoFromHuman(elDate.textContent),
        category:  elCat.textContent,
        narration: elNarrRow.hidden ? '' : elNarr.textContent,
        debit:     elAmount.classList.contains('is-debit')  ? _numFromAmount() : '',
        credit:    elAmount.classList.contains('is-credit') ? _numFromAmount() : '',
      });
      setMode('view');
    });
  }

  // After a successful HTMX save: read the just-submitted form values
  // into the view panel and swap back. The ledger fragment that the
  // server returned has already replaced #ledger-root.
  editForm.addEventListener('htmx:afterRequest', (e) => {
    if (!e.detail || !e.detail.successful) {
      // Surface a toast on validation failure; stay in edit mode.
      const msg = (e.detail && e.detail.xhr && e.detail.xhr.responseText) || 'Save failed';
      if (typeof window.expensoToast === 'function') window.expensoToast(msg, 4000);
      return;
    }
    paintView(dataFromForm());
    setMode('view');
  });

  // X / backdrop / Cancel-via-data-modal-close / Escape all close.
  modal.querySelectorAll('[data-modal-close]').forEach((el) => {
    el.addEventListener('click', close);
  });
  document.addEventListener('keydown', (e) => {
    if (!modal.hidden && e.key === 'Escape') close();
  });

  // Debit / Credit mutex inside the edit form — typing one zeros the other.
  const debit  = editForm.elements['debit'];
  const credit = editForm.elements['credit'];
  function mutex(other) {
    return (ev) => {
      const v = parseFloat(ev.target.value || '0');
      if (v > 0) other.value = '0';
    };
  }
  debit.addEventListener('input', mutex(credit));
  credit.addEventListener('input', mutex(debit));

  // --- helpers for Cancel restore -------------------------------------
  function _numFromAmount() {
    // "₹ 1,234" → "1234"
    return (elAmount.textContent || '').replace(/[^0-9]/g, '');
  }
  function _isoFromHuman(s) {
    // "Thursday, 22-05-2026" → "2026-05-22"
    const m = (s || '').match(/(\d{2})-(\d{2})-(\d{4})/);
    return m ? `${m[3]}-${m[2]}-${m[1]}` : s;
  }
})();
