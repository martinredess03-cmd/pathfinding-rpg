// Frontend: dibuja el mapa y consume la API REST del backend (Python).
const $ = (id) => document.getElementById(id);
const canvas = $("map");
const NAMES = { bfs: "Anchura BFS (ciega)", dijkstra: "Costo uniforme (ciega)", greedy: "Voraz (heurística)", astar: "A* (heurística)" };
const css = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();

let state = null;      // { width, height, costs, start, goal }
let result = null;     // respuesta de /api/search
let shown = 0;         // casillas exploradas que ya se muestran en la animación
let mode = "start";
let raf = 0;

async function api(path, options) {
  const response = await fetch(path, options);
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Error en el servidor");
  return data;
}
const postJson = (path, body) =>
  api(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
const setStatus = (text) => { $("status").textContent = text; };

function draw() {
  if (!state) return;
  const w = canvas.parentElement.clientWidth - 24, dpr = window.devicePixelRatio || 1;
  const cell = w / state.width, h = cell * state.height;
  canvas.style.width = w + "px"; canvas.style.height = h + "px";
  canvas.width = w * dpr; canvas.height = h * dpr;
  const g = canvas.getContext("2d");
  g.setTransform(dpr, 0, 0, dpr, 0, 0);
  const colors = { 0: css("--water"), 1: css("--grass"), 3: css("--forest"), 6: css("--swamp") };
  const at = (i) => [(i % state.width) * cell, Math.floor(i / state.width) * cell];
  state.costs.forEach((c, i) => { g.fillStyle = colors[c]; const [x, y] = at(i); g.fillRect(x, y, cell + 0.5, cell + 0.5); });
  if (result) {
    g.fillStyle = "rgba(255,214,0,.55)";
    result.expanded_order.slice(0, shown).forEach((i) => { const [x, y] = at(i); g.fillRect(x, y, cell + 0.5, cell + 0.5); });
    if (shown >= result.expanded_order.length && result.found) {
      g.beginPath();
      result.path.forEach((i, k) => { const [x, y] = at(i); k ? g.lineTo(x + cell / 2, y + cell / 2) : g.moveTo(x + cell / 2, y + cell / 2); });
      g.strokeStyle = css("--accent"); g.lineWidth = Math.max(2, cell * 0.3); g.lineJoin = "round"; g.stroke();
    }
  }
  const [sx, sy] = at(state.start), [gx, gy] = at(state.goal);
  g.fillStyle = "#fff"; g.strokeStyle = "#1d2430"; g.lineWidth = 2;
  g.beginPath(); g.arc(sx + cell / 2, sy + cell / 2, cell * 0.4, 0, 7); g.fill(); g.stroke();
  g.fillStyle = "#f5c400"; g.fillRect(gx + cell * 0.12, gy + cell * 0.12, cell * 0.76, cell * 0.76);
  g.strokeRect(gx + cell * 0.12, gy + cell * 0.12, cell * 0.76, cell * 0.76);
}

function showStats() {
  const blank = !result;
  $("sE").textContent = blank ? "—" : Math.min(shown, result.expanded);
  $("sC").textContent = blank ? "—" : result.found ? result.cost : "Sin camino";
  $("sP").textContent = blank || !result.found ? "—" : result.steps;
  $("sT").textContent = blank ? "—" : result.elapsed_ms.toFixed(2) + " ms";
}

function animate() {
  shown += Number($("spd").value) * 2;
  if (shown >= result.expanded_order.length) shown = result.expanded_order.length;
  draw(); showStats();
  if (shown < result.expanded_order.length) raf = requestAnimationFrame(animate);
}

function reset() { cancelAnimationFrame(raf); result = null; shown = 0; draw(); showStats(); }
const problem = () => ({ width: state.width, height: state.height, costs: state.costs, start: state.start, goal: state.goal });

async function newMap() {
  try { state = await api("/api/map"); setStatus(`Mapa generado con semilla ${state.seed}.`); reset(); }
  catch (e) { setStatus("No se pudo conectar con el backend: " + e.message); }
}

async function runSearch() {
  try {
    cancelAnimationFrame(raf);
    result = await postJson("/api/search", { ...problem(), algorithm: $("alg").value });
    shown = 0; setStatus(result.found ? "" : "No existe un camino entre el inicio y el cofre."); animate();
  } catch (e) { setStatus(e.message); }
}

function table(headers, rows) {
  return "<table><tr>" + headers.map((h) => `<th>${h}</th>`).join("") + "</tr>" +
    rows.map((r) => "<tr>" + r.map((c) => `<td>${c}</td>`).join("") + "</tr>").join("") + "</table>";
}

async function compare() {
  try {
    const { results } = await postJson("/api/compare", problem());
    $("out").innerHTML = table(["Algoritmo", "Nodos expandidos", "Costo de la ruta", "Pasos"],
      results.map((r) => [NAMES[r.algorithm], r.expanded, r.found ? r.cost : "sin camino", r.found ? r.steps : "—"])) +
      '<p class="note">Resultado en el mapa actual, calculado por el backend.</p>';
  } catch (e) { setStatus(e.message); }
}

async function experiment() {
  const button = $("bExp");
  button.disabled = true; $("out").innerHTML = '<p class="note">Ejecutando en el servidor…</p>';
  try {
    const data = await api("/api/experiment?maps=200&seed=42");
    $("out").innerHTML = table(["Algoritmo", "Nodos expandidos (media)", "Costo (media)", "Ruta óptima", "Tiempo (media)"],
      data.rows.map((r) => [NAMES[r.algorithm], r.avg_expanded, r.avg_cost, r.optimal_pct + " %", r.avg_ms + " ms"])) +
      `<p class="note">Promedios en ${data.maps} mapas aleatorios (semilla ${data.seed}), inicio y meta separados al menos ${data.min_distance} casillas.</p>`;
  } catch (e) { $("out").innerHTML = ""; setStatus(e.message); }
  button.disabled = false;
}

canvas.addEventListener("click", (event) => {
  if (!state) return;
  const rect = canvas.getBoundingClientRect(), cell = rect.width / state.width;
  const x = Math.floor((event.clientX - rect.left) / cell), y = Math.floor((event.clientY - rect.top) / cell);
  if (x < 0 || x >= state.width || y < 0 || y >= state.height) return;
  const i = y * state.width + x;
  if (mode === "water") { if (i !== state.start && i !== state.goal) state.costs[i] = state.costs[i] ? 0 : 1; }
  else { if (!state.costs[i]) state.costs[i] = 1; state[mode] = i; }
  reset();
});

[["mS", "start"], ["mG", "goal"], ["mW", "water"]].forEach(([id, m]) =>
  $(id).addEventListener("click", () => { mode = m; ["mS", "mG", "mW"].forEach((x) => $(x).setAttribute("aria-pressed", x === id)); }));
$("bGo").addEventListener("click", runSearch);
$("bNew").addEventListener("click", newMap);
$("bCmp").addEventListener("click", compare);
$("bExp").addEventListener("click", experiment);
$("alg").addEventListener("change", () => { if (result) runSearch(); });
window.addEventListener("resize", draw);
newMap();
