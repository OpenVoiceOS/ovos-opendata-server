/* OVOS Open Data Dashboard — frontend logic */
'use strict';

let langChart = null;
let intentChart = null;
let wwChart = null;

// Tab switching
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById('tab-' + btn.dataset.tab).classList.add('active');
  });
});

// Load stats and init charts
async function loadStats() {
  const res = await fetch('/dashboard/stats');
  if (!res.ok) return;
  const s = await res.json();

  document.getElementById('stat-intents').textContent = s.total_intents.toLocaleString();
  document.getElementById('stat-wakewords').textContent = s.total_wake_words.toLocaleString();
  document.getElementById('stat-utterances').textContent = s.total_utterances.toLocaleString();

  initDoughnut('chart-lang', 'Languages', s.language_distribution);
  initDoughnut('chart-intent', 'Intents', s.intent_distribution);
  initBar('chart-ww', 'Wake Words', s.wake_word_distribution);
}

function initDoughnut(canvasId, label, distObj) {
  const ctx = document.getElementById(canvasId).getContext('2d');
  const labels = Object.keys(distObj);
  const data = Object.values(distObj);
  if (canvasId === 'chart-lang' && langChart) langChart.destroy();
  if (canvasId === 'chart-intent' && intentChart) intentChart.destroy();
  const chart = new Chart(ctx, {
    type: 'doughnut',
    data: { labels, datasets: [{ data, backgroundColor: genColors(labels.length) }] },
    options: { plugins: { legend: { position: 'right' }, title: { display: true, text: label } }, responsive: true, maintainAspectRatio: false }
  });
  if (canvasId === 'chart-lang') langChart = chart;
  if (canvasId === 'chart-intent') intentChart = chart;
}

function initBar(canvasId, label, distObj) {
  const ctx = document.getElementById(canvasId).getContext('2d');
  const labels = Object.keys(distObj);
  const data = Object.values(distObj);
  if (wwChart) wwChart.destroy();
  wwChart = new Chart(ctx, {
    type: 'bar',
    data: { labels, datasets: [{ label, data, backgroundColor: '#4a90e2' }] },
    options: { plugins: { title: { display: true, text: label } }, responsive: true, maintainAspectRatio: false }
  });
}

function genColors(n) {
  const palette = ['#4a90e2','#e67e22','#2ecc71','#e74c3c','#9b59b6','#1abc9c','#f39c12','#3498db'];
  return Array.from({ length: n }, (_, i) => palette[i % palette.length]);
}

// Build query string from filters
function buildParams(pairs) {
  const p = new URLSearchParams();
  pairs.forEach(([k, v]) => { if (v) p.set(k, v); });
  return p.toString();
}

// Render pagination
function renderPagination(containerId, total, page, limit, loadFn) {
  const pages = Math.max(1, Math.ceil(total / limit));
  const el = document.getElementById(containerId);
  el.innerHTML = '';
  for (let i = 1; i <= pages; i++) {
    const btn = document.createElement('button');
    btn.textContent = i;
    if (i === page) btn.classList.add('active');
    btn.addEventListener('click', () => loadFn(i));
    el.appendChild(btn);
  }
}

// ---- Intents ----
async function loadIntents(page = 1) {
  const lang = document.getElementById('filter-intent-lang').value;
  const intent = document.getElementById('filter-intent-name').value;
  const from = document.getElementById('filter-intent-from').value;
  const to = document.getElementById('filter-intent-to').value;
  const params = buildParams([['lang', lang], ['intent', intent], ['date_from', from], ['date_to', to], ['page', page], ['limit', 50]]);
  const res = await fetch('/intents?' + params);
  if (!res.ok) return;
  const data = await res.json();
  const tbody = document.querySelector('#table-intents tbody');
  tbody.innerHTML = data.items.map(r =>
    `<tr><td>${r.id}</td><td>${esc(r.intent)}</td><td>${esc(r.language)}</td><td>${esc(r.utterance)}</td><td>${fmtDate(r.created_at)}</td></tr>`
  ).join('');
  renderPagination('page-intents', data.total, data.page, data.limit, loadIntents);
  // Update export links
  const csvParams = buildParams([['lang', lang], ['intent', intent], ['date_from', from], ['date_to', to], ['format', 'csv']]);
  document.getElementById('export-intents-csv').href = '/intents/export?' + csvParams;
  document.getElementById('export-intents-json').href = '/intents/export?' + csvParams.replace('format=csv', 'format=json');
}

// ---- Wake Words ----
async function loadWakeWords(page = 1) {
  const name = document.getElementById('filter-ww-name').value;
  const plugin = document.getElementById('filter-ww-plugin').value;
  const params = buildParams([['name', name], ['plugin', plugin], ['page', page], ['limit', 50]]);
  const res = await fetch('/wake_words?' + params);
  if (!res.ok) return;
  const data = await res.json();
  const tbody = document.querySelector('#table-ww tbody');
  tbody.innerHTML = data.items.map(r =>
    `<tr><td>${r.id}</td><td>${esc(r.wake_word||'')}</td><td>${esc(r.model||'')}</td><td>${esc(r.plugin||'')}</td><td>${esc(r.language||'')}</td><td>${fmtDate(r.created_at)}</td><td><button class="play-btn" onclick="playAudio('/wake_words/${r.id}/audio')">Play</button></td></tr>`
  ).join('');
  renderPagination('page-ww', data.total, data.page, data.limit, loadWakeWords);
}

// ---- Utterances ----
async function loadUtterances(page = 1) {
  const lang = document.getElementById('filter-utt-lang').value;
  const model = document.getElementById('filter-utt-model').value;
  const plugin = document.getElementById('filter-utt-plugin').value;
  const params = buildParams([['lang', lang], ['model', model], ['plugin', plugin], ['page', page], ['limit', 50]]);
  const res = await fetch('/utterances?' + params);
  if (!res.ok) return;
  const data = await res.json();
  const tbody = document.querySelector('#table-utt tbody');
  tbody.innerHTML = data.items.map(r =>
    `<tr><td>${r.id}</td><td>${esc(r.model||'')}</td><td>${esc(r.plugin||'')}</td><td>${esc(r.language||'')}</td><td>${fmtDate(r.created_at)}</td><td><button class="play-btn" onclick="playAudio('/utterances/${r.id}/audio')">Play</button></td></tr>`
  ).join('');
  renderPagination('page-utt', data.total, data.page, data.limit, loadUtterances);
}

// ---- Audio modal ----
async function playAudio(url) {
  const res = await fetch(url);
  if (!res.ok) { alert('Audio not found.'); return; }
  const blob = await res.blob();
  const blobUrl = URL.createObjectURL(blob);
  const player = document.getElementById('audio-player');
  player.src = blobUrl;
  document.getElementById('audio-modal').classList.remove('hidden');
  player.play();
}

function closeModal() {
  const player = document.getElementById('audio-player');
  player.pause();
  player.src = '';
  document.getElementById('audio-modal').classList.add('hidden');
}

// Utility
function esc(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

function fmtDate(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleString();
}

// Init on load
loadStats();
loadIntents(1);
loadWakeWords(1);
loadUtterances(1);
