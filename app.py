import streamlit as st
import time
from datetime import datetime
import random
import math

st.set_page_config(page_title="WMS HMI Demo (TS-aligned)", layout="wide")

# =========================
# UI / CSS
# =========================
st.markdown("""
<style>
/* Background */
[data-testid="stAppViewContainer"]{
  background: radial-gradient(1200px 600px at 30% 10%, #0f1b2d 0%, #070b14 55%, #050812 100%);
}
[data-testid="stSidebar"] { background: #0b1220; }
header, footer { visibility: hidden; }

html, body, [class*="css"] { color: #e5e7eb; }
small { color: #94a3b8; }

/* Card */
.hmi-card{
  background: rgba(11,18,32,0.92);
  border: 1px solid #1f2a3a;
  border-radius: 18px;
  padding: 14px 16px;
  box-shadow: 0 10px 28px rgba(0,0,0,0.35);
}
.hmi-title{
  font-weight: 900;
  font-size: 16px;
  margin-bottom: 10px;
  display:flex; align-items:center; gap:8px;
}
.hmi-sub{ color:#94a3b8; font-size:12px; margin-top:-6px; margin-bottom:10px; }

/* Pill */
.hmi-pill{
  display:inline-block;
  padding:6px 10px;
  border-radius:999px;
  border:1px solid #223049;
  background:#0b1220;
  color:#cbd5e1;
  font-size:12px;
  font-weight:800;
}
.hmi-ok{ color:#34d399; border-color:#1e3a32; }
.hmi-warn{ color:#fbbf24; border-color:#3a2f1e; }
.hmi-bad{ color:#fb7185; border-color:#3a1e28; }

/* Row */
.hmi-row{
  display:flex; justify-content:space-between; gap:10px;
  padding:10px 12px;
  border-radius:14px;
  border:1px solid #223049;
  background:#0b1220;
  margin: 6px 0;
}
.hmi-row .k{ color:#94a3b8; font-size:12px; font-weight:800; }
.hmi-row .v{ font-size:16px; font-weight:900; }

/* Gate tiles (overview) */
.gate-tile{
  background: rgba(11,18,32,0.92);
  border: 1px solid #223049;
  border-radius: 18px;
  padding: 12px 12px;
  box-shadow: 0 10px 28px rgba(0,0,0,0.25);
}
.gate-tile.sel{
  border-color: #60a5fa;
  box-shadow: 0 10px 34px rgba(59,130,246,0.25);
}
.gate-name{ font-weight: 900; font-size: 14px; margin-bottom: 6px; }
.gate-mini{ color:#94a3b8; font-size: 12px; margin-bottom: 10px; }

/* Simple bar */
.bar-wrap{ height: 10px; border-radius: 999px; background:#0a1020; border:1px solid #223049; overflow:hidden; }
.bar-fill{ height: 100%; border-radius: 999px; background: linear-gradient(90deg, #0ea5e9, #2563eb); }

/* Diverging bar (Plan in center) */
.div-wrap{
  position: relative;
  height: 14px;
  border-radius: 999px;
  background:#0a1020;
  border:1px solid #223049;
  overflow:hidden;
}
.div-center{
  position:absolute;
  left:50%;
  top:-2px;
  width:2px;
  height:18px;
  background:#94a3b8;
  opacity:0.8;
}
.div-fill-pos{
  position:absolute;
  left:50%;
  top:0;
  height:100%;
  background: linear-gradient(90deg, #34d399, #0ea5e9);
}
.div-fill-neg{
  position:absolute;
  right:50%;
  top:0;
  height:100%;
  background: linear-gradient(90deg, #fb7185, #f59e0b);
}
.div-scale{
  display:flex;
  justify-content:space-between;
  color:#94a3b8;
  font-size:11px;
  margin-top:4px;
}
</style>
""", unsafe_allow_html=True)

# =========================
# Helpers
# =========================
def card_start(title: str, subtitle: str | None = None, icon: str = "◼"):
    st.markdown(f"""
<div class="hmi-card">
  <div class="hmi-title">{icon} {title}</div>
  {"<div class='hmi-sub'>"+subtitle+"</div>" if subtitle else ""}
""", unsafe_allow_html=True)

def card_end():
    st.markdown("</div>", unsafe_allow_html=True)

def pill(label: str, klass="hmi-pill"):
    st.markdown(f"<span class='{klass}'>{label}</span>", unsafe_allow_html=True)

def row(key: str, val: str, badge_text: str | None = None, badge_class="hmi-ok"):
    b = f"<span class='hmi-pill {badge_class}' style='margin-left:10px;'>{badge_text}</span>" if badge_text else ""
    st.markdown(f"""
<div class="hmi-row">
  <div class="k">{key}</div>
  <div class="v">{val}{b}</div>
</div>
""", unsafe_allow_html=True)

def cctv_box(title="CCTV"):
    st.markdown(
        f"""
<div style="height:220px;border-radius:14px;border:1px solid #223049;background:#050a14;
display:flex;align-items:center;justify-content:center;">
  <div style="text-align:center;color:#94a3b8;">
    <div style="font-weight:900;margin-bottom:6px;">{title}</div>
    <div style="font-size:12px;">(Video placeholder)</div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

def gate_svg(open_pct: int, opening_m: float):
    """
    NOTE: SVG内の「Opening xx%」「Opening x.xx m」の2行テキストは削除（ユーザー指示）。
    """
    y = 120 - int(open_pct * 0.8)
    y = max(40, min(120, y))
    return f"""
<svg width="100%" viewBox="0 0 520 260" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="water" x1="0" x2="0" y1="0" y2="1">
      <stop offset="0" stop-color="#0ea5e9" stop-opacity="0.92"/>
      <stop offset="1" stop-color="#2563eb" stop-opacity="0.72"/>
    </linearGradient>
    <filter id="sh" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="6" stdDeviation="8" flood-color="#000" flood-opacity="0.35"/>
    </filter>
  </defs>

  <rect x="22" y="20" width="476" height="220" rx="18" fill="#0b1220" stroke="#223049"/>

  <rect x="150" y="40" width="46" height="170" rx="10" fill="#111c2e" stroke="#223049"/>
  <rect x="324" y="40" width="46" height="170" rx="10" fill="#111c2e" stroke="#223049"/>

  <rect x="80" y="170" width="360" height="44" rx="12" fill="#0a1020" stroke="#223049"/>
  <rect x="92" y="182" width="336" height="30" rx="10" fill="url(#water)" opacity="0.95"/>

  <rect x="220" y="62" width="80" height="140" rx="10" fill="#0a1020" stroke="#223049"/>

  <g filter="url(#sh)">
    <rect x="226" y="{y}" width="68" height="90" rx="10" fill="#1f6feb" opacity="0.92" stroke="#60a5fa"/>
    <path d="M232 {y+18} H288" stroke="#93c5fd" stroke-width="3" opacity="0.75"/>
    <path d="M232 {y+36} H288" stroke="#93c5fd" stroke-width="3" opacity="0.55"/>
    <path d="M232 {y+54} H288" stroke="#93c5fd" stroke-width="3" opacity="0.40"/>
  </g>
</svg>
"""

def bar(percent: int):
    p = max(0, min(100, int(percent)))
    st.markdown(f"<div class='bar-wrap'><div class='bar-fill' style='width:{p}%;'></div></div>", unsafe_allow_html=True)

def pct_delta(plan: float, actual: float):
    if plan == 0:
        return 0.0
    return (actual - plan) / plan * 100.0

def dev_badge(abs_pct: float) -> str:
    if abs_pct <= 2.0:
        return "hmi-ok"
    if abs_pct <= 5.0:
        return "hmi-warn"
    return "hmi-bad"

def diverging_bar(dev_pct: float, scale_pct: float = 10.0):
    """
    Diverging bar centered on target (Plan).
    dev_pct: (Actual-Plan)/Plan*100
    scale_pct: +/- scale_pct corresponds to full half-width.
    """
    d = max(-scale_pct, min(scale_pct, dev_pct))
    half = abs(d) / scale_pct * 50.0  # 0..50
    if d >= 0:
        st.markdown(f"""
<div class="div-wrap">
  <div class="div-center"></div>
  <div class="div-fill-pos" style="width:{half}%;"></div>
</div>
""", unsafe_allow_html=True)
    else:
        st.markdown(f"""
<div class="div-wrap">
  <div class="div-center"></div>
  <div class="div-fill-neg" style="width:{half}%;"></div>
</div>
""", unsafe_allow_html=True)

    st.markdown(f"""
<div class="div-scale">
  <div>-{scale_pct:.0f}%</div>
  <div>0%</div>
  <div>+{scale_pct:.0f}%</div>
</div>
""", unsafe_allow_html=True)

# =========================
# Data model (dummy)
# Station -> Canal -> Gates
# =========================
def build_demo_assets():
    return {
        "BBT15": {
            "BaratMainGate": ["Gate1", "Gate2", "Gate3", "Gate4"],
            "WastewayGate": ["Gate1", "Gate2", "Gate3"],
            "CiberangMainGate": ["Gate1", "Gate2"],
        },
        "BUT10": {
            "UtaraMainGate": ["Gate1", "Gate2", "Gate3", "Gate4"],
            "WaruGate": ["Gate1", "Gate2"],
        }
    }

ASSETS = build_demo_assets()

def init_state():
    ss = st.session_state

    if "station" not in ss: ss.station = "BBT15"
    if "canal" not in ss: ss.canal = "BaratMainGate"
    if "mode" not in ss: ss.mode = "REMOTE AUTOMATIC"
    if "selected_gate" not in ss: ss.selected_gate = "Gate1"

    if "remote_enabled" not in ss: ss.remote_enabled = True
    if "comm_main" not in ss: ss.comm_main = "NORMAL"
    if "comm_backup" not in ss: ss.comm_backup = "STANDBY"

    if "commercial_power" not in ss: ss.commercial_power = True
    if "gen_state" not in ss: ss.gen_state = "OFF"

    if "prot" not in ss:
        ss.prot = {
            "ELR": False,
            "Overload": False,
            "Over Torque Open": False,
            "Over Torque Close": False,
            "Control De-Energize": False,
        }

    if "q_plan" not in ss: ss.q_plan = 12.50
    if "h_plan" not in ss: ss.h_plan = 1.65
    if "q_actual" not in ss: ss.q_actual = 12.72
    if "h_actual" not in ss: ss.h_actual = 1.63

    if "pattern" not in ss: ss.pattern = "C"
    if "season" not in ss: ss.season = "Dry"

    if "control_cycle" not in ss: ss.control_cycle = "STOPPED"  # RUNNING/PAUSED/STOPPED
    if "trend_large" not in ss: ss.trend_large = False

    if "gate_state" not in ss:
        gs = {}
        for stn, canals in ASSETS.items():
            for c, gates in canals.items():
                for g in gates:
                    key = f"{stn}/{c}/{g}"
                    open_pct = random.choice([0, 10, 25, 40, 55, 70, 85])
                    max_open_m = random.choice([2.00, 1.80, 1.60])
                    gs[key] = {
                        "open_pct": open_pct,
                        "max_open_m": max_open_m,
                        "motion": "STOP",
                        "fully_open": open_pct >= 100,
                        "fully_close": open_pct <= 0,
                        "last_cmd": "—",
                        "last_cmd_time": "—",
                    }
        ss.gate_state = gs

    if "trend_gate" not in ss:
        ss.trend_gate = [random.randint(0, 100) for _ in range(120)]
        ss.trend_q = [round(ss.q_actual + 0.12*math.sin(i/12) + random.uniform(-0.05,0.05), 2) for i in range(120)]

init_state()

# =========================
# Logic helpers
# =========================
def current_gate_key():
    ss = st.session_state
    return f"{ss.station}/{ss.canal}/{ss.selected_gate}"

def get_gate():
    return st.session_state.gate_state[current_gate_key()]

def blocked():
    ss = st.session_state
    if ss.mode == "LOCAL (LCP ACTIVE)":
        return True
    if any(ss.prot.values()):
        return True
    if ss.gen_state == "ERROR":
        return True
    if not ss.remote_enabled:
        return True
    return False

def send_cmd(cmd: str):
    now = datetime.now().strftime("%H:%M:%S")
    gg = get_gate()
    gg["last_cmd"] = cmd
    gg["last_cmd_time"] = now

def step_gate_toward(target_pct: int):
    gg = get_gate()
    p = gg["open_pct"]
    if p < target_pct:
        p = min(100, p + 2)
        gg["motion"] = "OPENING"
    elif p > target_pct:
        p = max(0, p - 2)
        gg["motion"] = "CLOSING"
    else:
        gg["motion"] = "STOP"

    gg["open_pct"] = p
    gg["fully_open"] = (p >= 100)
    gg["fully_close"] = (p <= 0)

def opening_m_from_pct(open_pct: int, max_open_m: float):
    return round(max_open_m * (open_pct / 100.0), 2)

def compute_h_plan_from_qplan(q_plan: float):
    return round(1.10 + 0.06 * (q_plan - 10.0), 2)

def tick_signals():
    ss = st.session_state
    ss.h_plan = compute_h_plan_from_qplan(ss.q_plan)

    drift = 0.02 if ss.control_cycle == "RUNNING" else 0.00
    ss.q_actual = round(max(0.0, ss.q_actual + random.uniform(-0.05, 0.05) - (ss.q_actual - ss.q_plan)*drift), 2)

    gg = get_gate()
    open_pct = gg["open_pct"]
    base_h = ss.h_plan + (open_pct - 50) * 0.002
    ss.h_actual = round(base_h + random.uniform(-0.02, 0.02), 2)

    ss.trend_gate = (ss.trend_gate + [open_pct])[-120:]
    ss.trend_q = (ss.trend_q + [ss.q_actual])[-120:]

tick_signals()

# =========================
# Sidebar
# =========================
st.sidebar.markdown("## WMS HMI Demo")

stations = list(ASSETS.keys())
st.sidebar.selectbox("Station", stations, key="station")

canals = list(ASSETS[st.session_state.station].keys())
if st.session_state.canal not in canals:
    st.session_state.canal = canals[0]
st.sidebar.selectbox("Canal / ほうろ", canals, key="canal")

st.sidebar.markdown("---")
st.sidebar.radio(
    "Control Mode Screen",
    ["LOCAL (LCP ACTIVE)", "REMOTE MANUAL", "REMOTE AUTOMATIC", "REMOTE PROGRAM"],
    key="mode"
)

st.sidebar.markdown("---")
st.sidebar.markdown("### Comms / Access (dummy)")
st.session_state.remote_enabled = st.sidebar.checkbox("Remote enabled", value=st.session_state.remote_enabled)
st.session_state.comm_main = st.sidebar.selectbox("Main comm", ["NORMAL", "DOWN"], index=["NORMAL","DOWN"].index(st.session_state.comm_main))
st.session_state.comm_backup = st.sidebar.selectbox("Backup comm", ["STANDBY", "ACTIVE", "DOWN"], index=["STANDBY","ACTIVE","DOWN"].index(st.session_state.comm_backup))

st.sidebar.markdown("### Generator / Power")
st.session_state.commercial_power = st.sidebar.checkbox("Commercial power", value=st.session_state.commercial_power)
st.session_state.gen_state = st.sidebar.selectbox(
    "Generator state", ["OFF","READY","RUNNING","ERROR"],
    index=["OFF","READY","RUNNING","ERROR"].index(st.session_state.gen_state)
)

st.sidebar.markdown("### Protection / Alarms")
for k in list(st.session_state.prot.keys()):
    st.session_state.prot[k] = st.sidebar.checkbox(k, value=st.session_state.prot[k])

st.sidebar.markdown("### Plan (dummy)")
st.session_state.q_plan = round(st.sidebar.slider("Q_plan (target) [m³/s]", 5.0, 20.0, float(st.session_state.q_plan), 0.05), 2)

st.sidebar.markdown("---")
auto_refresh = st.sidebar.checkbox("Auto refresh (1s)", value=False)

# =========================
# Header
# =========================
mode = st.session_state.mode
is_blocked = blocked()

st.markdown(f"### {st.session_state.station}  ›  {st.session_state.canal}")
h1, h2, h3, h4 = st.columns([1.3, 1.3, 1.2, 1.2])
with h1:
    pill(
        f"MODE: {('AUTO' if mode=='REMOTE AUTOMATIC' else 'PROGRAM' if mode=='REMOTE PROGRAM' else 'MANUAL' if mode=='REMOTE MANUAL' else 'LOCAL')}",
        "hmi-pill hmi-ok" if mode != "LOCAL (LCP ACTIVE)" else "hmi-pill hmi-bad"
    )
with h2:
    pill(f"COMM: MAIN={st.session_state.comm_main} / BK={st.session_state.comm_backup}",
         "hmi-pill hmi-ok" if st.session_state.comm_main=="NORMAL" else "hmi-pill hmi-warn")
with h3:
    pill(f"GEN: {st.session_state.gen_state}", "hmi-pill hmi-ok" if st.session_state.gen_state != "ERROR" else "hmi-pill hmi-bad")
with h4:
    pill(f"LAST UPDATE: {datetime.now().strftime('%H:%M:%S')}", "hmi-pill")

st.markdown("")

# =========================
# Gate overview row
# =========================
gates = ASSETS[st.session_state.station][st.session_state.canal]
if st.session_state.selected_gate not in gates:
    st.session_state.selected_gate = gates[0]

card_start("Gate Overview", "Selected canal gates aligned horizontally for quick situational awareness", "🗺️")
cols = st.columns(len(gates), gap="large")

for i, gname in enumerate(gates):
    with cols[i]:
        key = f"{st.session_state.station}/{st.session_state.canal}/{gname}"
        gs = st.session_state.gate_state[key]
        open_pct = gs["open_pct"]
        open_m = opening_m_from_pct(open_pct, gs["max_open_m"])

        sel = (gname == st.session_state.selected_gate)
        st.markdown(f"<div class='gate-tile {'sel' if sel else ''}'>", unsafe_allow_html=True)
        st.markdown(f"<div class='gate-name'>🚪 {gname}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='gate-mini'>Motion: {gs['motion']} • Alarm: {'YES' if any(st.session_state.prot.values()) else 'NO'}</div>", unsafe_allow_html=True)

        bar(open_pct)
        st.markdown(f"<div class='gate-mini'>% {open_pct}  •  m {open_m:.2f}</div>", unsafe_allow_html=True)

        if st.button("Open detail", key=f"sel_{gname}", use_container_width=True):
            st.session_state.selected_gate = gname
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

card_end()
st.markdown("")

# =========================
# Detail area
# =========================
g = get_gate()
opening_pct = g["open_pct"]
opening_m = opening_m_from_pct(opening_pct, g["max_open_m"])

def panel_gate_status():
    # Gate Status: 2本バーに数値を並記（2つ前の方式に戻す）
    card_start(f"Gate Status — {st.session_state.selected_gate}",
               "Schematic only (Opening text in SVG removed). Bars show values (%, m).", "🚪")
    st.markdown(gate_svg(opening_pct, opening_m), unsafe_allow_html=True)

    # Bar 1: Opening %
    row("Opening (Percent)", f"{opening_pct}%")
    bar(opening_pct)

    # Bar 2: Opening m (as percent of max)
    meter_percent = int(round((opening_m / g["max_open_m"]) * 100)) if g["max_open_m"] > 0 else 0
    row("Opening (Meters)", f"{opening_m:.2f} m  (max {g['max_open_m']:.2f} m)")
    bar(meter_percent)

    row("Motion", g["motion"])
    row("Fully Open", "YES" if g["fully_open"] else "NO")
    row("Fully Close", "YES" if g["fully_close"] else "NO")
    row("Last Command", g["last_cmd"], f"@ {g['last_cmd_time']}" if g["last_cmd_time"] != "—" else None, "hmi-pill")
    card_end()

def panel_plan_actual():
    # Control Targets: 直前の方式（中央に目標、左右に不足/超過）
    ss = st.session_state

    dq = ss.q_actual - ss.q_plan
    pq = pct_delta(ss.q_plan, ss.q_actual)

    dh = ss.h_actual - ss.h_plan
    ph = pct_delta(ss.h_plan, ss.h_actual)

    card_start("Control Targets (Plan vs Actual)",
               "Plan is centered; Actual deviation is shown as shortage/excess (dummy).", "🎯")

    # Q
    row("Q_plan (target)", f"{ss.q_plan:.2f} m³/s")
    row("Q_actual", f"{ss.q_actual:.2f} m³/s", f"Δ {dq:+.2f} ({pq:+.1f}%)", dev_badge(abs(pq)))
    diverging_bar(pq, scale_pct=10.0)

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

    # H
    row("H_plan (target)", f"{ss.h_plan:.2f} m")
    row("H_actual", f"{ss.h_actual:.2f} m", f"Δ {dh:+.2f} ({ph:+.1f}%)", dev_badge(abs(ph)))
    diverging_bar(ph, scale_pct=10.0)

    card_end()

def panel_auto_control():
    card_start("Automatic Control", "Start / Pause / Stop. Start applies one dummy cycle while running.", "🤖")

    b1, b2, b3 = st.columns(3, gap="large")
    with b1:
        if st.button("▶ Start", use_container_width=True, disabled=is_blocked):
            st.session_state.control_cycle = "RUNNING"
            send_cmd("AUTO START")
            pseudo_target_pct = int(max(0, min(100, 20 + st.session_state.h_plan * 30)))
            step_gate_toward(pseudo_target_pct)

    with b2:
        if st.button("⏸ Pause", use_container_width=True):
            st.session_state.control_cycle = "PAUSED"
            send_cmd("AUTO PAUSE")
            g["motion"] = "STOP"

    with b3:
        if st.button("⏹ Stop", use_container_width=True):
            st.session_state.control_cycle = "STOPPED"
            send_cmd("AUTO STOP")
            g["motion"] = "STOP"

    row("Control state", st.session_state.control_cycle,
        None,
        "hmi-ok" if st.session_state.control_cycle=="RUNNING"
        else "hmi-warn" if st.session_state.control_cycle=="PAUSED"
        else "hmi-bad"
    )
    card_end()

def panel_manual_command():
    card_start("Manual Command", "Direct control (Open / Stop / Close).", "🕹️")
    pill("BLOCKED" if is_blocked else "READY", "hmi-pill hmi-bad" if is_blocked else "hmi-pill hmi-ok")
    b1, b2, b3 = st.columns(3, gap="large")
    with b1:
        if st.button("⬆ Open", use_container_width=True, disabled=is_blocked):
            send_cmd("OPEN")
            step_gate_toward(100)
    with b2:
        if st.button("■ Stop", use_container_width=True, disabled=is_blocked):
            send_cmd("STOP")
            g["motion"] = "STOP"
    with b3:
        if st.button("⬇ Close", use_container_width=True, disabled=is_blocked):
            send_cmd("CLOSE")
            step_gate_toward(0)
    card_end()

def panel_program_control():
    card_start("Program Control", "Pattern/Season selection (dummy).", "🧩")
    row("Pattern", st.session_state.pattern)
    row("Season", st.session_state.season)
    row("Control state", st.session_state.control_cycle, None, "hmi-pill")
    card_end()

def panel_alarms():
    card_start("Protection / Alarms", "Interlocks must be visible in any control mode (dummy)", "🛡️")
    if any(st.session_state.prot.values()):
        pill("ACTIVE ALARM / TRIP PRESENT", "hmi-pill hmi-bad")
    else:
        pill("NO ACTIVE TRIP", "hmi-pill hmi-ok")
    for k, v in st.session_state.prot.items():
        row(k, "ON" if v else "OFF", None, "hmi-bad" if v else "hmi-ok")
    card_end()

def panel_power():
    card_start("Power / Generator", "Power source status (dummy)", "⚡")
    row("Commercial power", "ON" if st.session_state.commercial_power else "OFF",
        None, "hmi-ok" if st.session_state.commercial_power else "hmi-warn")
    row("Generator state", st.session_state.gen_state,
        None, "hmi-ok" if st.session_state.gen_state != "ERROR" else "hmi-bad")
    card_end()

def panel_cctv():
    card_start("CCTV", "Observation (placeholder)", "📹")
    cctv_box("CCTV — Gate Area")
    card_end()

def panel_trends():
    card_start("Historical Trends", "Gate Opening and Discharge (dummy). Large view toggle for readability.", "📈")

    st.session_state.trend_large = st.toggle("Large view", value=st.session_state.trend_large)
    h = 320 if st.session_state.trend_large else 180

    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.line_chart(st.session_state.trend_gate, height=h)
        pill(f"Gate: {opening_pct}%", "hmi-pill hmi-ok")
    with c2:
        st.line_chart(st.session_state.trend_q, height=h)
        pill(f"Discharge(Q): {st.session_state.q_actual:.2f} m³/s", "hmi-pill hmi-ok")

    card_end()

# =========================
# Layout per mode
# =========================
left, mid, right = st.columns([1.10, 1.25, 1.05], gap="large")

with left:
    panel_gate_status()

with mid:
    panel_plan_actual()

    if mode == "REMOTE AUTOMATIC":
        panel_auto_control()
    elif mode == "REMOTE MANUAL":
        panel_manual_command()
    elif mode == "REMOTE PROGRAM":
        panel_program_control()
    else:
        card_start("Access / Lock", "Local LCP active (monitor-only).", "🔒")
        pill("LOCAL (LCP ACTIVE) — Remote operations disabled", "hmi-pill hmi-bad")
        row("Remote enabled", "YES" if st.session_state.remote_enabled else "NO")
        card_end()

    panel_trends()

with right:
    panel_alarms()
    panel_power()
    panel_cctv()

# =========================
# Auto refresh
# =========================
if auto_refresh:
    time.sleep(1)
    st.rerun()
