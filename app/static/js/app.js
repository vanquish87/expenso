// Shared top-bar behavior: active nav highlight + Re-import button + tiny toast.
(function () {
  const path = window.location.pathname;
  document.querySelectorAll('.navlink').forEach((a) => {
    const href = a.getAttribute('href');
    if (href === '/' ? path === '/' : path.startsWith(href)) {
      a.classList.add('is-active');
    }
  });

  const toast = document.getElementById('toast');
  function showToast(msg, ms = 2400) {
    if (!toast) return;
    toast.textContent = msg;
    toast.hidden = false;
    clearTimeout(showToast._t);
    showToast._t = setTimeout(() => { toast.hidden = true; }, ms);
  }
  window.expensoToast = showToast;

  // Tab cards (e.g. /entries Add | Filters): click a tab to swap which
  // panel is visible. Initial active states are server-rendered, so the
  // page works even before this script runs.
  document.querySelectorAll('.tabs').forEach((tabs) => {
    const buttons = tabs.querySelectorAll('.tabs__tab');
    const panels  = tabs.querySelectorAll('.tabs__panel');
    buttons.forEach((btn) => {
      btn.addEventListener('click', () => {
        const key = btn.dataset.tab;
        buttons.forEach((b) => {
          const active = b === btn;
          b.classList.toggle('is-active', active);
          b.setAttribute('aria-selected', String(active));
        });
        panels.forEach((p) => p.classList.toggle('is-active', p.dataset.panel === key));
      });
    });
  });

  // Hamburger nav (≤1024px): toggle the drawer; close on link click or Escape.
  const menuBtn = document.getElementById('menu-btn');
  const nav = document.getElementById('topbar-nav');
  if (menuBtn && nav) {
    const close = () => {
      nav.classList.remove('is-open');
      menuBtn.setAttribute('aria-expanded', 'false');
    };
    menuBtn.addEventListener('click', (e) => {
      e.stopPropagation();  // don't let the document-click handler immediately close it
      const open = nav.classList.toggle('is-open');
      menuBtn.setAttribute('aria-expanded', String(open));
    });
    nav.addEventListener('click', (e) => {
      if (e.target.closest('.navlink')) close();
    });
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && nav.classList.contains('is-open')) close();
    });
    // Click anywhere outside the drawer to dismiss it.
    document.addEventListener('click', (e) => {
      if (!nav.classList.contains('is-open')) return;
      if (e.target.closest('#topbar-nav, #menu-btn')) return;
      close();
    });
  }

  const btn = document.getElementById('reimport-btn');
  if (btn) {
    btn.addEventListener('click', async () => {
      if (!confirm('Re-import from the source xlsx? This replaces categories and entries.')) return;
      btn.disabled = true;
      const original = btn.textContent;
      btn.textContent = '…importing';
      try {
        const r = await fetch('/api/import/excel', { method: 'POST' });
        if (!r.ok) {
          const e = await r.json().catch(() => ({}));
          throw new Error(e.detail || `HTTP ${r.status}`);
        }
        const data = await r.json();
        showToast(`Imported ${data.categories} categories · ${data.entries} entries`);
        setTimeout(() => window.location.reload(), 600);
      } catch (e) {
        showToast(`Import failed: ${e.message}`, 4000);
      } finally {
        btn.disabled = false;
        btn.textContent = original;
      }
    });
  }

  // Auto-dismiss flash banners
  document.querySelectorAll('.banner').forEach((b) => {
    setTimeout(() => { b.style.transition = 'opacity .4s'; b.style.opacity = '0'; }, 3200);
    setTimeout(() => { b.remove(); }, 3700);
  });

  // Mutual-exclusion helper on entry forms: typing in debit zeroes credit, and vice versa.
  document.querySelectorAll('form').forEach((form) => {
    const debit = form.querySelector('input[name="debit"]');
    const credit = form.querySelector('input[name="credit"]');
    if (!debit || !credit) return;
    function clear(other) {
      return (ev) => {
        const v = parseFloat(ev.target.value || '0');
        if (v > 0) other.value = '0';
      };
    }
    debit.addEventListener('input', clear(credit));
    credit.addEventListener('input', clear(debit));
  });
})();
