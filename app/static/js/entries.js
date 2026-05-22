// Entries page: Edit button -> populate shared modal -> POST to /entries/{id}/update.
(function () {
  const modal = document.getElementById('entry-edit-modal');
  const form  = document.getElementById('entry-edit-form');
  if (!modal || !form) return;

  let lastFocus = null;

  function openModal(triggerEl, data) {
    lastFocus = triggerEl;
    form.action = `/entries/${data.id}/update`;
    form.elements['date'].value      = data.date;
    form.elements['category'].value  = data.category;
    form.elements['narration'].value = data.narration || '';
    form.elements['debit'].value     = data.debit;
    form.elements['credit'].value    = data.credit;
    modal.hidden = false;
    modal.setAttribute('aria-hidden', 'false');
    document.body.classList.add('modal-open');
    // focus first field after the open transition
    setTimeout(() => form.elements['date'].focus(), 30);
  }

  function closeModal() {
    modal.hidden = true;
    modal.setAttribute('aria-hidden', 'true');
    document.body.classList.remove('modal-open');
    if (lastFocus && typeof lastFocus.focus === 'function') lastFocus.focus();
  }

  // Wire up every Edit button — one delegated listener on tbody would also work,
  // but a per-button listener keeps the data-attribute scoping obvious.
  document.querySelectorAll('[data-edit-entry]').forEach((btn) => {
    btn.addEventListener('click', () => {
      // Row used to be a <tr>; in the new grouped layout it's an <li class="row">.
      // closest('[data-entry-id]') finds whatever element carries the row data.
      const row = btn.closest('[data-entry-id]');
      if (!row) return;
      openModal(btn, {
        id:        row.dataset.entryId,
        date:      row.dataset.date,
        category:  row.dataset.category,
        narration: row.dataset.narration,
        debit:     row.dataset.debit,
        credit:    row.dataset.credit,
      });
    });
  });

  // Close handlers: backdrop, × button, Cancel button, Escape key.
  modal.querySelectorAll('[data-modal-close]').forEach((el) => {
    el.addEventListener('click', closeModal);
  });
  document.addEventListener('keydown', (e) => {
    if (!modal.hidden && e.key === 'Escape') closeModal();
  });

  // Debit/Credit mutex inside the modal too — typing in one zeros the other.
  const debit  = form.elements['debit'];
  const credit = form.elements['credit'];
  function mutex(other) {
    return (ev) => {
      const v = parseFloat(ev.target.value || '0');
      if (v > 0) other.value = '0';
    };
  }
  debit.addEventListener('input', mutex(credit));
  credit.addEventListener('input', mutex(debit));
})();
