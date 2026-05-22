from flask import Flask, jsonify, render_template_string
import requests
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import sqlite3
import os

app = Flask(__name__)

POLYGON_KEY = "09polB1VjBW9a6sQYjwZM9ucQhsBYLt1"
MT5_BRIDGE = "http://localhost:5000"
DB_PATH = "/home/x/mym_bars.db"

CT = ZoneInfo("America/Chicago")
ET = ZoneInfo("America/New_York")

# Backtest-derived best windows (from backtests 1-9)
# These are the historically profitable hour windows on trend days
HOUR_STATS = {
    8:  {"winrate": 58, "grade": "B",  "label": "Open Momentum", "color": "#f59e0b"},
    9:  {"winrate": 64, "grade": "A",  "label": "Prime Window",  "color": "#22c55e"},
    10: {"winrate": 61, "grade": "A-", "label": "Strong Window", "color": "#4ade80"},
    11: {"winrate": 55, "grade": "B+", "label": "Mid Session",   "color": "#facc15"},
    12: {"winrate": 48, "grade": "C",  "label": "Lunch Chop",    "color": "#f87171"},
    13: {"winrate": 46, "grade": "C-", "label": "Avoid",         "color": "#ef4444"},
    14: {"winrate": 52, "grade": "B-", "label": "Late Day",      "color": "#fb923c"},
    15: {"winrate": 49, "grade": "C+", "label": "Close Risk",    "color": "#f97316"},
}

def get_mt5_price():
    try:
        r = requests.get(f"{MT5_BRIDGE}/api/price", timeout=3)
        return r.json()
    except:
        return {"error": "MT5 bridge offline"}

def get_mt5_bars():
    try:
        r = requests.get(f"{MT5_BRIDGE}/api/bars", timeout=3)
        return r.json()
    except:
        return {"error": "MT5 bridge offline"}

def get_dia_context():
    try:
        # Use ET for equity market date reference
        today_et = datetime.now(tz=ET).strftime('%Y-%m-%d')
        url = (
            f"https://api.massive.com/v2/aggs/ticker/DIA/range/1/day"
            f"/2026-01-01/{today_et}"
            f"?adjusted=true&sort=desc&limit=2&apiKey={POLYGON_KEY}"
        )
        r = requests.get(url, timeout=5)
        data = r.json()
        results = data.get('results', [])
        if not results:
            return {"error": "no data"}

        d = results[0]
        # Guard against stale bar — bar date must match today ET
        bar_date = datetime.fromtimestamp(d['t'] / 1000, tz=ET).strftime('%Y-%m-%d')
        if bar_date != today_et:
            # Market hasn't opened yet today or data not posted — use prior close
            # but flag it so the dashboard can show context correctly
            pct = (d['c'] - d['o']) / d['o'] * 100
            if pct >= 0.5:
                trend, color, bias = 'TREND UP (PRIOR)', '#22c55e', 'LONG'
            elif pct <= -0.5:
                trend, color, bias = 'TREND DOWN (PRIOR)', '#ef4444', 'SHORT'
            else:
                trend, color, bias = 'RANGE DAY (PRIOR)', '#f59e0b', 'NEUTRAL'
            return {
                "date": bar_date,
                "open": d['o'], "close": d['c'],
                "high": d['h'], "low": d['l'],
                "pct": round(pct, 3),
                "trend": trend, "color": color, "bias": bias,
                "stale": True
            }

        pct = (d['c'] - d['o']) / d['o'] * 100
        if pct >= 0.5:
            trend, color, bias = 'TREND UP', '#22c55e', 'LONG'
        elif pct <= -0.5:
            trend, color, bias = 'TREND DOWN', '#ef4444', 'SHORT'
        else:
            trend, color, bias = 'RANGE DAY', '#f59e0b', 'NEUTRAL'
        return {
            "date": today_et,
            "open": d['o'], "close": d['c'],
            "high": d['h'], "low": d['l'],
            "pct": round(pct, 3),
            "trend": trend, "color": color, "bias": bias,
            "stale": False
        }
    except Exception as e:
        return {"error": str(e)}

def get_vix():
    try:
        today_et = datetime.now(tz=ET).strftime('%Y-%m-%d')
        url = (
            f"https://api.massive.com/v2/aggs/ticker/I:VIX/range/1/day"
            f"/2026-01-01/{today_et}"
            f"?adjusted=true&sort=desc&limit=1&apiKey={POLYGON_KEY}"
        )
        r = requests.get(url, timeout=5)
        data = r.json()
        results = data.get('results', [])
        if results:
            v = results[0]
            level = "LOW" if v['c'] < 15 else "ELEVATED" if v['c'] < 25 else "HIGH"
            return {"vix": round(v['c'], 2), "vix_open": round(v['o'], 2), "level": level}
    except:
        pass
    return {"error": "no vix"}

def get_current_window():
    # Always compute CT hour from system clock via zoneinfo — no manual offset math
    now_ct = datetime.now(tz=CT)
    hour = now_ct.hour
    stats = HOUR_STATS.get(hour, {
        "winrate": 0, "grade": "—",
        "label": "Outside Primary Hours", "color": "#6b7280"
    })
    return {
        "ct_hour": hour,
        "stats": stats,
        "time": now_ct.strftime('%H:%M:%S CT')
    }

@app.route('/api/all')
def api_all():
    price = get_mt5_price()
    bars  = get_mt5_bars()
    dia   = get_dia_context()
    vix   = get_vix()
    window = get_current_window()
    return jsonify({
        "price": price,
        "bars": bars,
        "dia": dia,
        "vix": vix,
        "window": window,
        "hour_stats": HOUR_STATS
    })

@app.route('/api/price')
def api_price():
    return jsonify(get_mt5_price())

@app.route('/api/bars')
def api_bars():
    return jsonify(get_mt5_bars())

@app.route('/api/context')
def api_context():
    return jsonify(get_dia_context())

@app.route('/')
def index():
    return render_template_string(DASHBOARD_HTML)

DASHBOARD_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CURRICKULUS // MARKET</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@300;400;600;700&display=swap" rel="stylesheet">
<style>
  :root {
    --bg: #030712;
    --bg2: #0a0f1e;
    --bg3: #0f172a;
    --border: #1e293b;
    --accent: #00d4ff;
    --accent2: #7c3aed;
    --green: #22c55e;
    --red: #ef4444;
    --yellow: #f59e0b;
    --text: #e2e8f0;
    --muted: #475569;
    --mono: 'Share Tech Mono', monospace;
    --sans: 'Rajdhani', sans-serif;
  }

  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: var(--sans);
    min-height: 100vh;
    overflow-x: hidden;
  }

  /* Scanline effect */
  body::before {
    content: '';
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: repeating-linear-gradient(
      0deg,
      transparent,
      transparent 2px,
      rgba(0,0,0,0.03) 2px,
      rgba(0,0,0,0.03) 4px
    );
    pointer-events: none;
    z-index: 1000;
  }

  header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 32px;
    border-bottom: 1px solid var(--border);
    background: var(--bg2);
  }

  .logo {
    font-family: var(--mono);
    font-size: 18px;
    color: var(--accent);
    letter-spacing: 4px;
    text-transform: uppercase;
  }

  .logo span { color: var(--muted); }

  #clock {
    font-family: var(--mono);
    font-size: 24px;
    color: var(--accent);
    letter-spacing: 2px;
  }

  #connection-status {
    font-family: var(--mono);
    font-size: 11px;
    padding: 4px 12px;
    border-radius: 2px;
    letter-spacing: 2px;
  }

  .connected    { background: rgba(34,197,94,0.15);  color: var(--green); border: 1px solid var(--green); }
  .disconnected { background: rgba(239,68,68,0.15);  color: var(--red);   border: 1px solid var(--red);   }

  .grid {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    grid-template-rows: auto auto;
    gap: 1px;
    background: var(--border);
    margin: 1px;
  }

  .card {
    background: var(--bg2);
    padding: 24px;
    position: relative;
    overflow: hidden;
  }

  .card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--accent), transparent);
    opacity: 0.3;
  }

  .card-label {
    font-family: var(--mono);
    font-size: 10px;
    color: var(--muted);
    letter-spacing: 3px;
    text-transform: uppercase;
    margin-bottom: 12px;
  }

  /* PRICE CARD */
  .price-card { grid-column: 1; }

  #live-price {
    font-family: var(--mono);
    font-size: 56px;
    font-weight: bold;
    color: var(--accent);
    line-height: 1;
    letter-spacing: -1px;
  }

  #price-change {
    font-family: var(--mono);
    font-size: 18px;
    margin-top: 8px;
  }

  #bid-ask {
    font-family: var(--mono);
    font-size: 13px;
    color: var(--muted);
    margin-top: 8px;
  }

  /* BIAS CARD */
  .bias-card { grid-column: 2; }

  #bias-display {
    font-family: var(--mono);
    font-size: 42px;
    font-weight: 700;
    letter-spacing: 4px;
    line-height: 1;
  }

  #dia-info {
    font-family: var(--mono);
    font-size: 12px;
    color: var(--muted);
    margin-top: 12px;
    line-height: 1.8;
  }

  /* WINDOW CARD */
  .window-card { grid-column: 3; }

  #window-grade {
    font-family: var(--mono);
    font-size: 64px;
    font-weight: 700;
    line-height: 1;
    color: var(--accent);
  }

  #window-label {
    font-size: 20px;
    font-weight: 600;
    color: var(--text);
    margin-top: 4px;
    letter-spacing: 2px;
    text-transform: uppercase;
  }

  #window-winrate {
    font-family: var(--mono);
    font-size: 13px;
    color: var(--muted);
    margin-top: 8px;
  }

  /* CHART CARD */
  .chart-card {
    grid-column: 1 / 3;
    padding: 0;
  }

  #chart-container {
    width: 100%;
    height: 320px;
    position: relative;
  }

  canvas#chart {
    width: 100%;
    height: 100%;
  }

  /* HOURS CARD */
  .hours-card { grid-column: 3; }

  .hour-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 6px 0;
    border-bottom: 1px solid rgba(30,41,59,0.5);
    font-family: var(--mono);
    font-size: 12px;
  }

  .hour-row:last-child { border-bottom: none; }

  .hour-time  { color: var(--muted); width: 60px; }
  .hour-grade { font-weight: bold; width: 30px; text-align: center; }
  .hour-label { flex: 1; padding: 0 8px; }
  .hour-wr    { color: var(--muted); }

  .hour-bar {
    height: 3px;
    border-radius: 1px;
    margin-top: 2px;
    transition: width 0.5s ease;
  }

  /* VIX */
  #vix-display {
    font-family: var(--mono);
    font-size: 36px;
    color: var(--yellow);
  }

  #vix-level {
    font-family: var(--mono);
    font-size: 12px;
    margin-top: 4px;
  }

  /* SIGNAL */
  #signal-box {
    margin-top: 16px;
    padding: 12px 16px;
    border-radius: 2px;
    font-family: var(--mono);
    font-size: 13px;
    letter-spacing: 1px;
  }

  .signal-long    { background: rgba(34,197,94,0.1);  border: 1px solid var(--green); color: var(--green); }
  .signal-short   { background: rgba(239,68,68,0.1);  border: 1px solid var(--red);   color: var(--red);   }
  .signal-neutral { background: rgba(107,114,128,0.1);border: 1px solid var(--muted); color: var(--muted); }

  #last-updated {
    font-family: var(--mono);
    font-size: 10px;
    color: var(--muted);
    text-align: center;
    padding: 8px;
    border-top: 1px solid var(--border);
  }

  .up   { color: var(--green); }
  .down { color: var(--red);   }
  .flat { color: var(--muted); }

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0.4; }
  }

  .live-dot {
    display: inline-block;
    width: 6px; height: 6px;
    border-radius: 50%;
    background: var(--green);
    animation: pulse 2s infinite;
    margin-right: 6px;
  }
</style>
</head>
<body>

<header>
  <div class="logo">CURRICKULUS <span>//</span> MARKET INTELLIGENCE</div>
  <div id="clock">--:--:--</div>
  <div id="connection-status" class="disconnected">&#9679; OFFLINE</div>
</header>

<div class="grid">

  <!-- LIVE PRICE -->
  <div class="card price-card">
    <div class="card-label"><span class="live-dot"></span>MYM LIVE PRICE</div>
    <div id="live-price">------</div>
    <div id="price-change" class="flat">-- ticks</div>
    <div id="bid-ask">BID: ------ | ASK: ------</div>
    <div id="signal-box" class="signal-neutral">AWAITING DATA...</div>
  </div>

  <!-- DAY BIAS -->
  <div class="card bias-card">
    <div class="card-label">DAY BIAS // DIA</div>
    <div id="bias-display" style="color: var(--muted)">------</div>
    <div id="dia-info">Loading context...</div>
  </div>

  <!-- CURRENT WINDOW -->
  <div class="card window-card">
    <div class="card-label">CURRENT TRADING WINDOW</div>
    <div id="window-grade">-</div>
    <div id="window-label">Loading...</div>
    <div id="window-winrate">Historical win rate: --%</div>
    <br>
    <div class="card-label">VOLATILITY // VIX</div>
    <div id="vix-display">--.-</div>
    <div id="vix-level" class="flat">Loading...</div>
  </div>

  <!-- CHART -->
  <div class="card chart-card">
    <canvas id="chart"></canvas>
  </div>

  <!-- HOUR BREAKDOWN -->
  <div class="card hours-card">
    <div class="card-label">HISTORICAL WINDOW PERFORMANCE</div>
    <div id="hours-grid"></div>
  </div>

</div>

<div id="last-updated">Last updated: --</div>

<script>
let prevPrice = null;
let barData = [];

const HOUR_STATS = {
  8:  {winrate: 58, grade: "B",  label: "Open Momentum", color: "#f59e0b"},
  9:  {winrate: 64, grade: "A",  label: "Prime Window",  color: "#22c55e"},
  10: {winrate: 61, grade: "A-", label: "Strong Window", color: "#4ade80"},
  11: {winrate: 55, grade: "B+", label: "Mid Session",   color: "#facc15"},
  12: {winrate: 48, grade: "C",  label: "Lunch Chop",    color: "#f87171"},
  13: {winrate: 46, grade: "C-", label: "Avoid",         color: "#ef4444"},
  14: {winrate: 52, grade: "B-", label: "Late Day",      color: "#fb923c"},
  15: {winrate: 49, grade: "C+", label: "Close Risk",    color: "#f97316"},
};

function buildHoursGrid() {
  const container = document.getElementById('hours-grid');
  // Get current CT hour from server-supplied data, fall back to JS estimate
  const ctHour = window._lastCtHour !== undefined ? window._lastCtHour : null;
  let html = '';
  for (const [h, s] of Object.entries(HOUR_STATS)) {
    const active = ctHour !== null && parseInt(h) === ctHour
      ? 'style="background:rgba(0,212,255,0.05);"' : '';
    html += `<div class="hour-row" ${active}>
      <span class="hour-time">${h}:00 CT</span>
      <span class="hour-grade" style="color:${s.color}">${s.grade}</span>
      <span class="hour-label" style="color:${s.color}">${s.label}</span>
      <span class="hour-wr">${s.winrate}%</span>
    </div>
    <div class="hour-bar" style="width:${s.winrate}%;background:${s.color};opacity:0.4"></div>`;
  }
  container.innerHTML = html;
}

function drawChart(bars) {
  const canvas = document.getElementById('chart');
  const ctx = canvas.getContext('2d');
  canvas.width  = canvas.offsetWidth;
  canvas.height = canvas.offsetHeight;

  if (!bars || bars.length === 0) return;

  const prices = bars.map(b => b.c);
  const min = Math.min(...prices) - 20;
  const max = Math.max(...prices) + 20;
  const range = max - min;
  const w = canvas.width, h = canvas.height, pad = 40;
  const chartW = w - pad * 2, chartH = h - pad * 2;

  ctx.clearRect(0, 0, w, h);

  // Grid lines
  ctx.strokeStyle = 'rgba(30,41,59,0.8)';
  ctx.lineWidth = 1;
  for (let i = 0; i <= 4; i++) {
    const y = pad + (chartH / 4) * i;
    ctx.beginPath(); ctx.moveTo(pad, y); ctx.lineTo(w - pad, y); ctx.stroke();
    const price = max - (range / 4) * i;
    ctx.fillStyle = '#475569';
    ctx.font = '10px Share Tech Mono';
    ctx.fillText(Math.round(price), 2, y + 4);
  }

  // Price line + fill
  const gradient = ctx.createLinearGradient(0, pad, 0, h - pad);
  gradient.addColorStop(0, 'rgba(0,212,255,0.8)');
  gradient.addColorStop(1, 'rgba(0,212,255,0)');

  ctx.beginPath();
  bars.forEach((b, i) => {
    const x = pad + (i / (bars.length - 1)) * chartW;
    const y = pad + ((max - b.c) / range) * chartH;
    i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
  });
  ctx.strokeStyle = '#00d4ff';
  ctx.lineWidth = 2;
  ctx.stroke();

  ctx.lineTo(pad + chartW, h - pad);
  ctx.lineTo(pad, h - pad);
  ctx.closePath();
  ctx.fillStyle = gradient;
  ctx.globalAlpha = 0.15;
  ctx.fill();
  ctx.globalAlpha = 1;

  // Current price dot
  const last = bars[bars.length - 1];
  const lx = pad + chartW;
  const ly = pad + ((max - last.c) / range) * chartH;
  ctx.beginPath();
  ctx.arc(lx, ly, 4, 0, Math.PI * 2);
  ctx.fillStyle = '#00d4ff';
  ctx.fill();
}

async function update() {
  try {
    const res  = await fetch('/market/api/all');
    const data = await res.json();

    // Connection status
    const statusEl = document.getElementById('connection-status');
    if (!data.price.error) {
      statusEl.className   = 'connected';
      statusEl.textContent = '● LIVE';
    } else {
      statusEl.className   = 'disconnected';
      statusEl.textContent = '● OFFLINE';
    }

    // Price
    if (!data.price.error) {
      const price   = data.price.last;
      const priceEl = document.getElementById('live-price');
      priceEl.textContent = Math.round(price).toLocaleString();

      if (prevPrice !== null) {
        const diff     = price - prevPrice;
        const changeEl = document.getElementById('price-change');
        if (diff > 0) {
          changeEl.textContent = `▲ +${diff.toFixed(0)} ticks`;
          changeEl.className   = 'up';
          priceEl.style.color  = '#22c55e';
        } else if (diff < 0) {
          changeEl.textContent = `▼ ${diff.toFixed(0)} ticks`;
          changeEl.className   = 'down';
          priceEl.style.color  = '#ef4444';
        } else {
          priceEl.style.color = 'var(--accent)';
        }
      }
      prevPrice = price;

      document.getElementById('bid-ask').textContent =
        `BID: ${Math.round(data.price.bid).toLocaleString()} | ASK: ${Math.round(data.price.ask).toLocaleString()}`;
    }

    // DIA Bias
    if (!data.dia.error) {
      const d = data.dia;
      document.getElementById('bias-display').textContent  = d.trend;
      document.getElementById('bias-display').style.color  = d.color;
      const staleNote = d.stale ? '<br><span style="color:#475569;font-size:10px">PRIOR SESSION</span>' : '';
      document.getElementById('dia-info').innerHTML =
        `DIA: ${d.open?.toFixed(2)} → ${d.close?.toFixed(2)}<br>` +
        `Move: ${d.pct > 0 ? '+' : ''}${d.pct?.toFixed(2)}%<br>` +
        `Bias: <span style="color:${d.color}">${d.bias}</span>${staleNote}`;

      // Signal box
      const signalEl = document.getElementById('signal-box');
      if (d.bias === 'LONG') {
        signalEl.className   = 'signal-long';
        signalEl.textContent = '▲ TREND DAY — FAVOR LONGS';
      } else if (d.bias === 'SHORT') {
        signalEl.className   = 'signal-short';
        signalEl.textContent = '▼ TREND DAY — FAVOR SHORTS';
      } else {
        signalEl.className   = 'signal-neutral';
        signalEl.textContent = '◆ RANGE DAY — REDUCE SIZE';
      }
    }

    // Window — use CT hour from server (already correct via zoneinfo)
    const w = data.window;
    window._lastCtHour = w.ct_hour;
    const stats = HOUR_STATS[w.ct_hour] || {winrate: 0, grade: '—', label: 'Outside Primary Hours', color: '#6b7280'};
    document.getElementById('window-grade').textContent   = stats.grade;
    document.getElementById('window-grade').style.color   = stats.color;
    document.getElementById('window-label').textContent   = stats.label;
    document.getElementById('window-label').style.color   = stats.color;
    document.getElementById('window-winrate').textContent = `Historical win rate: ${stats.winrate || '--'}%`;

    // VIX
    if (!data.vix.error) {
      document.getElementById('vix-display').textContent = data.vix.vix;
      const vixLevel = document.getElementById('vix-level');
      vixLevel.textContent = data.vix.level;
      vixLevel.className   = data.vix.level === 'LOW' ? 'up' : data.vix.level === 'HIGH' ? 'down' : 'flat';
    }

    // Chart
    if (!data.bars.error && data.bars.bars) {
      barData = data.bars.bars;
      drawChart(barData);
    }

    document.getElementById('last-updated').textContent =
      `Last updated: ${new Date().toLocaleTimeString()} | CT: ${w.time}`;

    buildHoursGrid();

  } catch(e) {
    document.getElementById('connection-status').className   = 'disconnected';
    document.getElementById('connection-status').textContent = '● ERROR';
  }
}

// Clock
function updateClock() {
  document.getElementById('clock').textContent = new Date().toLocaleTimeString();
}

// Init
buildHoursGrid();
update();
setInterval(update, 5000);
setInterval(updateClock, 1000);
window.addEventListener('resize', () => drawChart(barData));
</script>
</body>
</html>'''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)
