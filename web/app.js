'use strict';

const TIERS = ['DISPATCH', 'VERIFY', 'LOG'];
const RANK = { DISPATCH: 0, VERIFY: 1, LOG: 2 };
const GLOSS = { DISPATCH: 'message field staff now', VERIFY: 'camera and photo first', LOG: 'dashboard only' };
const INK = { DISPATCH: '#c21e2e', VERIFY: '#c9741a', LOG: '#7c8083', paper: '#f6f8f3', ink: '#221c15', contour: '#8e5428' };
const WINDOW = { A: 'Window A · S-NPP', B: 'Window B · NOAA-20', live: 'Live' };
const CONF = { h: 'high', n: 'nominal', l: 'low' };
const FIELD = { fire: 'real forest fire', none: 'nothing found', farm: 'farm or village fire', burn: 'our controlled burn' };
const PAGE = 200;
const POLL_MS = 3000;

const $ = (s, root = document) => root.querySelector(s);
const SVG = 'http://www.w3.org/2000/svg';

function el(tag, attrs = {}, ...kids) {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v == null || v === false) continue;
    if (k === 'class') n.className = v;
    else if (k.startsWith('on')) n.addEventListener(k.slice(2), v);
    else n.setAttribute(k, v === true ? '' : v);
  }
  for (const k of kids.flat()) if (k != null && k !== false) n.append(k instanceof Node ? k : String(k));
  return n;
}
function svgUse(id, cls) {
  const s = document.createElementNS(SVG, 'svg');
  s.setAttribute('class', cls);
  s.setAttribute('aria-hidden', 'true');
  const u = document.createElementNS(SVG, 'use');
  u.setAttribute('href', '#' + id);
  s.append(u);
  return s;
}
const sym = tier => svgUse('sym-' + tier, 'sym');
const icon = id => svgUse('i-' + id, 'i');

const IST = new Intl.DateTimeFormat('en-IN', { timeZone: 'Asia/Kolkata', day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit', hour12: false });
const IST_CLOCK = new Intl.DateTimeFormat('en-IN', { timeZone: 'Asia/Kolkata', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
const UTC = new Intl.DateTimeFormat('en-GB', { timeZone: 'UTC', day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit', hour12: false });
const ist = d => IST.format(d).replace(',', '') + ' IST';
const num = n => n.toLocaleString('en-IN');
const km = k => (k < 10 ? k.toFixed(1) : Math.round(k)) + ' km';
const signed = d => (d > 0 ? '+' : '−') + Math.abs(d).toFixed(2);
function dms(v, pos, neg) {
  let s = Math.round(Math.abs(v) * 3600);
  const d = Math.floor(s / 3600); s -= d * 3600;
  const m = Math.floor(s / 60); s -= m * 60;
  return `${d}°${String(m).padStart(2, '0')}′${String(s).padStart(2, '0')}″${v >= 0 ? pos : neg}`;
}
function dm(v, pos, neg) {
  const m = Math.round(Math.abs(v) * 60);
  const d = Math.floor(m / 60), r = m % 60;
  return `${d}°${r ? String(r).padStart(2, '0') + '′' : ''}${v >= 0 ? pos : neg}`;
}
function since(ms) {
  const s = Math.round(ms / 1000);
  if (s < 90) return `${s} s`;
  if (s < 5400) return `${Math.round(s / 60)} min`;
  return `${(s / 3600).toFixed(1)} h`;
}

// ---- state ------------------------------------------------------------------
const S = {
  all: [], byId: new Map(), list: [], limit: PAGE, version: null,
  selected: null, hover: null, tiers: new Set(['DISPATCH', 'VERIFY']), win: 'all', q: '',
  marks: new Map(), outcomes: {}, sent: {}, baseline: true,
};
const mark = (id, patch) => S.marks.set(id, { ...(S.marks.get(id) || {}), ...patch });

function toAlert(cols, row) {
  const a = {};
  cols.forEach((c, i) => { a[c] = row[i]; });
  a.t = new Date(String(a.t).replace(' ', 'T'));
  a.village_name = a.village_name || 'unnamed place';
  return a;
}

// ---- map ----------------------------------------------------------------------
L.Canvas.include({
  _updateShape(layer) {
    if (!this._drawing || layer._empty()) return;
    const p = layer._point, ctx = this._ctx, r = layer._radius, k = layer.options.shape;
    ctx.beginPath();
    if (k === 'tri') { ctx.moveTo(p.x, p.y - r * 1.2); ctx.lineTo(p.x + r * 1.05, p.y + r * 0.78); ctx.lineTo(p.x - r * 1.05, p.y + r * 0.78); ctx.closePath(); }
    else if (k === 'dia') { ctx.moveTo(p.x, p.y - r); ctx.lineTo(p.x + r, p.y); ctx.lineTo(p.x, p.y + r); ctx.lineTo(p.x - r, p.y); ctx.closePath(); }
    else ctx.arc(p.x, p.y, r * 0.62, 0, Math.PI * 2);
    this._fillStroke(ctx, layer);
  },
});
const Shape = L.CircleMarker.extend({ _updatePath() { this._renderer._updateShape(this); } });
const STYLE = {  // bubblingMouseEvents off: a symbol click must not also place a burn
  DISPATCH: { shape: 'tri', radius: 6, color: INK.paper, weight: 1, fillColor: INK.DISPATCH, fillOpacity: 1, bubblingMouseEvents: false },
  VERIFY: { shape: 'dia', radius: 5.2, color: INK.VERIFY, weight: 2, fillColor: INK.paper, fillOpacity: 1, bubblingMouseEvents: false },
  LOG: { shape: 'dot', radius: 5, stroke: false, fillColor: INK.LOG, fillOpacity: 0.85, bubblingMouseEvents: false },
};

const map = L.map('map', { preferCanvas: true, zoomSnap: 0.25, minZoom: 6.5, maxZoom: 15, maxBounds: [[27.6, 76.3], [32.6, 82.3]], keyboard: true });
const canvas = L.canvas({ padding: 0.4 });
L.tileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', {
  subdomains: 'abc', maxZoom: 15,
  attribution: 'Terrain © <a href="https://opentopomap.org">OpenTopoMap</a> (CC-BY-SA), © <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>, SRTM · Boundary: geoBoundaries, DataMeet · Alerts: NASA FIRMS',
}).addTo(map);
map.attributionControl.setPrefix(false);
L.control.scale({ imperial: false, position: 'bottomleft' }).addTo(map);
map.setView([30.1, 79.2], 8);
fetch('uttarakhand.geojson').then(r => r.json()).then(g => {
  // Cased like a printed boundary: a paper underlay keeps the dash-dot legible on busy relief.
  L.geoJSON(g, { interactive: false, style: { color: INK.paper, weight: 5, opacity: 0.9, fill: false } }).addTo(map);
  const outline = L.geoJSON(g, { interactive: false, style: { color: INK.ink, weight: 2, dashArray: '11 4 2 4', fill: false } }).addTo(map);
  map.fitBounds(outline.getBounds(), { padding: [10, 10] });
});
const layers = { LOG: L.layerGroup().addTo(map), VERIFY: L.layerGroup().addTo(map), DISPATCH: L.layerGroup().addTo(map) };
const ring = L.circleMarker([0, 0], { radius: 12, color: INK.ink, weight: 1.5, fill: false, interactive: false, renderer: L.svg() });
const burnLayer = L.layerGroup().addTo(map);
let placing = null;

// Symbols shrink when zoomed out so thousands of alerts stay a pattern, not a blot.
const zoomScale = () => (map.getZoom() < 8.5 ? 0.6 : map.getZoom() < 9.5 ? 0.8 : 1);
let drawnScale = null;
map.on('zoomend', () => { if (zoomScale() !== drawnScale) renderMarkers(); });

function renderMarkers() {
  for (const t of TIERS) layers[t].clearLayers();
  const shown = S.list, k = drawnScale = zoomScale();
  for (const t of ['LOG', 'VERIFY', 'DISPATCH']) {
    const style = { ...STYLE[t], radius: STYLE[t].radius * k, weight: STYLE[t].weight && Math.max(1, STYLE[t].weight * k), renderer: canvas };
    for (const a of shown) {
      if (a.tier !== t) continue;
      const m = new Shape([a.latitude, a.longitude], style);
      m.on('click', () => select(a.id, false));
      layers[t].addLayer(m);
    }
  }
}

function drawTicks() {
  const box = $('#ticks');
  box.replaceChildren();
  const b = map.getBounds(), z = map.getZoom();
  const step = z < 7.5 ? 1 : z < 8.6 ? 0.5 : z < 9.6 ? 0.25 : z < 11 ? 0.1 : 0.05;
  for (let i = Math.ceil(b.getWest() / step); i * step <= b.getEast(); i++) {
    const lon = +(i * step).toFixed(4), x = map.latLngToContainerPoint([b.getNorth(), lon]).x;
    box.append(el('span', { class: 'tick tick-lon', style: `left:${x}px` }, dm(lon, 'E', 'W')));
  }
  for (let i = Math.ceil(b.getSouth() / step); i * step <= b.getNorth(); i++) {
    const lat = +(i * step).toFixed(4), y = map.latLngToContainerPoint([lat, b.getWest()]).y;
    box.append(el('span', { class: 'tick tick-lat', style: `top:${y}px` }, dm(lat, 'N', 'S')));
  }
}
map.on('moveend zoomend resize', drawTicks);
map.on('move zoom', () => drawLeader(false));

// ---- queue --------------------------------------------------------------------
function filtered() {
  const q = S.q.trim().toLowerCase();
  return S.all.filter(a => (S.win === 'all' || a.window === S.win)
    && (!q || a.id.includes(q) || a.village_name.toLowerCase().includes(q)));
}

function reasons(a) {
  const parts = String(a.why || '').split('; ');
  const context = parts.pop() || '';
  const rest = context.replace(/^[\d.]+ km from .+?, (?=slope)/, '');
  return [...parts, rest].filter(Boolean).join(' · ');
}

function marksFor(a) {
  const m = S.marks.get(a.id) || {}, out = [];
  if (m.isNew) out.push(el('span', { class: 'mark mark-new' }, 'New'));
  if (m.changed) out.push(el('span', { class: 'mark mark-changed' }, `${m.changed.from} → ${m.changed.to}`));
  const o = S.outcomes[a.id];
  if (o) out.push(o.src === 'field'
    ? el('span', { class: 'mark mark-field' }, `Field: ${FIELD[o.result] || o.result}`)
    : el('span', { class: 'mark mark-camera' }, `Camera: ${o.result === 'smoke' ? 'smoke' : 'no smoke'}`));
  if (S.sent[a.id]) out.push(el('span', { class: 'mark mark-sent' }, icon('flag'), 'Sent'));
  return out;
}

function item(a) {
  const li = el('li', { class: 'item', 'data-id': a.id, 'aria-current': a.id === S.selected ? 'true' : null });
  li.append(el('button', {
    class: 'row', type: 'button',
    'aria-label': `${a.tier}, p ${a.p.toFixed(2)}, risk ${a.r} of 7, ${km(a.village_km)} from ${a.village_name}`,
    onclick: () => select(a.id, true),
    onmouseenter: () => setHover(a.id), onmouseleave: () => setHover(null),
  },
  sym(a.tier),
  el('span', { class: 'line1' },
    el('span', { class: 'place' }, `${km(a.village_km)} from ${a.village_name}`),
    el('span', { class: 'pr' }, 'p ', el('b', {}, a.p.toFixed(2)), ' · risk ', el('b', {}, a.r))),
  el('span', { class: 'why' }, reasons(a)),
  el('span', { class: 'meta' }, el('time', { datetime: a.t.toISOString() }, ist(a.t)), el('span', {}, WINDOW[a.window]), marksFor(a))));
  return li;
}

function groupHead(tier, n) {
  return el('li', { class: 'group', 'data-tier': tier, role: 'presentation' },
    el('h3', {}, tier), el('span', { class: 'count' }, num(n)), el('span', { class: 'gloss' }, GLOSS[tier]));
}

function render({ markers = true } = {}) {
  const base = filtered();
  const counts = { DISPATCH: 0, VERIFY: 0, LOG: 0 };
  for (const a of base) counts[a.tier]++;
  for (const t of TIERS) $('#n-' + t).textContent = num(counts[t]);
  $('#n-all').textContent = num(base.length);

  S.list = base.filter(a => S.tiers.has(a.tier)).sort((x, y) => RANK[x.tier] - RANK[y.tier] || y.p - x.p || y.t - x.t);
  const queue = $('#queue');
  const top = $('.margin').scrollTop;
  queue.replaceChildren();
  queue.setAttribute('aria-busy', 'false');
  if (!S.list.length) {
    queue.append(el('li', { class: 'queue-note' }, 'No alerts match these filters.', el('br'),
      el('button', { class: 'btn', type: 'button', onclick: resetFilters }, 'Show DISPATCH and VERIFY, all windows')));
    $('#more').hidden = true;
  } else {
    const page = S.list.slice(0, S.limit);
    const sel = S.selected && S.byId.get(S.selected);
    if (sel && S.list.includes(sel) && !page.includes(sel)) {
      queue.append(el('li', { class: 'group', role: 'presentation' }, el('h3', {}, 'SELECTED ON THE SHEET')), item(sel));
    }
    let current = null;
    for (const a of page) {
      if (a.tier !== current) { current = a.tier; queue.append(groupHead(current, counts[current])); }
      queue.append(item(a));
    }
    const left = S.list.length - page.length;
    $('#more').hidden = left <= 0;
    $('#more').textContent = `Show ${num(Math.min(PAGE, left))} more · ${num(left)} not listed`;
  }
  $('.margin').scrollTop = top;
  if (markers) renderMarkers();
  drawLeader(false);
}

function resetFilters() {
  S.tiers = new Set(['DISPATCH', 'VERIFY']); S.win = 'all'; S.q = ''; S.limit = PAGE;
  for (const box of document.querySelectorAll('input[name=tier]')) box.checked = S.tiers.has(box.value);
  $('#window').value = 'all'; $('#q').value = '';
  render();
}

// ---- selection and the leader line -------------------------------------------
async function select(id, fromQueue) {
  const a = S.byId.get(id);
  if (!a) return;
  S.selected = id;
  history.replaceState(null, '', '#' + id);
  const m = S.marks.get(id);
  if (m && (m.isNew || m.changed)) mark(id, { isNew: false, changed: null });
  const widen = !S.tiers.has(a.tier) || (S.win !== 'all' && S.win !== a.window);
  if (widen) { S.tiers.add(a.tier); S.win = 'all'; syncFilters(); }
  render({ markers: widen });
  const row = $(`.item[data-id="${CSS.escape(id)}"]`);
  if (row && !fromQueue) row.scrollIntoView({ block: 'nearest' });
  const ll = [a.latitude, a.longitude];
  if (!map.getBounds().pad(-0.08).contains(ll)) map.panTo(ll, { animate: true, duration: 0.5 });
  ring.setLatLng(ll).addTo(map);
  requestAnimationFrame(() => drawLeader(true));
  showEvidence(id);
}

function syncFilters() {
  for (const box of document.querySelectorAll('input[name=tier]')) box.checked = S.tiers.has(box.value);
  $('#window').value = S.win;
}

function setHover(id) {
  S.hover = id;
  drawLeader(false);
}

function drawLeader(animate) {
  const svg = $('#leader');
  const id = S.hover || S.selected;
  const a = id && S.byId.get(id);
  const row = a && $(`.item[data-id="${CSS.escape(id)}"] .row`);
  const hide = () => { svg.style.display = 'none'; };
  if (!a || !row || matchMedia('(max-width: 760px)').matches) return hide();
  const mr = $('#map').getBoundingClientRect(), qr = $('.margin').getBoundingClientRect(), rr = row.getBoundingClientRect();
  const pt = map.latLngToContainerPoint([a.latitude, a.longitude]);
  const x2 = mr.left + pt.x, y2 = mr.top + pt.y;
  if (x2 < mr.left || x2 > mr.right || y2 < mr.top || y2 > mr.bottom) return hide();
  const y1 = Math.min(Math.max(rr.top + rr.height / 2, qr.top + 10), qr.bottom - 10);
  const x1 = qr.right;
  svg.style.display = 'block';
  svg.classList.toggle('is-hover', S.hover != null && S.hover !== S.selected);
  const path = $('.leader-line', svg);
  path.setAttribute('d', `M${x1} ${y1} H${x1 + 16} L${x2} ${y2}`);
  const tag = $('.leader-tag', svg), text = $('text', tag), rect = $('rect', tag);
  text.textContent = `${dms(a.latitude, 'N', 'S')}  ${dms(a.longitude, 'E', 'W')}`;
  const right = x2 + 210 < mr.right;
  text.setAttribute('x', right ? x2 + 16 : x2 - 16);
  text.setAttribute('y', y2 - 14);
  text.setAttribute('text-anchor', right ? 'start' : 'end');
  const bb = text.getBBox();
  rect.setAttribute('x', bb.x - 6); rect.setAttribute('y', bb.y - 3);
  rect.setAttribute('width', bb.width + 12); rect.setAttribute('height', bb.height + 6);
  if (animate) {
    const len = path.getTotalLength();
    path.style.setProperty('--len', len);
    path.style.strokeDasharray = len;
    svg.classList.remove('is-drawing');
    void svg.getBoundingClientRect();
    svg.classList.add('is-drawing');
    path.addEventListener('animationend', () => { svg.classList.remove('is-drawing'); path.style.strokeDasharray = ''; }, { once: true });
  }
}
$('.margin').addEventListener('scroll', () => drawLeader(false), { passive: true });
addEventListener('resize', () => drawLeader(false));

// ---- evidence panel -----------------------------------------------------------
function dockHead(tier, title, sub) {
  return el('header', { class: 'dock-head' }, tier ? sym(tier) : null,
    el('div', {}, el('h2', { id: 'ev-title' }, title), sub ? el('p', { class: 'ev-id' }, sub) : null),
    el('button', { class: 'icon-btn', type: 'button', 'aria-label': 'Close the evidence panel', onclick: closeDock }, icon('close')));
}

function scaleBar(p, th, tier) {
  const W = 360, x = v => 8 + v * (W - 16);
  const s = document.createElementNS(SVG, 'svg');
  s.setAttribute('class', 'scale');
  s.setAttribute('viewBox', `0 0 ${W} 44`);
  s.setAttribute('role', 'img');
  s.setAttribute('aria-label', `p ${p.toFixed(2)} on a 0 to 1 scale; VERIFY from ${th.verify}, DISPATCH from ${th.dispatch}, or from ${th.risky} with risk ${th.risky_r} or more`);
  const add = (tag, attrs, text) => { const n = document.createElementNS(SVG, tag); for (const k in attrs) n.setAttribute(k, attrs[k]); if (text != null) n.textContent = text; s.append(n); return n; };
  for (let i = 0; i < 10; i++) add('rect', { x: x(i / 10), y: 16, width: (W - 16) / 10, height: 6, fill: i % 2 ? INK.paper : INK.ink, stroke: INK.ink, 'stroke-width': 1 });
  for (const [v, label, anchor] of [[0, '0', 'start'], [th.verify, 'VERIFY', 'middle'], [th.risky, '0.6', 'middle'], [th.dispatch, 'DISPATCH', 'middle'], [1, '1', 'end']]) {
    add('line', { x1: x(v), x2: x(v), y1: 22, y2: 28, stroke: INK.ink, 'stroke-width': 1 });
    add('text', { x: x(v), y: 39, 'text-anchor': anchor, 'font-size': 10, 'font-weight': 600, fill: '#5a4a3a' }, label);
  }
  add('path', { d: `M${x(p)} 14 l-6 -9 h12 z`, fill: INK[tier], stroke: INK.ink, 'stroke-width': 1 });
  return s;
}

async function showEvidence(id) {
  const dock = $('#evidence');
  $('#burnpanel').hidden = true;
  $('.sheet').classList.remove('is-placing');
  dock.hidden = false;
  if (!dock.firstChild) dock.append(el('p', { class: 'queue-note' }, 'Loading evidence…'));
  let d;
  try {
    const r = await fetch('/api/alerts/' + encodeURIComponent(id), { cache: 'no-store' });
    if (!r.ok) throw new Error(r.status === 404 ? 'This alert is no longer in the data.' : `Server answered ${r.status}.`);
    d = await r.json();
  } catch (e) {
    if (S.selected === id) dock.replaceChildren(dockHead(null, 'Evidence unavailable'), el('p', { class: 'queue-note' }, `${e.message} Pick the alert again to retry.`));
    return;
  }
  if (S.selected !== id) return;
  const a = d.alert, tier = a.tier, p = Number(a.p), t = new Date(String(a.t).replace(' ', 'T'));
  const ledger = el('ol', { class: 'ledger' }, el('li', {}, el('span', {}, 'Starting value'), el('span', { class: 'd' }, d.p_start.toFixed(2))));
  for (const row of d.ledger) ledger.append(el('li', {}, el('span', {}, row.text), el('span', { class: 'd ' + (row.delta < 0 ? 'neg' : 'pos') }, signed(row.delta))));
  if (!d.ledger.length) ledger.append(el('li', {}, el('span', {}, 'No check moved p'), el('span', { class: 'd' }, '0.00')));
  ledger.append(el('li', { class: 'total' }, el('span', {}, d.image ? 'Data checks, clipped to 0–1' : 'p, clipped to 0–1'), el('span', { class: 'd' }, d.p_sum.toFixed(2))));
  if (d.image) ledger.append(el('li', { class: 'override' }, el('span', {}, `Image check: ${d.image} overrides the sum`), el('span', { class: 'd' }, d.image_p.toFixed(2))));

  const riskList = el('ol', { class: 'ledger' });
  for (const row of d.risk) riskList.append(el('li', {}, el('span', {}, row.text), el('span', { class: 'd pos' }, '+' + row.points)));
  if (!d.risk.length) riskList.append(el('li', {}, el('span', {}, 'No risk condition met'), el('span', { class: 'd' }, '0')));
  const pips = el('span', { class: 'pips', 'aria-hidden': 'true' }, Array.from({ length: 7 }, (_, i) => el('i', { class: i < a.r ? 'on' : null })));

  const events = [{ label: 'Detected by satellite', at: t, kind: 'detected' }];
  for (const h of d.history) {
    events.push({ at: new Date(h.ts * 1000), kind: h.src === 'field' ? 'field' : 'camera',
      label: h.src === 'field' ? `Field staff: ${FIELD[h.result] || h.result}` : `Camera ${h.src}: ${h.result === 'smoke' ? 'smoke in 4 or more of 6 frames' : 'no smoke'}` });
  }
  if (d.sent) events.push({ at: new Date(d.sent * 1000), kind: 'sent', label: 'Dispatched: Telegram message and CAP file' });
  events.sort((x, y) => x.at - y.at);
  const life = el('ol', { class: 'life' }, events.map(e => el('li', {}, el('time', { datetime: e.at.toISOString(), title: ist(e.at) }, IST_CLOCK.format(e.at)), el('span', {}, e.label))));
  const span = events.at(-1).at - events[0].at;
  let bar = null;
  if (events.length > 1 && span > 0 && span < 864e5) {
    const colour = { camera: INK.VERIFY, field: '#2f6a2a', sent: INK.ink, detected: INK.LOG };
    bar = el('div', { class: 'lifebar', role: 'img', 'aria-label': `From detection to the last step took ${since(span)}` },
      events.slice(1).map((e, i) => el('span', { style: `flex:${Math.max(e.at - events[i].at, 1)};background:${colour[e.kind]}`, title: `${since(e.at - events[i].at)} to: ${e.label}` })));
  }

  dock.replaceChildren(
    dockHead(tier, `${tier} · ${GLOSS[tier]}`, a.id),
    el('section', {},
      el('p', { class: 'ev-headline' }, el('span', {}, 'p ', el('b', {}, p.toFixed(2))), el('span', {}, 'risk ', el('b', {}, a.r), ' of 7', pips)),
      scaleBar(p, d.thresholds, tier)),
    el('section', {}, el('h3', {}, `Why p is ${p.toFixed(2)}`), ledger),
    el('section', {}, el('h3', {}, `Why risk is ${a.r}`), riskList),
    el('section', {}, el('h3', {}, 'Where'),
      el('dl', { class: 'facts' },
        el('dt', {}, 'Position'), el('dd', { class: 'coords' }, `${dms(a.latitude, 'N', 'S')}  ${dms(a.longitude, 'E', 'W')}`),
        el('dt', {}, 'Nearest place'), el('dd', {}, `${a.village_name || 'unnamed place'}, ${km(a.village_km)}`),
        el('dt', {}, 'Slope'), el('dd', {}, `${Math.round(a.slope)}°`),
        el('dt', {}, 'Land cover'), el('dd', {}, `${Math.round(a.veg * 100)}% vegetation, ${Math.round(a.tree * 100)}% tree, ${Math.round(a.farm * 100)}% farm or built-up`),
        el('dt', {}, 'Map'), el('dd', {}, el('a', { href: d.map, target: '_blank', rel: 'noopener' }, 'Open in Google Maps')))),
    el('section', {}, el('h3', {}, 'Detection'),
      el('dl', { class: 'facts' },
        el('dt', {}, 'Seen'), el('dd', {}, `${ist(t)} (${UTC.format(t)} UTC)`),
        el('dt', {}, 'Satellite'), el('dd', {}, `${a.instrument || 'VIIRS'} ${a.satellite || ''}, ${a.confidence ? CONF[String(a.confidence)[0]] || a.confidence : '—'} confidence`),
        el('dt', {}, 'Fire power'), el('dd', {}, `${Number(a.frp).toFixed(1)} MW`),
        el('dt', {}, 'Repeats'), el('dd', {}, `seen ${a.seen + 1} times in 12 h; this cell fired ${a.recur} times in 2023–25`),
        el('dt', {}, 'Weather'), el('dd', {}, a.wind == null ? 'unavailable' : `wind ${Math.round(a.wind)} km/h, humidity ${Math.round(a.rh)}%`))),
    el('section', {}, el('h3', {}, 'Lifecycle'), bar, life,
      d.sent ? el('p', {}, el('a', { class: 'cap-link', href: `/cap/${encodeURIComponent(a.id)}.xml`, target: '_blank', rel: 'noopener' }, icon('flag'), 'Open the CAP 1.2 alert')) : null));
}

function closeDock() {
  $('#evidence').hidden = true;
  $('#burnpanel').hidden = true;
  $('.sheet').classList.remove('is-placing');
  if (placing) { burnLayer.removeLayer(placing); placing = null; }
  S.selected = null;
  ring.remove();
  history.replaceState(null, '', location.pathname);
  render({ markers: false });
}

// ---- burn register -------------------------------------------------------------
const form = $('#burnform');
async function drawBurns() {
  try {
    const list = await (await fetch('/api/burns', { cache: 'no-store' })).json();
    burnLayer.clearLayers();
    if (placing) burnLayer.addLayer(placing);
    for (const b of list) {
      L.circle([b.lat, b.lon], { radius: b.r_km * 1000, color: INK.contour, weight: 1.4, dashArray: '5 4', fillColor: INK.contour, fillOpacity: 0.08, interactive: false }).addTo(burnLayer);
    }
  } catch { /* the register is optional on the sheet */ }
}

function openBurn() {
  $('#evidence').hidden = true;
  const panel = $('#burnpanel');
  panel.hidden = false;
  $('.sheet').classList.add('is-placing');
  const start = new Date(Math.ceil(Date.now() / 36e5) * 36e5);
  if (!form.start.value) form.start.value = start.toISOString().slice(0, 16);
  if (!form.end.value) form.end.value = new Date(+start + 6 * 36e5).toISOString().slice(0, 16);
  $('#burn-msg').textContent = '';
  form.lat.focus();
}

function previewBurn() {
  const lat = +form.lat.value, lon = +form.lon.value, r = +form.r_km.value;
  if (placing) { burnLayer.removeLayer(placing); placing = null; }
  if (!form.lat.value || !form.lon.value || !(r > 0)) return;
  placing = L.circle([lat, lon], { radius: r * 1000, color: INK.ink, weight: 1.5, dashArray: '2 4', fillOpacity: 0.05, interactive: false }).addTo(burnLayer);
}
map.on('click', e => {
  if ($('#burnpanel').hidden) return;
  form.lat.value = e.latlng.lat.toFixed(4);
  form.lon.value = e.latlng.lng.toFixed(4);
  previewBurn();
});
for (const name of ['lat', 'lon', 'r_km']) form[name].addEventListener('input', previewBurn);

form.addEventListener('submit', async e => {
  e.preventDefault();
  const msg = $('#burn-msg');
  msg.className = 'form-msg';
  if (!form.checkValidity()) { form.reportValidity(); return; }
  if (form.end.value <= form.start.value) { msg.className = 'form-msg err'; msg.textContent = 'End must be after start.'; form.end.focus(); return; }
  const btn = $('button[type=submit]', form);
  btn.disabled = true;
  try {
    const r = await fetch('/api/burns', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({
      lat: +form.lat.value, lon: +form.lon.value, r_km: +form.r_km.value, start: form.start.value, end: form.end.value, note: form.note.value }) });
    const body = await r.json();
    if (!r.ok) throw new Error(Array.isArray(body.detail) ? body.detail.map(x => x.msg.replace(/^Value error, /, '')).join('; ') : body.detail);
    msg.className = 'form-msg ok';
    msg.textContent = `${body.id} added: ${body.r_km} km round ${body.lat}, ${body.lon}, ${body.start} to ${body.end} UTC.`;
    if (placing) { burnLayer.removeLayer(placing); placing = null; }
    form.note.value = '';
    drawBurns();
  } catch (err) {
    msg.className = 'form-msg err';
    msg.textContent = `Not added: ${err.message || 'the server did not answer'}.`;
  } finally {
    btn.disabled = false;
  }
});

// ---- live polling --------------------------------------------------------------
function setStatus(kind, text) {
  const s = $('#status');
  s.classList.toggle('is-live', kind === 'live');
  s.classList.toggle('is-down', kind === 'down');
  $('#status-text').textContent = text;
}

function announce(id, text) {
  const strip = $('#live-strip');
  strip.hidden = false;
  strip.replaceChildren(el('b', {}, 'Live'), el('span', {}, `${IST_CLOCK.format(new Date())} IST · ${text}`),
    el('button', { class: 'btn', type: 'button', onclick: () => { strip.hidden = true; select(id, false); } }, 'Show'));
}

async function loadAll() {
  const r = await fetch('/api/alerts', { cache: 'no-store' });
  if (!r.ok) throw new Error(r.status);
  const j = await r.json();
  const before = new Map(S.all.filter(a => a.window !== 'live').map(a => [a.id, a.tier]));
  const live = S.all.filter(a => a.window === 'live');
  S.all = j.rows.map(row => toAlert(j.cols, row)).filter(a => a.window !== 'live').concat(live);
  S.byId = new Map(S.all.map(a => [a.id, a]));
  if (before.size) {
    const moved = S.all.filter(a => before.has(a.id) && before.get(a.id) !== a.tier);
    if (moved.length <= 50) for (const a of moved) mark(a.id, { changed: { from: before.get(a.id), to: a.tier } });
  }
  S.version = j.version;
}

async function poll() {
  try {
    const r = await fetch('/api/live', { cache: 'no-store' });
    if (!r.ok) throw new Error(r.status);
    const j = await r.json();
    let dirty = false;
    if (JSON.stringify(j.version) !== JSON.stringify(S.version)) { await loadAll(); dirty = true; drawBurns(); }
    const liveNow = new Map(j.live.map(row => { const a = toAlert(j.cols, row); return [a.id, a]; }));
    for (const [id, a] of liveNow) {
      const old = S.byId.get(id);
      if (!old) {
        S.all.push(a); S.byId.set(id, a); dirty = true;
        if (!S.baseline) { mark(id, { isNew: true }); announce(id, `new alert ${km(a.village_km)} from ${a.village_name}, ${a.tier}`); }
      } else if (old.tier !== a.tier || old.p !== a.p || old.why !== a.why) {
        if (old.tier !== a.tier && !S.baseline) { mark(id, { changed: { from: old.tier, to: a.tier } }); announce(id, `${old.tier} → ${a.tier}, ${km(a.village_km)} from ${a.village_name}`); }
        Object.assign(old, a); dirty = true;
      }
    }
    const gone = S.all.filter(a => a.window === 'live' && !liveNow.has(a.id));
    if (gone.length) { S.all = S.all.filter(a => !gone.includes(a)); for (const a of gone) S.byId.delete(a.id); dirty = true; }
    for (const [id, o] of Object.entries(j.outcomes)) {
      const prev = S.outcomes[id];
      if (!prev || prev.ts !== o.ts) {
        S.outcomes[id] = o; dirty = true;
        const a = S.byId.get(id);
        if (!S.baseline && a) announce(id, o.src === 'field' ? `field staff report ${FIELD[o.result] || o.result} near ${a.village_name}` : `camera ${o.src} reports ${o.result === 'smoke' ? 'smoke' : 'no smoke'} near ${a.village_name}`);
      }
    }
    for (const [id, ts] of Object.entries(j.sent)) {
      if (S.sent[id] !== ts) {
        S.sent[id] = ts; dirty = true;
        const a = S.byId.get(id);
        if (!S.baseline && a) announce(id, `dispatched to Range Staff: ${km(a.village_km)} from ${a.village_name}`);
      }
    }
    S.baseline = false;
    if (dirty) {
      render();
      if (S.selected && !$('#evidence').hidden) showEvidence(S.selected);
    }
    setStatus('live', `Live · checked ${IST_CLOCK.format(new Date())} IST`);
  } catch {
    setStatus('down', 'Server unreachable · retrying');
  }
  setTimeout(poll, POLL_MS);
}

// ---- controls --------------------------------------------------------------------
for (const box of document.querySelectorAll('input[name=tier]')) {
  box.addEventListener('change', () => {
    box.checked ? S.tiers.add(box.value) : S.tiers.delete(box.value);
    S.limit = PAGE;
    render();
  });
}
$('#window').addEventListener('change', e => { S.win = e.target.value; S.limit = PAGE; render(); });
let typing;
$('#q').addEventListener('input', e => { clearTimeout(typing); typing = setTimeout(() => { S.q = e.target.value; S.limit = PAGE; render(); }, 160); });
$('#more').addEventListener('click', () => { S.limit += PAGE; render(); });
$('#burn-open').addEventListener('click', openBurn);
for (const b of document.querySelectorAll('#burnpanel [data-close]')) b.addEventListener('click', closeDock);

function step(dir) {
  if (!S.list.length) return;
  const i = S.list.findIndex(a => a.id === S.selected);
  const next = S.list[Math.min(Math.max(i < 0 ? 0 : i + dir, 0), S.list.length - 1)];
  if (S.list.indexOf(next) >= S.limit) S.limit = Math.ceil((S.list.indexOf(next) + 1) / PAGE) * PAGE;
  select(next.id, false);
}
document.addEventListener('keydown', e => {
  if (e.target.closest('input, select, textarea, #map') || e.metaKey || e.ctrlKey || e.altKey) return;
  if (e.key === 'j' || e.key === 'ArrowDown') { e.preventDefault(); step(1); }
  else if (e.key === 'k' || e.key === 'ArrowUp') { e.preventDefault(); step(-1); }
  else if (e.key === 'Escape') closeDock();
});

// ---- start -----------------------------------------------------------------------
(async () => {
  try {
    await loadAll();
    render();
    drawBurns();
    const fromHash = decodeURIComponent(location.hash.slice(1));
    if (fromHash && S.byId.has(fromHash)) select(fromHash, false);
  } catch {
    $('#queue').replaceChildren(el('li', { class: 'queue-note' }, 'Could not load alerts. Start the server with: uvicorn api:app --port 8000'));
    setStatus('down', 'Server unreachable · retrying');
  }
  poll();
})();
