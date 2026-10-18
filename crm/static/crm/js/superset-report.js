/* Each live chart and its commentary share one CRM card. */
(() => {
  const states = new Map();
  let sessionData = null;
  let fetchedAt = 0;
  let pendingSession = null;
  let observer = null;
  const cards = () => [...document.querySelectorAll('.live-chart-card')];
  const status = () => document.getElementById('supersetEmbedStatus');

  async function session() {
    if (sessionData && performance.now() - fetchedAt < 240000) return sessionData;
    if (!pendingSession) {
      pendingSession = (async () => {
        const response = await fetch(document.getElementById('tab-content-superset-live').dataset.sessionUrl, {
          credentials: 'same-origin', cache: 'no-store', headers: {Accept: 'application/json'},
          signal: AbortSignal.timeout(25000),
        });
        if (!response.ok || response.redirected) throw new Error('session unavailable');
        sessionData = await response.json();
        fetchedAt = performance.now();
        return sessionData;
      })().finally(() => { pendingSession = null; });
    }
    return pendingSession;
  }

  function within(promise, milliseconds) {
    let timeout;
    return Promise.race([promise, new Promise((_, reject) => {
      timeout = setTimeout(() => reject(new Error('embed timeout')), milliseconds);
    })]).finally(() => clearTimeout(timeout));
  }

  function updateStatus() {
    const all = [...states.values()];
    const live = all.filter(state => state.live).length;
    const fallback = all.filter(state => state.fallback).length;
    status().textContent = fallback
      ? `${live} biểu đồ Superset đã kết nối; ${fallback} biểu đồ đang dùng dữ liệu CRM thay thế. Phân tích nằm ngay dưới từng biểu đồ.`
      : `Đã kết nối ${live} biểu đồ Superset. Các biểu đồ còn lại tải khi bạn cuộn đến.`;
  }

  async function loadCard(card) {
    const key = card.dataset.chartKey;
    if (states.has(key)) return;
    const state = {live: false, fallback: false, dashboard: null, abandoned: false};
    states.set(key, state);
    const mount = card.querySelector('.superset-chart-mount');
    const attempt = document.createElement('div');
    attempt.style.height = '100%';
    mount.replaceChildren(attempt);
    mount.hidden = false;
    card.querySelector('.local-chart-fallback').hidden = true;
    try {
      const initial = await session();
      if (state.abandoned) return;
      const widget = initial.widgets.find(item => item.key === key);
      if (!widget) throw new Error('widget not configured');
      const pending = window.supersetEmbeddedSdk.embedDashboard({
        id: widget.id, supersetDomain: initial.domain, mountPoint: attempt,
        iframeTitle: card.querySelector('h3').textContent + ' — Superset', referrerPolicy: 'strict-origin',
        dashboardUiConfig: {hideTitle: true, filters: {visible: false}},
        fetchGuestToken: async () => (await session()).token,
      });
      pending.then(instance => { if (state.abandoned) instance.unmount(); }, () => {});
      state.dashboard = await within(pending, 30000);
      await within(state.dashboard.getScrollSize(), 20000);
      if (state.abandoned) return;
      state.live = true;
      card.querySelector('[data-chart-source]').textContent = 'Superset trực tiếp';
    } catch (_) {
      if (state.abandoned) return;
      state.abandoned = true;
      state.dashboard?.unmount();
      mount.replaceChildren();
      mount.hidden = true;
      card.querySelector('.local-chart-fallback').hidden = false;
      window.resizeLocalReportChart?.(card);
      state.fallback = true;
      card.querySelector('[data-chart-source]').textContent = 'Dữ liệu CRM (Superset gián đoạn)';
    }
    updateStatus();
  }

  function reset() {
    observer?.disconnect();
    for (const state of states.values()) {
      state.abandoned = true;
      state.dashboard?.unmount();
    }
    states.clear();
  }

  window.loadSupersetReport = (force = false) => {
    if (observer && !force) {
      cards().filter(card => card.querySelector('.local-chart-fallback').hidden === false).forEach(card => window.resizeLocalReportChart?.(card));
      return;
    }
    reset();
    if (force) { sessionData = null; fetchedAt = 0; }
    observer = new IntersectionObserver(entries => {
      entries.filter(entry => entry.isIntersecting).forEach(entry => {
        observer.unobserve(entry.target);
        loadCard(entry.target);
      });
    }, {rootMargin: '300px'});
    cards().forEach(card => observer.observe(card));
  };
  document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('supersetEmbedRetry')?.addEventListener('click', () => window.location.reload());
  });
  window.addEventListener('resize', () => cards().filter(card => !card.querySelector('.local-chart-fallback').hidden).forEach(card => window.resizeLocalReportChart?.(card)));
  window.addEventListener('pagehide', () => observer?.disconnect());
  window.addEventListener('pageshow', event => {
    if (event.persisted) window.loadSupersetReport(true);
  });
})();
