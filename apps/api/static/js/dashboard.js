/* AIZIX Trading OS — paper venue UI client */

let lastPrice = null;
let tapeReturns = [];
let chartAnchoredPair = null;
let audioCtx = null;

let requireAuth =
  document.querySelector('meta[name="aizix-require-auth"]')?.getAttribute("content") === "true";
let authToken = localStorage.getItem("aizix_token");

async function refreshAuthFlags() {
  try {
    const h = await fetch("/api/health").then((r) => r.json());
    if (typeof h.require_auth === "boolean") requireAuth = h.require_auth;
  } catch {
    /* ignore */
  }
}

function authHeaders() {
  const h = { "Content-Type": "application/json" };
  if (authToken) h.Authorization = `Bearer ${authToken}`;
  return h;
}

function paintAuthUi() {
  const out = document.getElementById("auth-out");
  const inn = document.getElementById("auth-in");
  const label = document.getElementById("auth-label");
  if (!out || !inn || !label) return;
  const has = !!authToken;
  out.style.display = has ? "inline-block" : "none";
  inn.style.display = has ? "none" : "inline";
  label.textContent = has ? "Authenticated" : requireAuth ? "Sign in required" : "Demo session";
}

async function api(path, opts = {}) {
  const r = await fetch(path, {
    headers: { ...authHeaders(), ...(opts.headers || {}) },
    ...opts,
  });
  if (r.status === 401 && requireAuth) {
    window.location.href = "/login";
    throw new Error("Unauthorized");
  }
  if (!r.ok) throw new Error(`${path} ${r.status}`);
  return r.json();
}

function fmtUsd(n) {
  if (n == null || Number.isNaN(n)) return "—";
  return Number(n).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function fmtTime(iso) {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString(undefined, { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  } catch {
    return iso;
  }
}

const BT_OBJECTIVE_LABELS = {
  return_over_drawdown: "Return ÷ max drawdown",
  total_return: "Total return",
  profit_factor: "Profit factor",
};

function getBacktestObjectiveSelect() {
  return document.getElementById("bt-objective")?.value || "return_over_drawdown";
}

function fmtBacktestPct(n) {
  if (n == null || Number.isNaN(Number(n))) return "—";
  return `${Number(n).toFixed(2)}%`;
}

function fmtBacktestPf(n) {
  if (n == null || Number.isNaN(Number(n))) return "—";
  return Number(n).toFixed(2);
}

function fmtBacktestSlTp(n) {
  if (n == null || Number.isNaN(Number(n))) return "—";
  return `${Number(n).toFixed(1)}%`;
}

function renderBacktestSummaryPanel(data) {
  const empty = document.getElementById("bt-summary-empty");
  const content = document.getElementById("bt-summary-content");
  const subtitle = document.getElementById("bt-summary-subtitle");
  const objectiveEl = document.getElementById("bt-summary-objective");
  const grid = document.getElementById("bt-summary-metrics");
  const note = document.getElementById("bt-summary-note");
  if (!empty || !content || !objectiveEl || !grid || !note) return;

  const objRaw = data.optimization_objective ?? data.objective ?? "return_over_drawdown";
  const objLabel = BT_OBJECTIVE_LABELS[objRaw] || objRaw;

  empty.hidden = true;
  content.hidden = false;

  if (subtitle) {
    if (data.subtitle) {
      subtitle.textContent = data.subtitle;
      subtitle.removeAttribute("hidden");
    } else {
      subtitle.textContent = "";
      subtitle.setAttribute("hidden", "");
    }
  }

  objectiveEl.textContent = `Objective: ${objLabel}`;

  if (data.missing) {
    grid.innerHTML =
      '<p class="muted tiny" style="grid-column: 1 / -1; margin:0">No results to display for this comparison.</p>';
    note.textContent = data.note || "";
    return;
  }

  const mk = (label, value) =>
    `<article class="card metric"><span class="metric-label">${label}</span><span class="metric-value mono">${value}</span></article>`;

  grid.innerHTML = [
    mk("Best SL (optimized)", fmtBacktestSlTp(data.recommended_sl_pct)),
    mk("Best TP (optimized)", fmtBacktestSlTp(data.recommended_tp_pct)),
    mk("Win rate", fmtBacktestPct(data.win_rate_pct)),
    mk("Profit factor", fmtBacktestPf(data.profit_factor)),
    mk("Max drawdown", fmtBacktestPct(data.max_drawdown_pct)),
    mk("Total return", fmtBacktestPct(data.total_return_pct)),
  ].join("");

  note.textContent = data.note || "";
}

function ensureAudio() {
  if (!document.getElementById("sound-on")?.checked) return null;
  try {
    audioCtx = audioCtx || new (window.AudioContext || window.webkitAudioContext)();
    return audioCtx;
  } catch {
    return null;
  }
}

function playTone(freq, dur = 0.06, gain = 0.03) {
  const ctx = ensureAudio();
  if (!ctx) return;
  const o = ctx.createOscillator();
  const g = ctx.createGain();
  o.type = "sine";
  o.frequency.value = freq;
  g.gain.value = gain;
  o.connect(g);
  g.connect(ctx.destination);
  const t = ctx.currentTime;
  o.start(t);
  o.stop(t + dur);
}

function perfScopeLabel(scope) {
  if (scope === "persisted_sql") return "Source: persisted trades";
  if (scope === "session_memory") return "Source: session memory";
  if (scope === "empty") return "No closed trades";
  return scope || "—";
}

function paintPerfEquity(values) {
  const svg = document.getElementById("perf-equity-svg");
  if (!svg) return;
  const curve = Array.isArray(values) && values.length ? values : [];
  if (curve.length < 2) {
    svg.innerHTML = `<line class="equity-path" x1="0" y1="60" x2="400" y2="60" stroke-dasharray="4 4" stroke-opacity="0.35" />
      <text x="14" y="64" fill="#64748b" font-size="10" font-family="ui-monospace,monospace">Flat until two or more closed legs</text>`;
    return;
  }
  let pts = curve;
  const cap = 500;
  if (pts.length > cap) {
    const step = (pts.length - 1) / (cap - 1);
    const out = [];
    for (let j = 0; j < cap; j++) {
      const idx = Math.min(pts.length - 1, Math.round(j * step));
      out.push(pts[idx]);
    }
    pts = out;
  }
  const min = Math.min(...pts);
  const max = Math.max(...pts);
  const span = max - min || 1;
  const poly = pts.map((y, i) => {
    const x = (i / (pts.length - 1 || 1)) * 400;
    const yy = 110 - ((y - min) / span) * 100;
    return `${x.toFixed(1)},${yy.toFixed(1)}`;
  });
  svg.innerHTML = `<polyline class="equity-path" points="${poly.join(" ")}" />`;
}

function renderPerfTrades(rows) {
  const tb = document.getElementById("perf-tbody-trades");
  if (!tb) return;
  tb.innerHTML = "";
  (rows || []).forEach((t) => {
    const tr = document.createElement("tr");
    const cls = t.pnl_usd >= 0 ? "tag-long" : "tag-short";
    tr.innerHTML = `
      <td class="muted tiny">${fmtTime(t.time)}</td>
      <td class="mono">${t.symbol}</td>
      <td class="mono">${t.side}</td>
      <td class="mono">${Number(t.entry).toFixed(4)}</td>
      <td class="mono">${Number(t.exit).toFixed(4)}</td>
      <td class="mono ${cls}">${fmtUsd(t.pnl_usd)}</td>
      <td class="mono">${t.confidence_pct != null ? `${Number(t.confidence_pct).toFixed(1)}%` : "—"}</td>
      <td class="mono">${t.risk_level ?? "—"}</td>`;
    const tdReason = document.createElement("td");
    tdReason.className = "muted tiny perf-reason";
    tdReason.title = t.reason || "";
    tdReason.textContent = t.reason || "—";
    tr.appendChild(tdReason);
    tb.appendChild(tr);
  });
}

function renderPerfDaily(rows) {
  const tb = document.getElementById("perf-tbody-daily");
  if (!tb) return;
  tb.innerHTML = "";
  (rows || []).forEach((d) => {
    const tr = document.createElement("tr");
    const cls = d.net_pnl_usd >= 0 ? "tag-long" : "tag-short";
    tr.innerHTML = `
      <td class="mono">${d.date}</td>
      <td class="mono">${d.trades}</td>
      <td class="mono">${d.wins}</td>
      <td class="mono">${d.losses}</td>
      <td class="mono ${cls}">${fmtUsd(d.net_pnl_usd)}</td>
      <td class="mono">${Number(d.drawdown_pct ?? 0).toFixed(2)}%</td>`;
    tb.appendChild(tr);
  });
}

async function refreshPerformance() {
  const perf = await api("/api/performance");
  const elDisc = document.getElementById("perf-disclaimer");
  if (elDisc && perf.disclaimer) elDisc.textContent = perf.disclaimer;
  const scopeEl = document.getElementById("perf-scope");
  if (scopeEl) scopeEl.textContent = `${perfScopeLabel(perf.data_scope)} · schema ${perf.schema_version ?? 1}`;

  const m = perf.metrics || {};
  const set = (id, v) => {
    const n = document.getElementById(id);
    if (n) n.textContent = v;
  };
  set("perf-m-trades", String(m.total_trades ?? "—"));
  set("perf-m-winrate", m.win_rate_pct != null ? `${Number(m.win_rate_pct).toFixed(2)}%` : "—");
  set("perf-m-pf", m.profit_factor != null ? String(m.profit_factor) : "—");
  set("perf-m-dd", `${Number(m.max_drawdown_pct ?? 0).toFixed(2)}%`);
  set("perf-m-avgret", m.average_trade_return_pct != null ? `${Number(m.average_trade_return_pct).toFixed(2)}%` : "—");
  set("perf-m-best", m.best_trade_usd != null ? fmtUsd(m.best_trade_usd) : "—");
  set("perf-m-worst", m.worst_trade_usd != null ? fmtUsd(m.worst_trade_usd) : "—");
  set("perf-m-daily", fmtUsd(m.daily_pnl_usd));
  const sub = document.getElementById("perf-m-session");
  if (sub) sub.textContent = `Session book accum.: ${fmtUsd(m.session_paper_accum_usd)}`;
  set("perf-m-total", fmtUsd(m.total_pnl_usd));

  const eq = perf.equity?.values || [];
  const startEl = document.getElementById("perf-equity-start");
  if (startEl) startEl.textContent = `Starting ${fmtUsd(perf.equity?.starting_equity_usd)}`;
  paintPerfEquity(eq);

  renderPerfTrades(perf.trades || []);
  renderPerfDaily(perf.daily || []);
}

function bindViews() {
  document.querySelectorAll(".nav-link").forEach((btn) => {
    btn.addEventListener("click", () => {
      const v = btn.dataset.view;
      document.querySelectorAll(".nav-link").forEach((b) => b.classList.toggle("active", b === btn));
      document.querySelectorAll(".view").forEach((el) => el.classList.toggle("active", el.id === `view-${v}`));
      if (v === "performance") refreshPerformance().catch(() => {});
    });
  });
}

function bindTf() {
  document.querySelectorAll(".tf").forEach((b) => {
    b.addEventListener("click", () => {
      document.querySelectorAll(".tf").forEach((x) => x.classList.remove("active"));
      b.classList.add("active");
    });
  });
}

async function postPrefs(payload) {
  await api("/api/dashboard/preferences", { method: "POST", body: JSON.stringify(payload) });
}

function pushPrefs() {
  postPrefs({
    risk_level: +document.getElementById("risk-level").value,
    capital_usage_pct: +document.getElementById("capital-usage").value,
    max_daily_loss_pct: +document.getElementById("max-daily-loss").value,
    pair: document.getElementById("sel-pair").value,
    strategy: document.getElementById("sel-strategy").value,
    sl_pct: +document.getElementById("inp-sl").value,
    tp_pct: +document.getElementById("inp-tp").value,
    trail_pct: +document.getElementById("inp-trail").value,
    confidence_threshold: +document.getElementById("conf-thresh").value,
    sound_on: document.getElementById("sound-on").checked,
    compounding_enabled: document.getElementById("compound-on").checked,
    speed: +document.getElementById("poll-speed").value,
  }).then(() => refreshPortfolio());
}

function wirePrefsInputs() {
  const ids = [
    "risk-level",
    "capital-usage",
    "max-daily-loss",
    "sel-pair",
    "sel-strategy",
    "inp-sl",
    "inp-tp",
    "inp-trail",
    "conf-thresh",
    "compound-on",
    "poll-speed",
    "sound-on",
  ];
  ids.forEach((id) => {
    const el = document.getElementById(id);
    if (!el) return;
    el.addEventListener("change", pushPrefs);
    el.addEventListener("input", () => {
      if (id === "risk-level") document.getElementById("risk-val").textContent = el.value;
      if (id === "capital-usage") document.getElementById("capital-val").textContent = `${el.value}%`;
      if (id === "max-daily-loss") document.getElementById("max-loss-val").textContent = `${el.value}%`;
      if (id === "conf-thresh") document.getElementById("conf-val").textContent = el.value;
    });
  });
}

function initChart(n = 28) {
  const host = document.getElementById("chart-candles");
  const vol = document.getElementById("chart-volume");
  if (!host || host.children.length) return;
  tapeReturns = [];
  for (let i = 0; i < n; i++) {
    const col = document.createElement("div");
    col.className = "candle-col";
    const body = document.createElement("div");
    body.className = "candle-body flat";
    body.style.height = "45%";
    col.appendChild(body);
    host.appendChild(col);
    const vb = document.createElement("div");
    vb.className = "vol-bar";
    vb.style.height = "28%";
    vol.appendChild(vb);
  }
}

/** Candle heights derive from observed price returns between polls — no decorative motion. */
function pushTapeReturn(prevPx, px) {
  if (px == null || prevPx == null || prevPx <= 0) return;
  const cols = document.querySelectorAll("#chart-candles .candle-body").length || 28;
  tapeReturns.push(((px - prevPx) / prevPx) * 100);
  while (tapeReturns.length > cols) tapeReturns.shift();
}

function syncChartToTape(market) {
  const bodies = document.querySelectorAll("#chart-candles .candle-body");
  const vols = document.querySelectorAll("#chart-volume .vol-bar");
  const C = bodies.length;
  if (!C) return;

  const volNorm = Math.min(1, ((market?.volatility_annualized_pct ?? 40) / 100));
  const L = tapeReturns.length;

  bodies.forEach((el, i) => {
    const idx = L >= C ? L - C + i : i;
    const rr = idx >= 0 && idx < L ? tapeReturns[idx] : null;
    if (rr == null) {
      el.style.height = "45%";
      el.classList.remove("up", "down");
      el.classList.add("flat");
      return;
    }
    const h = Math.max(18, Math.min(82, 46 + rr * 14));
    el.style.height = `${h}%`;
    el.classList.remove("flat");
    el.classList.toggle("up", rr >= 0);
    el.classList.toggle("down", rr < 0);
  });

  vols.forEach((el, i) => {
    const idx = L >= C ? L - C + i : i;
    const rr = idx >= 0 && idx < L ? tapeReturns[idx] : null;
    if (rr == null) {
      el.style.height = `${Math.round(22 + volNorm * 28)}%`;
      return;
    }
    const mag = Math.abs(rr);
    const h = Math.max(14, Math.min(92, 22 + mag * 42 + volNorm * 28));
    el.style.height = `${h}%`;
  });
}

function renderPositions(tbId, rows, showClose) {
  const tb = document.getElementById(tbId);
  if (!tb) return;
  tb.innerHTML = "";
  (rows || []).forEach((p) => {
    const tr = document.createElement("tr");
    const typCls = p.type === "Long" || p.side === "BUY" ? "tag-long" : "tag-short";
    const pnl = p.pnl_usd ?? 0;
    const pnlCls = pnl >= 0 ? "tag-long" : "tag-short";
    const badge = p.stop_badge === "TRAIL" ? "badge-stop badge-trail" : "badge-stop";
    const core = `
      <td class="mono">${p.pair}</td>
      <td class="mono ${typCls}">${p.type || p.side}</td>
      <td class="mono">${p.size ?? p.qty}</td>
      <td class="mono">${Number(p.entry).toFixed(4)}</td>
      <td class="mono">${p.current_price != null ? Number(p.current_price).toFixed(4) : "—"}</td>
      <td class="mono ${pnlCls}">${fmtUsd(pnl)}</td>
      <td class="mono ${pnlCls}">${p.pnl_pct != null ? `${pnl >= 0 ? "+" : ""}${Number(p.pnl_pct).toFixed(2)}%` : "—"}</td>
      <td><span class="${badge}">${p.stop_badge}</span></td>`;
    tr.innerHTML = showClose
      ? `${core}<td><button type="button" class="btn btn-ghost btn-xs" data-close="${p.id}">Close</button></td>`
      : core;
    tb.appendChild(tr);
  });
  if (showClose) {
    tb.querySelectorAll("[data-close]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        await api("/api/paper-trade/close", {
          method: "POST",
          body: JSON.stringify({ position_id: btn.getAttribute("data-close") }),
        });
        playTone(440);
        refreshPortfolio();
      });
    });
  }
}

function renderTrades(rows) {
  const tb = document.getElementById("tbody-trades");
  if (!tb) return;
  tb.innerHTML = "";
  [...(rows || [])].reverse().forEach((t) => {
    const tr = document.createElement("tr");
    const cls = t.pnl_usd >= 0 ? "tag-long" : "tag-short";
    tr.innerHTML = `
      <td class="muted tiny">${fmtTime(t.closed_at)}</td>
      <td class="mono">${t.symbol}</td>
      <td class="mono">${t.side}</td>
      <td class="mono ${cls}">${fmtUsd(t.pnl_usd)}</td>
      <td class="mono ${cls}">${Number(t.pnl_pct).toFixed(2)}%</td>`;
    tb.appendChild(tr);
  });
}

function renderSignalHist(rows) {
  const tb = document.getElementById("tbody-signals");
  if (!tb) return;
  tb.innerHTML = "";
  [...(rows || [])].reverse().slice(0, 40).forEach((s) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td class="muted tiny">${fmtTime(s.as_of)}</td>
      <td class="mono">${s.pair}</td>
      <td class="mono">${s.action}</td>
      <td class="mono">${s.confidence_pct?.toFixed(1)}%</td>
      <td class="mono">${s.risk_score?.toFixed(0) ?? "—"}</td>`;
    tb.appendChild(tr);
  });
}

function renderMarkets(m) {
  const tb = document.getElementById("tbody-markets");
  if (!tb || !m.prices) return;
  tb.innerHTML = "";
  Object.entries(m.prices).forEach(([pair, px]) => {
    const mom = m.momentum_pct_by_pair?.[pair];
    const tr = document.createElement("tr");
    const momCls = mom >= 0 ? "tag-long" : "tag-short";
    tr.innerHTML = `
      <td class="mono">${pair}</td>
      <td class="mono">${Number(px).toFixed(4)}</td>
      <td class="mono ${momCls}">${mom != null ? `${mom >= 0 ? "+" : ""}${mom.toFixed(3)}%` : "—"}</td>
      <td class="muted tiny">${m.trend} tape</td>`;
    tb.appendChild(tr);
  });
}

function renderAllSignals(signals) {
  const tb = document.getElementById("tbody-all-signals");
  if (!tb) return;
  tb.innerHTML = "";
  (signals || []).forEach((s) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td class="mono">${s.pair}</td>
      <td class="mono">${s.action}</td>
      <td class="mono">${Number(s.confidence_pct).toFixed(1)}%</td>
      <td class="mono">${s.risk_score?.toFixed(1) ?? "—"}</td>
      <td class="mono">${s.risk_level ?? "—"}</td>
      <td class="muted tiny">${s.reason || ""}</td>`;
    tb.appendChild(tr);
  });
}

function aiSuggested(ai) {
  if (!ai) return "Observe.";
  if (ai.action === "HOLD") return "No new risk — maintain discipline.";
  if (ai.action === "BUY") return "Consider incremental long sleeve entry within limits.";
  return "Consider trimming or hedging sleeve exposure.";
}

function paintAi(ai) {
  document.getElementById("ai-action").textContent = ai?.action ?? "—";
  document.getElementById("ai-conf").textContent = ai ? `${Number(ai.confidence_pct).toFixed(1)}%` : "—";
  document.getElementById("ai-risk").textContent = ai ? `${ai.risk_level ?? ""} (${Number(ai.risk_score ?? 0).toFixed(0)})` : "—";
  document.getElementById("ai-reason").textContent = ai?.reason ?? "Awaiting signal refresh.";
  document.getElementById("ai-stance").textContent = ai?.stance ?? "";
  document.getElementById("ai-suggested").textContent = aiSuggested(ai);
  const bar = document.getElementById("ai-bar");
  if (bar) bar.style.width = ai ? `${Math.min(100, ai.confidence_pct)}%` : "0%";
}

async function refreshPortfolio() {
  const d = await api("/api/portfolio");
  document.getElementById("hdr-balance").textContent = fmtUsd(d.balance_usd);
  document.getElementById("m-portfolio").textContent = fmtUsd(d.portfolio_value_usd);
  document.getElementById("m-daily").textContent = fmtUsd(d.daily_profit_usd);
  document.getElementById("m-winrate").textContent = `${d.win_rate_pct ?? "—"}%`;
  document.getElementById("m-dd").textContent = `${Number(d.drawdown_pct ?? 0).toFixed(2)}%`;
  document.getElementById("m-exposure").textContent = `${Number(d.risk_exposure_pct ?? 0).toFixed(1)}%`;

  document.getElementById("p-portfolio").textContent = fmtUsd(d.portfolio_value_usd);
  document.getElementById("p-win").textContent = `${d.win_rate_pct ?? "—"}%`;
  document.getElementById("p-dd").textContent = `${Number(d.drawdown_pct ?? 0).toFixed(2)}%`;

  document.getElementById("bot-status-pill").textContent = `Engine ${d.bot_status}`;
  document.getElementById("sel-pair").value = d.selected_pair || document.getElementById("sel-pair").value;
  document.getElementById("sel-strategy").value = d.strategy || document.getElementById("sel-strategy").value;
  document.getElementById("risk-level").value = d.risk_level;
  document.getElementById("risk-val").textContent = String(d.risk_level);
  document.getElementById("capital-usage").value = d.capital_usage_pct ?? 68;
  document.getElementById("capital-val").textContent = `${Math.round(d.capital_usage_pct ?? 68)}%`;
  document.getElementById("max-daily-loss").value = d.max_daily_loss_pct ?? 5;
  document.getElementById("max-loss-val").textContent = `${Number(d.max_daily_loss_pct ?? 5).toFixed(1)}%`;
  document.getElementById("inp-sl").value = d.sl_pct;
  document.getElementById("inp-tp").value = d.tp_pct;
  document.getElementById("inp-trail").value = d.trail_pct;
  document.getElementById("conf-thresh").value = d.confidence_threshold;
  document.getElementById("conf-val").textContent = String(d.confidence_threshold);
  document.getElementById("compound-on").checked = d.compounding_enabled;
  document.getElementById("poll-speed").value = d.speed ?? 1;
  document.getElementById("sound-on").checked = d.sound_on;

  paintAi(d.primary_ai);

  renderPositions("tbody-positions", d.positions, true);
  renderPositions("tbody-portfolio-pos", d.positions, false);
  renderTrades(d.recent_trades);
  renderSignalHist(d.signal_history);

  document.getElementById("risk-json").textContent = JSON.stringify(d.risk_controller, null, 2);

  const comp = await api("/api/compounding").catch(() => null);
  if (comp) {
    document.getElementById("w-trading").textContent = fmtUsd(comp.trading_balance);
    document.getElementById("w-safe").textContent = fmtUsd(comp.safety_balance);
    const tr = comp.compounding_enabled ? Math.round((comp.trading_balance / (comp.total || 1)) * 100) : 100;
    document.getElementById("split-a").textContent = String(tr);
    document.getElementById("split-b").textContent = String(100 - tr);
  }

  if (document.getElementById("view-performance")?.classList.contains("active")) {
    refreshPerformance().catch(() => {});
  }
}

async function refreshMarket() {
  const m = await api("/api/market");
  const pair = document.getElementById("sel-pair").value;
  if (chartAnchoredPair !== pair) {
    chartAnchoredPair = pair;
    tapeReturns = [];
    lastPrice = null;
  }
  document.getElementById("chart-pair").textContent = pair;
  const px = m.prices?.[pair];
  const el = document.getElementById("chart-price");
  const chg = document.getElementById("chart-chg");
  const prevPx = lastPrice;
  if (px != null && el) {
    el.textContent = Number(px).toFixed(4);
    if (prevPx != null && chg) {
      const d = ((px - prevPx) / prevPx) * 100;
      chg.textContent = `${d >= 0 ? "+" : ""}${d.toFixed(2)}%`;
      chg.style.color = d >= 0 ? "var(--secondary)" : "var(--danger)";
    }
    pushTapeReturn(prevPx, px);
    lastPrice = px;
  }
  syncChartToTape(m);
  renderMarkets(m);
}

async function refreshSignals() {
  const s = await api("/api/signals");
  renderAllSignals(s.signals || []);
}

async function ping() {
  try {
    await api("/api/health");
    document.getElementById("health-dot").classList.remove("off");
    document.getElementById("health-label").textContent = "API operational";
  } catch {
    document.getElementById("health-dot").classList.add("off");
    document.getElementById("health-label").textContent = "API degraded";
  }
}

async function botPost(path, freq) {
  playTone(freq);
  await api(path, { method: "POST", body: "{}" });
  await refreshPortfolio();
}

function wireBot() {
  document.getElementById("btn-start").addEventListener("click", () => botPost("/api/bot/start", 523));
  document.getElementById("btn-pause").addEventListener("click", () => botPost("/api/bot/pause", 392));
  document.getElementById("btn-stop").addEventListener("click", () => botPost("/api/bot/stop", 196));
  document.getElementById("btn-emergency").addEventListener("click", () => botPost("/api/bot/emergency-stop", 880));

  document.getElementById("btn-paper-exec").addEventListener("click", async () => {
    await api("/api/paper-trade/execute", {
      method: "POST",
      body: JSON.stringify({
        symbol: document.getElementById("sel-pair").value,
        side: "buy",
        qty: 100,
        confidence_pct: +document.getElementById("conf-thresh").value + 8,
      }),
    });
    playTone(660);
    await refreshPortfolio();
  });
  document.getElementById("btn-close-all").addEventListener("click", async () => {
    await api("/api/paper-trade/close-all", { method: "POST", body: "{}" });
    playTone(330);
    await refreshPortfolio();
  });

  document.getElementById("btn-bt-run").addEventListener("click", async () => {
    const res = await api("/api/backtest/run", {
      method: "POST",
      body: JSON.stringify({
        pair: document.getElementById("bt-pair").value,
        sl_pct: +document.getElementById("bt-sl").value,
        tp_pct: +document.getElementById("bt-tp").value,
        days: +document.getElementById("bt-days").value,
        source: document.getElementById("bt-source")?.value || "binance",
        optimization_objective: getBacktestObjectiveSelect(),
      }),
    });
    renderBacktestSummaryPanel({
      optimization_objective: res.optimization_objective,
      total_return_pct: res.total_return_pct,
      max_drawdown_pct: res.max_drawdown_pct,
      win_rate_pct: res.win_rate_pct,
      profit_factor: res.profit_factor,
      recommended_sl_pct: res.recommended_sl_pct,
      recommended_tp_pct: res.recommended_tp_pct,
      note: res.note || "",
    });
    const curve = res.equity_curve || [];
    const svg = document.getElementById("equity-svg");
    if (!curve.length || !svg) return;
    const min = Math.min(...curve);
    const max = Math.max(...curve);
    const span = max - min || 1;
    const pts = curve.map((y, i) => {
      const x = (i / (curve.length - 1 || 1)) * 400;
      const yy = 110 - ((y - min) / span) * 100;
      return `${x.toFixed(1)},${yy.toFixed(1)}`;
    });
    svg.innerHTML = `<polyline class="equity-path" points="${pts.join(" ")}" />`;
  });

  const cmp = document.getElementById("btn-bt-compare");
  if (cmp) {
    cmp.addEventListener("click", async () => {
      const days = +document.getElementById("bt-days").value;
      const source = document.getElementById("bt-source")?.value || "binance";
      const optimization_objective = getBacktestObjectiveSelect();
      const res = await api("/api/backtest/compare", {
        method: "POST",
        body: JSON.stringify({
          days,
          source,
          optimization_objective,
          configs: [
            { label: "BTC sleeve", pair: "BTC3L/USDT", sl_pct: 2, tp_pct: 4 },
            { label: "ETH sleeve", pair: "ETH3L/USDT", sl_pct: 2, tp_pct: 5 },
            { label: "SOL sleeve", pair: "SOL3L/USDT", sl_pct: 2.5, tp_pct: 6 },
          ],
        }),
      });
      const best = res.best;
      if (best) {
        renderBacktestSummaryPanel({
          objective: res.objective ?? optimization_objective,
          subtitle: `Best sleeve · ${best.label}`,
          total_return_pct: best.total_return_pct,
          max_drawdown_pct: best.max_drawdown_pct,
          win_rate_pct: best.win_rate_pct,
          profit_factor: best.profit_factor,
          recommended_sl_pct: best.recommended_sl_pct,
          recommended_tp_pct: best.recommended_tp_pct,
          note: `Compared ${res.results?.length ?? 0} configurations over ${res.days ?? days} days.`,
        });
      } else {
        renderBacktestSummaryPanel({
          objective: res.objective ?? optimization_objective,
          missing: true,
          note: "Compare finished with no ranked result — check data source or network.",
        });
      }
      const svg = document.getElementById("equity-svg");
      const curve = best?.equity_curve || [];
      if (!curve.length || !svg) return;
      const min = Math.min(...curve);
      const max = Math.max(...curve);
      const span = max - min || 1;
      const pts = curve.map((y, i) => {
        const x = (i / (curve.length - 1 || 1)) * 400;
        const yy = 110 - ((y - min) / span) * 100;
        return `${x.toFixed(1)},${yy.toFixed(1)}`;
      });
      svg.innerHTML = `<polyline class="equity-path" points="${pts.join(" ")}" />`;
    });
  }
}

async function refreshStrategies() {
  const sel = document.getElementById("saved-strategies");
  const status = document.getElementById("strategy-status");
  if (!sel) return;
  try {
    const rows = await api("/api/strategies");
    sel.innerHTML = "";
    rows.forEach((r) => {
      const o = document.createElement("option");
      o.value = String(r.id);
      o.textContent = `${r.name} · SL ${r.sl_pct}% / TP ${r.tp_pct}%`;
      sel.appendChild(o);
    });
    if (status) status.textContent = rows.length ? `${rows.length} saved strategy(ies).` : "No saved strategies yet.";
  } catch {
    if (status) status.textContent = "Could not load strategies (auth?).";
  }
}

function wireStrategies() {
  const saveBtn = document.getElementById("btn-strategy-save");
  const applyBtn = document.getElementById("btn-strategy-apply");
  const nameEl = document.getElementById("strategy-save-name");
  const sel = document.getElementById("saved-strategies");
  const status = document.getElementById("strategy-status");
  if (saveBtn && nameEl) {
    saveBtn.addEventListener("click", async () => {
      const name = nameEl.value.trim() || "My strategy";
      await api("/api/dashboard/save-strategy", {
        method: "POST",
        body: JSON.stringify({ name }),
      });
      if (status) status.textContent = `Saved “${name}”.`;
      await refreshStrategies();
    });
  }
  if (applyBtn && sel) {
    applyBtn.addEventListener("click", async () => {
      const id = sel.value;
      if (!id) return;
      await api(`/api/strategies/${id}/apply`, { method: "POST", body: "{}" });
      if (status) status.textContent = `Applied strategy #${id}.`;
      await refreshPortfolio();
    });
  }
}

async function loop() {
  const sp = +(document.getElementById("poll-speed")?.value || 1);
  const ms = Math.round(4000 / sp);
  try {
    await ping();
    await refreshSignals();
    await refreshPortfolio();
    await refreshMarket();
  } catch (e) {
    console.warn(e);
  }
  setTimeout(loop, ms);
}

document.addEventListener("DOMContentLoaded", () => {
  initChart();
  bindViews();
  bindTf();
  wirePrefsInputs();
  wireBot();
  wireStrategies();
  document.getElementById("auth-out")?.addEventListener("click", () => {
    localStorage.removeItem("aizix_token");
    authToken = null;
    paintAuthUi();
    window.location.reload();
  });
  refreshAuthFlags()
    .then(() => {
      paintAuthUi();
      return refreshStrategies();
    })
    .then(() => refreshSignals())
    .then(() => refreshPortfolio())
    .then(() => refreshMarket())
    .then(() => loop());
});
