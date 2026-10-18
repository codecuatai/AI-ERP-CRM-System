/* Embedded SDK owns guest-token renewal; credentials stay on the CRM server. */
(() => {
  let dashboard = null;
  let loading = false;
  let loaded = false;
  const unavailable = 'Chưa tải được dashboard Superset. Nhận xét vẫn hiển thị ở trên; bạn có thể xem biểu đồ CRM hoặc thử kết nối lại.';
  const status = () => document.getElementById('supersetEmbedStatus');

  async function session() {
    const mount = document.getElementById('supersetEmbedMount');
    const response = await fetch(mount.dataset.sessionUrl, {
      credentials: 'same-origin', cache: 'no-store',
      headers: {Accept: 'application/json'}, signal: AbortSignal.timeout(25000),
    });
    if (!response.ok || response.redirected) throw new Error('session unavailable');
    return response.json();
  }

  function within(promise, milliseconds) {
    let timeout;
    return Promise.race([
      promise,
      new Promise((_, reject) => { timeout = setTimeout(() => reject(new Error('embed timeout')), milliseconds); }),
    ]).finally(() => clearTimeout(timeout));
  }

  window.loadSupersetReport = async (force = false) => {
    if (loading || (loaded && !force)) return;
    loading = true;
    loaded = false;
    dashboard?.unmount();
    dashboard = null;
    const root = document.getElementById('supersetEmbedMount');
    root.hidden = false;
    document.getElementById('supersetLocalFallback').hidden = true;
    const attempt = document.createElement('div');
    attempt.style.height = '100%';
    root.replaceChildren(attempt);
    status().textContent = 'Đang kết nối dashboard Superset…';
    const retry = document.getElementById('supersetEmbedRetry');
    retry.disabled = true;
    let abandoned = false;
    try {
      const initial = await session();
      let firstToken = initial.token;
      const pending = window.supersetEmbeddedSdk.embedDashboard({
        id: initial.id, supersetDomain: initial.domain, mountPoint: attempt,
        iframeTitle: 'Dashboard AI CRM — Apache Superset', referrerPolicy: 'strict-origin',
        dashboardUiConfig: {hideTitle: true, filters: {expanded: false}},
        fetchGuestToken: async () => {
          if (firstToken) { const token = firstToken; firstToken = null; return token; }
          try {
            const refreshed = await session();
            status().textContent = 'Đã kết nối Superset. Phiên xem được gia hạn tự động.';
            return refreshed.token;
          } catch (error) {
            status().textContent = 'Kết nối đang gián đoạn hoặc phiên CRM đã hết hạn. Hệ thống đang thử gia hạn; bạn có thể tải lại trang.';
            throw error;
          }
        },
      });
      pending.then(instance => { if (abandoned) instance.unmount(); }, () => {});
      dashboard = await within(pending, 30000);
      // A frame load alone also fires for blocked/error pages. Require a response
      // from Superset's embedded app before reporting an established connection.
      await within(dashboard.getScrollSize(), 20000);
      status().textContent = 'Đã kết nối Superset. Phiên xem được gia hạn tự động khi bạn đang đăng nhập CRM.';
      loaded = true;
    } catch (_) {
      abandoned = true;
      dashboard?.unmount();
      dashboard = null;
      attempt.remove();
      root.hidden = true;
      document.getElementById('supersetLocalFallback').hidden = false;
      window.renderReportFallback?.();
      status().textContent = unavailable;
    } finally {
      loading = false;
      retry.disabled = false;
    }
  };
  document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('supersetEmbedRetry')?.addEventListener('click', () => window.loadSupersetReport(true));
  });
  window.addEventListener('pagehide', () => {
    dashboard?.unmount();
    dashboard = null;
    loaded = false;
  });
  window.addEventListener('pageshow', event => {
    if (event.persisted && !document.getElementById('tab-content-superset-live').classList.contains('hidden')) {
      window.loadSupersetReport();
    }
  });
})();
