/* OVOS Open Data Dashboard — frontend logic */
'use strict';

const REFRESH_INTERVAL_MS = 60_000;
const numberFormatter = new Intl.NumberFormat();

const charts = {
  lang: null,
  intent: null,
  ww: null,
  session: null,
};

// ---- Theme-aware Chart.js palette ----
function isDarkMode() {
  return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
}

function chartTextColor() {
  return isDarkMode() ? '#e6e8ef' : '#222';
}

function chartGridColor() {
  return isDarkMode() ? 'rgba(255,255,255,.1)' : 'rgba(0,0,0,.08)';
}

function genColors(n) {
  const palette = ['#4a90e2', '#e67e22', '#2ecc71', '#e74c3c', '#9b59b6', '#1abc9c', '#f39c12', '#3498db'];
  return Array.from({ length: n }, (_, i) => palette[i % palette.length]);
}

// ---- Tab switching ----
document.querySelectorAll('.tab-btn').forEach((btn) => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab-btn').forEach((b) => b.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach((p) => p.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById('tab-' + btn.dataset.tab).classList.add('active');
  });
});

// ---- Stats + charts ----
async function loadStats() {
  const statusEl = document.getElementById('stats-status');
  statusEl.textContent = 'Loading…';
  statusEl.classList.remove('error');
  try {
    const res = await fetch('/dashboard/stats');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const s = await res.json();

    document.getElementById('stat-intents').textContent = numberFormatter.format(s.total_intents);
    document.getElementById('stat-wakewords').textContent = numberFormatter.format(s.total_wake_words);
    document.getElementById('stat-utterances').textContent = numberFormatter.format(s.total_utterances);

    renderDoughnut('lang', 'chart-lang', 'Languages', s.language_distribution);
    renderDoughnut('intent', 'chart-intent', 'Intents', s.intent_distribution);
    renderBar('ww', 'chart-ww', 'Wake Words', s.wake_word_distribution);
    renderDoughnut('session', 'chart-session', 'Local vs remote (HiveMind) clients', {
      local: s.session_distribution.true,
      remote: s.session_distribution.false,
      unknown: s.session_distribution.unknown,
    });

    statusEl.textContent = `Updated ${new Date().toLocaleTimeString()}`;
  } catch (err) {
    statusEl.textContent = `Failed to load stats: ${err.message}`;
    statusEl.classList.add('error');
  }
}

// Show/hide a "No data yet" message alongside a chart canvas, without
// touching the canvas itself (an empty Chart.js instance still needs to
// exist so later updates have something to update).
function toggleChartEmptyState(canvasId, isEmpty) {
  const canvas = document.getElementById(canvasId);
  canvas.classList.toggle('hidden', isEmpty);
  let note = canvas.parentElement.querySelector('.chart-empty');
  if (isEmpty) {
    if (!note) {
      note = document.createElement('p');
      note.className = 'chart-empty';
      canvas.insertAdjacentElement('afterend', note);
    }
    note.textContent = 'No data yet for this category';
  } else if (note) {
    note.remove();
  }
}

function renderDoughnut(key, canvasId, label, distObj) {
  const labels = Object.keys(distObj);
  const data = Object.values(distObj);
  toggleChartEmptyState(canvasId, data.every((n) => !n));
  const ctx = document.getElementById(canvasId).getContext('2d');
  if (charts[key]) {
    charts[key].data.labels = labels;
    charts[key].data.datasets[0].data = data;
    charts[key].data.datasets[0].backgroundColor = genColors(labels.length);
    charts[key].options.plugins.legend.labels.color = chartTextColor();
    charts[key].options.plugins.title.color = chartTextColor();
    charts[key].update();
    return;
  }
  charts[key] = new Chart(ctx, {
    type: 'doughnut',
    data: { labels, datasets: [{ data, backgroundColor: genColors(labels.length) }] },
    options: {
      plugins: {
        legend: { position: 'right', labels: { color: chartTextColor() } },
        title: { display: true, text: label, color: chartTextColor() },
      },
      responsive: true,
      maintainAspectRatio: false,
    },
  });
}

function renderBar(key, canvasId, label, distObj) {
  const labels = Object.keys(distObj);
  const data = Object.values(distObj);
  toggleChartEmptyState(canvasId, data.every((n) => !n));
  const ctx = document.getElementById(canvasId).getContext('2d');
  if (charts[key]) {
    charts[key].data.labels = labels;
    charts[key].data.datasets[0].data = data;
    charts[key].options.plugins.title.color = chartTextColor();
    charts[key].options.scales.x.ticks.color = chartTextColor();
    charts[key].options.scales.y.ticks.color = chartTextColor();
    charts[key].options.scales.x.grid.color = chartGridColor();
    charts[key].options.scales.y.grid.color = chartGridColor();
    charts[key].update();
    return;
  }
  charts[key] = new Chart(ctx, {
    type: 'bar',
    data: { labels, datasets: [{ label, data, backgroundColor: '#4a90e2' }] },
    options: {
      plugins: { title: { display: true, text: label, color: chartTextColor() } },
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: { ticks: { color: chartTextColor() }, grid: { color: chartGridColor() } },
        y: { ticks: { color: chartTextColor() }, grid: { color: chartGridColor() } },
      },
    },
  });
}

// Re-theme charts in place when the OS color scheme flips.
if (window.matchMedia) {
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
    Object.values(charts).forEach((c) => {
      if (!c) return;
      if (c.options.plugins.legend) c.options.plugins.legend.labels.color = chartTextColor();
      if (c.options.plugins.title) c.options.plugins.title.color = chartTextColor();
      if (c.options.scales) {
        Object.values(c.options.scales).forEach((scale) => {
          if (scale.ticks) scale.ticks.color = chartTextColor();
          if (scale.grid) scale.grid.color = chartGridColor();
        });
      }
      c.update();
    });
  });
}

// ---- Query helpers ----
function buildParams(pairs) {
  const p = new URLSearchParams();
  pairs.forEach(([k, v]) => { if (v) p.set(k, v); });
  return p.toString();
}

// Render an empty-state row spanning every column of a table's tbody.
function emptyRow(colspan) {
  return `<tr class="empty-row"><td colspan="${colspan}">No data yet for this category</td></tr>`;
}

function renderPagination(containerId, total, page, limit, loadFn) {
  const pages = Math.max(1, Math.ceil(total / limit));
  const el = document.getElementById(containerId);
  el.innerHTML = '';
  if (pages <= 1) return;
  for (let i = 1; i <= pages; i++) {
    const btn = document.createElement('button');
    btn.textContent = i;
    if (i === page) btn.classList.add('active');
    btn.addEventListener('click', () => loadFn(i));
    el.appendChild(btn);
  }
}

function setStatus(id, message, isError) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = message;
  el.classList.toggle('error', Boolean(isError));
}

// ---- Intents ----
async function loadIntents(page = 1) {
  const lang = document.getElementById('filter-intent-lang').value;
  const intent = document.getElementById('filter-intent-name').value;
  const from = document.getElementById('filter-intent-from').value;
  const to = document.getElementById('filter-intent-to').value;
  const params = buildParams([['lang', lang], ['intent', intent], ['date_from', from], ['date_to', to], ['page', page], ['limit', 50]]);
  setStatus('status-intents', 'Loading…', false);
  try {
    const res = await fetch('/intents?' + params);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    const tbody = document.querySelector('#table-intents tbody');
    tbody.innerHTML = data.items.length
      ? data.items.map((r) =>
          `<tr><td>${r.id}</td><td>${esc(r.intent)}</td><td>${esc(r.language)}</td><td>${esc(r.utterance)}</td><td title="${r.created_at ? esc(r.created_at) : ''}">${fmtDate(r.created_at)}</td></tr>`
        ).join('')
      : emptyRow(5);
    renderPagination('page-intents', data.total, data.page, data.limit, loadIntents);
    setStatus('status-intents', '', false);

    const csvParams = buildParams([['lang', lang], ['intent', intent], ['date_from', from], ['date_to', to], ['format', 'csv']]);
    document.getElementById('export-intents-csv').href = '/intents/export?' + csvParams;
    document.getElementById('export-intents-json').href = '/intents/export?' + csvParams.replace('format=csv', 'format=json');
  } catch (err) {
    setStatus('status-intents', `Failed to load intents: ${err.message}`, true);
  }
}

// ---- Wake Words ----
async function loadWakeWords(page = 1) {
  const name = document.getElementById('filter-ww-name').value;
  const plugin = document.getElementById('filter-ww-plugin').value;
  const params = buildParams([['name', name], ['plugin', plugin], ['page', page], ['limit', 50]]);
  setStatus('status-ww', 'Loading…', false);
  try {
    const res = await fetch('/wake_words?' + params);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    const tbody = document.querySelector('#table-ww tbody');
    tbody.innerHTML = '';
    if (!data.items.length) tbody.innerHTML = emptyRow(7);
    data.items.forEach((r) => {
      const tr = document.createElement('tr');
      tr.innerHTML = `<td>${r.id}</td><td>${esc(r.wake_word || '')}</td><td>${esc(r.model || '')}</td><td>${esc(r.plugin || '')}</td><td>${esc(r.language || '')}</td><td title="${r.created_at ? esc(r.created_at) : ''}">${fmtDate(r.created_at)}</td><td></td>`;
      const playBtn = document.createElement('button');
      playBtn.className = 'play-btn';
      playBtn.textContent = 'Play';
      playBtn.addEventListener('click', () => playAudio(`/wake_words/${r.id}/audio`));
      tr.lastElementChild.appendChild(playBtn);
      tbody.appendChild(tr);
    });
    renderPagination('page-ww', data.total, data.page, data.limit, loadWakeWords);
    setStatus('status-ww', '', false);
  } catch (err) {
    setStatus('status-ww', `Failed to load wake words: ${err.message}`, true);
  }
}

// ---- Utterances ----
async function loadUtterances(page = 1) {
  const lang = document.getElementById('filter-utt-lang').value;
  const model = document.getElementById('filter-utt-model').value;
  const plugin = document.getElementById('filter-utt-plugin').value;
  const params = buildParams([['lang', lang], ['model', model], ['plugin', plugin], ['page', page], ['limit', 50]]);
  setStatus('status-utt', 'Loading…', false);
  try {
    const res = await fetch('/utterances?' + params);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    const tbody = document.querySelector('#table-utt tbody');
    tbody.innerHTML = '';
    if (!data.items.length) tbody.innerHTML = emptyRow(6);
    data.items.forEach((r) => {
      const tr = document.createElement('tr');
      tr.innerHTML = `<td>${r.id}</td><td>${esc(r.model || '')}</td><td>${esc(r.plugin || '')}</td><td>${esc(r.language || '')}</td><td title="${r.created_at ? esc(r.created_at) : ''}">${fmtDate(r.created_at)}</td><td></td>`;
      const playBtn = document.createElement('button');
      playBtn.className = 'play-btn';
      playBtn.textContent = 'Play';
      playBtn.addEventListener('click', () => playAudio(`/utterances/${r.id}/audio`));
      tr.lastElementChild.appendChild(playBtn);
      tbody.appendChild(tr);
    });
    renderPagination('page-utt', data.total, data.page, data.limit, loadUtterances);
    setStatus('status-utt', '', false);
  } catch (err) {
    setStatus('status-utt', `Failed to load utterances: ${err.message}`, true);
  }
}

// ---- Audio modal ----
async function playAudio(url) {
  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const blob = await res.blob();
    const blobUrl = URL.createObjectURL(blob);
    const player = document.getElementById('audio-player');
    player.src = blobUrl;
    document.getElementById('audio-modal').classList.remove('hidden');
    document.getElementById('modal-close').focus();
    player.play();
  } catch (err) {
    alert(`Audio not found: ${err.message}`);
  }
}

function closeModal() {
  const player = document.getElementById('audio-player');
  player.pause();
  player.src = '';
  document.getElementById('audio-modal').classList.add('hidden');
}

document.getElementById('modal-close').addEventListener('click', closeModal);
document.getElementById('audio-modal').addEventListener('keydown', (e) => {
  if (e.key === 'Escape') closeModal();
});
document.getElementById('apply-intents').addEventListener('click', () => loadIntents(1));
document.getElementById('apply-ww').addEventListener('click', () => loadWakeWords(1));
document.getElementById('apply-utt').addEventListener('click', () => loadUtterances(1));

// ---- Utility ----
function esc(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

// Formats an ISO timestamp in the browser's own locale; callers also set a
// `title` attribute with the raw ISO value so the exact instant is always
// recoverable regardless of locale ambiguity.
function fmtDate(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleString();
}

// ---- Init + auto-refresh ----
loadStats();
loadIntents(1);
loadWakeWords(1);
loadUtterances(1);

setInterval(loadStats, REFRESH_INTERVAL_MS);
