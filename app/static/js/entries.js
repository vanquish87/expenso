// Entries page: clicking a ledger row opens the detail modal,
// populated from the row's data-* attrs. The modal owns the Edit form
// + Delete button (regular POSTs that redirect back to /entries).
(function () {
  const modal = document.getElementById('entry-detail-modal');
  if (!modal) return;

  const elIcon     = modal.querySelector('[data-detail-icon]');
  const elCat      = modal.querySelector('[data-detail-cat]');
  const elAmount   = modal.querySelector('[data-detail-amount]');
  const elNarrRow  = modal.querySelector('[data-detail-narr-row]');
  const elNarr     = modal.querySelector('[data-detail-narr]');
  const elDate     = modal.querySelector('[data-detail-date]');
  const editForm   = document.getElementById('entry-detail-edit-form');
  const deleteForm = document.getElementById('entry-detail-delete-form');
  const editPanel  = document.getElementById('edit-section');

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

  function open(rowBtn) {
    lastFocus = rowBtn;
    const d = rowBtn.dataset;
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

    // Wire form actions to this entry's id
    deleteForm.action = `/entries/${d.entryId}/delete`;
    editForm.action   = `/entries/${d.entryId}/update`;
    editForm.elements['date'].value      = d.date;
    editForm.elements['category'].value  = d.category;
    editForm.elements['narration'].value = d.narration || '';
    editForm.elements['debit'].value     = isDebit  ? d.debit  : '';
    editForm.elements['credit'].value    = !isDebit ? d.credit : '';

    // Edit panel starts collapsed every time
    if (editPanel) editPanel.open = false;

    modal.hidden = false;
    modal.setAttribute('aria-hidden', 'false');
    document.body.classList.add('modal-open');
  }

  function close() {
    modal.hidden = true;
    modal.setAttribute('aria-hidden', 'true');
    document.body.classList.remove('modal-open');
    if (lastFocus && typeof lastFocus.focus === 'function') lastFocus.focus();
  }

  // Event delegation on body — survives HTMX-driven swaps of #ledger-root.
  document.body.addEventListener('click', (e) => {
    const row = e.target.closest('.row__link');
    if (!row) return;
    open(row);
  });

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
})();
