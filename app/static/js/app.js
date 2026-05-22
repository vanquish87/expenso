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

  // Hamburger nav (≤1024px): toggle the drawer; close on link click or Escape.
  const menuBtn = document.getElementById('menu-btn');
  const nav = document.getElementById('topbar-nav');
  if (menuBtn && nav) {
    const close = () => {
      nav.classList.remove('is-open');
      menuBtn.setAttribute('aria-expanded', 'false');
    };
    menuBtn.addEventListener('click', () => {
      const open = nav.classList.toggle('is-open');
      menuBtn.setAttribute('aria-expanded', String(open));
    });
    nav.addEventListener('click', (e) => {
      if (e.target.closest('.navlink')) close();
    });
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && nav.classList.contains('is-open')) close();
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
