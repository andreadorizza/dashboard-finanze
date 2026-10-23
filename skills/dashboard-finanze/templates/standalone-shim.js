/* A tiny stand-in for the Dashboard artifact's `dash` API, so the same page works as one
   self-contained HTML file when the session has no Dashboard type (Free plan, Claude Code).
   build_page.py puts the data in window.__DASH_DATA__ = {id: {columns, rows}} before this. */
(function () {
  const RAW = window.__DASH_DATA__ || {};
  const DEFAULTS = window.__DASH_PARAMS__ || {};
  const calcs = {};
  const listeners = [];
  let params = Object.assign({}, DEFAULTS);
  const colors = [1, 2, 3, 4, 5, 6, 7, 8].map(i => `var(--series-${i})`);

  function data(id) {
    if (RAW[id]) return {status: 'ok', data: RAW[id].rows, columns: RAW[id].columns, refreshing: false, meta: []};
    const c = calcs[id];
    if (!c) return {status: 'missing', data: [], meta: []};
    if (!('value' in c)) {
      try {
        const ins = c.inputs.map(i => {
          const d = data(i);
          if (d.status !== 'ok') throw new Error('input ' + i + ' is ' + d.status);
          return d.data;
        });
        c.value = c.fn(...ins);
        c.error = null;
      } catch (e) {
        c.value = [];
        c.error = String(e);
        console.error('calc ' + id + ': ' + e);
      }
    }
    return c.error ? {status: 'error', data: [], message: c.error, meta: []} : {status: 'ok', data: c.value, meta: []};
  }

  function run() {
    listeners.forEach(fn => {
      try { fn(); } catch (e) { console.error(e); }
    });
  }

  let t = null;
  window.addEventListener('resize', () => { clearTimeout(t); t = setTimeout(run, 150); });
  window.addEventListener('load', run);

  window.dash = {
    data,
    onData(fn) { listeners.push(fn); try { fn(); } catch (e) { console.error(e); } },
    calc(id, o) { calcs[id] = {inputs: o.inputs || [], fn: o.fn, title: o.title, description: o.description}; },
    loader() {},
    colors,
    params: () => Object.assign({}, params),
    setParams(p) { Object.assign(params, p); run(); },
    resetParams() { params = Object.assign({}, DEFAULTS); run(); },
    setLink(name) { try { history.replaceState(null, '', '#' + name); } catch (e) { /* preview */ } },
    refresh() {}
  };
})();
