import streamlit as st
import streamlit.components.v1 as components
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

/* Streamlit widgets tweak */
div[data-testid="stRadio"] > label { color:#94a3b8; font-weight:800; }
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
    d = max(-scale_pct, min(scale_pct, dev_pct))
    half = abs(d) / scale_pct * 50.0  # 0..50
    if d >= 0:
        st.markdown(f"""
<div class="div-wrap">
  <div class="div-center"></div>
  <div class="div-fill-pos" style='width:{half}%;'></div>
</div>
""", unsafe_allow_html=True)
    else:
        st.markdown(f"""
<div class="div-wrap">
  <div class="div-center"></div>
  <div class="div-fill-neg" style='width:{half}%;'></div>
</div>
""", unsafe_allow_html=True)

    st.markdown(f"""
<div class="div-scale">
  <div>-{scale_pct:.0f}%</div>
  <div>0%</div>
  <div>+{scale_pct:.0f}%</div>
</div>
""", unsafe_allow_html=True)

def opening_m_from_pct(open_pct: int, max_open_m: float):
    return round(max_open_m * (open_pct / 100.0), 2)

def opening_pct_from_m(open_m: float, max_open_m: float):
    if max_open_m <= 0:
        return 0
    return int(max(0, min(100, round(open_m / max_open_m * 100))))

def compute_h_plan_from_qplan(q_plan: float):
    return round(1.10 + 0.06 * (q_plan - 10.0), 2)

# =========================
# Pattern / Program (dummy)
# =========================
PATTERNS = {
    "A": {"target_open_base": 45, "target_open_gain": 2.0, "desc": "Standard"},
    "B": {"target_open_base": 55, "target_open_gain": 2.5, "desc": "High Demand"},
    "C": {"target_open_base": 35, "target_open_gain": 1.6, "desc": "Conservation"},
    "HOLD": {"target_open_base": 0, "target_open_gain": 0.0, "desc": "Safe Hold (no movement)"},
}

PROGRAMS = {
    "P-01 Dry / Standard": {"season": "Dry", "default_pattern": "A", "q_plan_bias": +0.00, "desc": "Dry season standard distribution program."},
    "P-02 Dry / High Demand": {"season": "Dry", "default_pattern": "B", "q_plan_bias": +0.80, "desc": "Dry season high-demand program (higher Q target)."},
    "P-03 Wet / Conservation": {"season": "Wet", "default_pattern": "C", "q_plan_bias": -0.50, "desc": "Wet season conservation program (lower Q target)."},
    "P-04 Maintenance / Safe Hold": {"season": "Dry", "default_pattern": "HOLD", "q_plan_bias": -999.0, "desc": "Maintenance hold (no automatic movement)."},
}

# =========================
# Data model (dummy)
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

# =========================
# Key helpers
# =========================
def current_dir_key():
    ss = st.session_state
    return f"{ss.station}/{ss.direction}"

def current_gate_key():
    ss = st.session_state
    return f"{ss.station}/{ss.direction}/{ss.selected_gate}"

# =========================
# State init
# =========================
def init_state():
    ss = st.session_state

    if "station" not in ss: ss.station = "BBT15"
    if "direction" not in ss: ss.direction = "BaratMainGate"
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

    # Direction-level targets/actuals (NEW)
    if "direction_state" not in ss:
        ds = {}
        for stn, dirs in ASSETS.items():
            for d in dirs.keys():
                dk = f"{stn}/{d}"
                q_plan = round(random.uniform(9.0, 14.0), 2)
                h_plan = compute_h_plan_from_qplan(q_plan)
                q_actual = round(q_plan + random.uniform(-0.3, 0.3), 2)
                h_actual = round(h_plan + random.uniform(-0.05, 0.05), 2)
                ds[dk] = {
                    "q_plan": q_plan,
                    "h_plan": h_plan,
                    "q_actual": q_actual,
                    "h_actual": h_actual,
                    "trend_q": [round(q_actual + 0.12*math.sin(i/12) + random.uniform(-0.05,0.05), 2) for i in range(120)],
                }
        ss.direction_state = ds

    # Global mode execution (direction-level concept)
    if "auto_state" not in ss: ss.auto_state = "STOPPED"     # RUNNING/PAUSED/STOPPED
    if "program_running" not in ss: ss.program_running = False

    # Remote Program selections
    if "program_name" not in ss: ss.program_name = "P-01 Dry / Standard"
    if "pattern_sel" not in ss: ss.pattern_sel = "A"
    if "season" not in ss: ss.season = PROGRAMS[ss.program_name]["season"]

    if "cctv_camera" not in ss: ss.cctv_camera = "CCTV — Gate Area"

    # Gate states
    if "gate_state" not in ss:
        gs = {}
        for stn, dirs in ASSETS.items():
            for d, gates in dirs.items():
                for g in gates:
                    key = f"{stn}/{d}/{g}"
                    open_pct = random.choice([0, 10, 25, 40, 55, 70, 85])
                    max_open_m = random.choice([2.00, 1.80, 1.60])
                    gs[key] = {
                        "open_pct": open_pct,
                        "max_open_m": max_open_m,
                        "last_cmd": "—",
                        "last_cmd_time": "—",
                    }
        ss.gate_state = gs

    # Trends
    if "trend_gate" not in ss:
        ss.trend_gate = [random.randint(0, 100) for _ in range(120)]

    if "trend_large" not in ss: ss.trend_large = False

init_state()

# =========================
# Core access control
# =========================
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

def get_gate():
    return st.session_state.gate_state[current_gate_key()]

def get_dir():
    return st.session_state.direction_state[current_dir_key()]

def send_cmd(cmd: str):
    now = datetime.now().strftime("%H:%M:%S")
    gg = get_gate()
    gg["last_cmd"] = cmd
    gg["last_cmd_time"] = now

def set_gate_open_pct(open_pct: int):
    gg = get_gate()
    gg["open_pct"] = int(max(0, min(100, open_pct)))

def step_gate_toward(gate_key: str, target_pct: int):
    gg = st.session_state.gate_state[gate_key]
    p = gg["open_pct"]
    if p < target_pct:
        p = min(100, p + 2)
    elif p > target_pct:
        p = max(0, p - 2)
    gg["open_pct"] = p

def step_all_gates_in_direction(target_pct: int):
    ss = st.session_state
    gates = ASSETS[ss.station][ss.direction]
    for g in gates:
        k = f"{ss.station}/{ss.direction}/{g}"
        step_gate_toward(k, target_pct)

# =========================
# Direction signals update (dummy)
# =========================
def tick_direction_signals():
    ss = st.session_state
    d = get_dir()

    d["h_plan"] = compute_h_plan_from_qplan(d["q_plan"])

    drift = 0.02 if ss.auto_state == "RUNNING" else 0.00
    d["q_actual"] = round(max(0.0, d["q_actual"] + random.uniform(-0.05, 0.05) - (d["q_actual"] - d["q_plan"])*drift), 2)

    # tie H_actual loosely with plan + noise (direction-level)
    d["h_actual"] = round(d["h_plan"] + random.uniform(-0.04, 0.04), 2)

    d["trend_q"] = (d["trend_q"] + [d["q_actual"]])[-120:]

def tick_gate_trend():
    gg = get_gate()
    open_pct = gg["open_pct"]
    st.session_state.trend_gate = (st.session_state.trend_gate + [open_pct])[-120:]

def apply_auto_control_if_running():
    ss = st.session_state
    if ss.mode != "REMOTE AUTOMATIC":
        return
    if ss.auto_state != "RUNNING":
        return
    if blocked():
        ss.auto_state = "STOPPED"
        return
    d = get_dir()
    # dummy target opening derived from H_plan (direction-level)
    target = int(max(0, min(100, 20 + d["h_plan"] * 30)))
    step_all_gates_in_direction(target)

def apply_program_control_if_running():
    ss = st.session_state
    if ss.mode != "REMOTE PROGRAM":
        return
    if not ss.program_running:
        return
    if blocked():
        ss.program_running = False
        return

    prog = PROGRAMS.get(ss.program_name)
    if not prog:
        return

    # direction-level season display
    ss.season = prog["season"]

    # optional q_plan bias (slow)
    d = get_dir()
    if prog["q_plan_bias"] > -900:
        d["q_plan"] = round(max(5.0, min(20.0, d["q_plan"] + prog["q_plan_bias"] * 0.01)), 2)

    pt = PATTERNS.get(ss.pattern_sel, PATTERNS["A"])
    if ss.pattern_sel == "HOLD":
        return

    target = int(pt["target_open_base"] + pt["target_open_gain"] * (d["q_plan"] - 10.0))
    target = max(0, min(100, target))
    step_all_gates_in_direction(target)

# tick once per render
tick_direction_signals()
apply_auto_control_if_running()
apply_program_control_if_running()
tick_gate_trend()

# =========================
# Direction Plan vs Actual Panel (REMOTE AUTOMATIC only)
# =========================
def panel_direction_plan_actual():
    dd = get_dir()
    dq = dd["q_actual"] - dd["q_plan"]
    pq = pct_delta(dd["q_plan"], dd["q_actual"])
    dh = dd["h_actual"] - dd["h_plan"]
    ph = pct_delta(dd["h_plan"], dd["h_actual"])

    card_start(
        "Control Targets (Plan vs Actual)",
        "Direction-level (NOT gate-level). Shown only in REMOTE AUTOMATIC.",
        "🎯"
    )

    row("Q_plan (Direction target)", f"{dd['q_plan']:.2f} m³/s")
    row("Q_actual (Direction)", f"{dd['q_actual']:.2f} m³/s", f"Δ {dq:+.2f} ({pq:+.1f}%)", dev_badge(abs(pq)))
    diverging_bar(pq, scale_pct=10.0)

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

    row("H_plan (Direction target)", f"{dd['h_plan']:.2f} m")
    row("H_actual (Direction)", f"{dd['h_actual']:.2f} m", f"Δ {dh:+.2f} ({ph:+.1f}%)", dev_badge(abs(ph)))
    diverging_bar(ph, scale_pct=10.0)

    card_end()

# =========================
# SVG: Gate overview building (no external images)
# =========================
def overview_building_svg(
    station: str,
    direction: str,
    gates: list[str],
    gate_states: dict,
    selected_gate: str,
    alarm_active: bool,
):
    n = max(1, len(gates))
    W, H = 1100, 420
    margin = 60
    bay_gap = 14
    bay_w = (W - 2*margin - (n-1)*bay_gap) / n
    bay_h = 200
    bay_y = 150

    roof_y = 40
    facade_y = 90

    stroke = "#223049"
    card = "#0b1220"
    panel = "#0a1020"
    water1 = "#0ea5e9"
    water2 = "#2563eb"
    txt = "#e5e7eb"
    sub = "#94a3b8"
    bad = "#fb7185"
    ok = "#34d399"

    alarm_color = bad if alarm_active else ok

    svg_parts = []
    svg_parts.append(f"""
<svg width="100%" height="100%" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid meet"
     xmlns="http://www.w3.org/2000/svg">

  <defs>
    <linearGradient id="bggrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#0b1220" stop-opacity="1"/>
      <stop offset="1" stop-color="#070b14" stop-opacity="1"/>
    </linearGradient>
    <linearGradient id="water" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{water1}" stop-opacity="0.95"/>
      <stop offset="1" stop-color="{water2}" stop-opacity="0.75"/>
    </linearGradient>
    <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="8" stdDeviation="10" flood-color="#000" flood-opacity="0.35"/>
    </filter>
  </defs>

  <rect x="0" y="0" width="{W}" height="{H}" rx="22" fill="url(#bggrad)" stroke="none"/>
 
  <path d="M{margin} {facade_y} L{margin+120} {roof_y} H{W-margin-120} L{W-margin} {facade_y} Z"
        fill="#111c2e" stroke="{stroke}" opacity="0.95"/>
  <rect x="{margin+20}" y="{facade_y}" width="{W-2*margin-40}" height="80" rx="14" fill="#0f172a" stroke="{stroke}" opacity="0.95"/>

  <circle cx="{W-margin-18}" cy="36" r="7" fill="{alarm_color}" opacity="0.9"/>
  <text x="{W-margin-30}" y="55" fill="{sub}" font-size="11" font-weight="800" text-anchor="end">
    {'ALARM' if alarm_active else 'NORMAL'}
  </text>
""")

    for i, gname in enumerate(gates):
        key = f"{station}/{direction}/{gname}"
        gs = gate_states.get(key, None)
        open_pct = gs["open_pct"] if gs else 0
        max_m = gs["max_open_m"] if gs else 2.0
        open_m = opening_m_from_pct(open_pct, max_m)

        x = margin + i*(bay_w + bay_gap)
        sel = (gname == selected_gate)

        outline = "#60a5fa" if sel else stroke
        glow = 'filter="url(#shadow)"' if sel else ''

        gate_dot = bad if alarm_active else ok

        svg_parts.append(f"""
  <g {glow}>
    <rect x="{x}" y="{bay_y}" width="{bay_w}" height="{bay_h}" rx="18" fill="{card}" stroke="{outline}" stroke-width="{2 if sel else 1}"/>
    <rect x="{x+18}" y="{bay_y+128}" width="{bay_w-36}" height="46" rx="14" fill="{panel}" stroke="{stroke}"/>
    <rect x="{x+26}" y="{bay_y+138}" width="{bay_w-52}" height="28" rx="12" fill="url(#water)" opacity="0.95"/>

    <rect x="{x+bay_w*0.36}" y="{bay_y+26}" width="{bay_w*0.28}" height="130" rx="12" fill="{panel}" stroke="{stroke}"/>
    <rect x="{x+bay_w*0.36+6}" y="{bay_y+40}" width="{bay_w*0.28-12}" height="70" rx="12" fill="#1f6feb" stroke="#60a5fa" opacity="0.92"/>

    <circle cx="{x+24}" cy="{bay_y+26}" r="6" fill="{gate_dot}" opacity="0.9"/>
    <text x="{x+40}" y="{bay_y+30}" fill="{txt}" font-size="13" font-weight="900">{gname}</text>

    <text x="{x+bay_w/2}" y="{bay_y+bay_h+28}" fill="{txt}" font-size="13" font-weight="900" text-anchor="middle">{open_pct}%</text>
    <text x="{x+bay_w/2}" y="{bay_y+bay_h+48}" fill="{sub}" font-size="12" font-weight="800" text-anchor="middle">{open_m:.2f} m</text>
  </g>
""")

    svg_parts.append("</svg>")
    return "\n".join(svg_parts)

# =========================
# SVG: single gate for manual intuitive control
# =========================
def gate_svg(open_pct: int):
    y = 120 - int(open_pct * 0.8)
    y = max(40, min(120, y))
    return f"""
<svg width="100%" height="100%" viewBox="0 0 520 260" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="water_d" x1="0" x2="0" y1="0" y2="1">
      <stop offset="0" stop-color="#0ea5e9" stop-opacity="0.92"/>
      <stop offset="1" stop-color="#2563eb" stop-opacity="0.72"/>
    </linearGradient>
    <filter id="sh_d" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="6" stdDeviation="8" flood-color="#000" flood-opacity="0.35"/>
    </filter>
  </defs>

  <rect x="22" y="20" width="476" height="220" rx="18" fill="#0b1220" stroke="#223049"/>
  <rect x="150" y="40" width="46" height="170" rx="10" fill="#111c2e" stroke="#223049"/>
  <rect x="324" y="40" width="46" height="170" rx="10" fill="#111c2e" stroke="#223049"/>

  <rect x="80" y="170" width="360" height="44" rx="12" fill="#0a1020" stroke="#223049"/>
  <rect x="92" y="182" width="336" height="30" rx="10" fill="url(#water_d)" opacity="0.95"/>

  <rect x="220" y="62" width="80" height="140" rx="10" fill="#0a1020" stroke="#223049"/>

  <g filter="url(#sh_d)">
    <rect x="226" y="{y}" width="68" height="90" rx="10" fill="#1f6feb" opacity="0.92" stroke="#60a5fa"/>
  </g>
</svg>
"""

# =========================
# Sidebar
# =========================
st.sidebar.markdown("## WMS HMI Demo")

stations = list(ASSETS.keys())
st.sidebar.selectbox("Station", stations, key="station")

directions = list(ASSETS[st.session_state.station].keys())
if st.session_state.direction not in directions:
    st.session_state.direction = directions[0]
st.sidebar.selectbox("Direction", directions, key="direction")

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

# Direction-level plan slider (still editable, but now affects Direction)
st.sidebar.markdown("### Direction Plan (dummy)")
d = get_dir()
d["q_plan"] = round(st.sidebar.slider("Q_plan (Direction target) [m³/s]", 5.0, 20.0, float(d["q_plan"]), 0.05), 2)

st.sidebar.markdown("---")
auto_refresh = st.sidebar.checkbox("Auto refresh (1s)", value=False)

# =========================
# Header
# =========================
mode = st.session_state.mode
is_blocked = blocked()

st.markdown(f"### {st.session_state.station}  ›  Direction: {st.session_state.direction}")
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
    pill(f"LAST UPDATE: {datetime.now().strftime("%H:%M:%S")}", "hmi-pill")

st.markdown("")

# =========================
# Gate Overview + Mode-level controls above it
# =========================
gates = ASSETS[st.session_state.station][st.session_state.direction]
if st.session_state.selected_gate not in gates:
    st.session_state.selected_gate = gates[0]

alarm_active = any(st.session_state.prot.values())

# --- Mode top controls (Gateより上位)
if mode == "REMOTE AUTOMATIC":
    card_start("Automatic Mode Control",
               "Direction-level execution controls (not gate-specific).",
               "🤖")
    b1, b2, b3 = st.columns(3, gap="large")
    with b1:
        if st.button("▶ Start", use_container_width=True, disabled=is_blocked):
            st.session_state.auto_state = "RUNNING"
    with b2:
        if st.button("⏸ Pause", use_container_width=True):
            st.session_state.auto_state = "PAUSED"
    with b3:
        if st.button("⏹ Stop", use_container_width=True):
            st.session_state.auto_state = "STOPPED"
    row("Auto state", st.session_state.auto_state,
        None,
        "hmi-ok" if st.session_state.auto_state=="RUNNING"
        else "hmi-warn" if st.session_state.auto_state=="PAUSED"
        else "hmi-bad"
    )
    card_end()
    st.markdown("")

    # NEW: Plan vs Actual shown under Automatic Mode Control
    panel_direction_plan_actual()
    st.markdown("")

if mode == "REMOTE PROGRAM":
    card_start("Program Mode Control",
               "Direction-level program execution controls (not gate-specific).",
               "🧩")
    c1, c2 = st.columns([1.2, 1.0], gap="large")
    with c1:
        st.selectbox("Program", list(PROGRAMS.keys()), key="program_name")
        st.caption(PROGRAMS[st.session_state.program_name]["desc"])
    with c2:
        st.selectbox("Pattern", list(PATTERNS.keys()), key="pattern_sel")
        st.caption(f"Pattern detail: {PATTERNS[st.session_state.pattern_sel]["desc"]}")
    bb1, bb2 = st.columns(2, gap="large")
    with bb1:
        if st.button("▶ RUN", use_container_width=True, disabled=is_blocked):
            st.session_state.program_running = True
            st.session_state.season = PROGRAMS[st.session_state.program_name]["season"]
    with bb2:
        if st.button("⏹ STOP", use_container_width=True):
            st.session_state.program_running = False
    row("Program state", "RUNNING" if st.session_state.program_running else "STOPPED",
        None, "hmi-ok" if st.session_state.program_running else "hmi-bad"
    )
    row("Season", st.session_state.season)
    card_end()
    st.markdown("")

# --- Gate Overview
card_start(
    "Gate Overview",
    "Code-generated schematic (no image files). Select a gate below to open detail panels.",
    "🏛️"
)

svg_overview = overview_building_svg(
    station=st.session_state.station,
    direction=st.session_state.direction,
    gates=gates,
    gate_states=st.session_state.gate_state,
    selected_gate=st.session_state.selected_gate,
    alarm_active=alarm_active,
)

html_overview = f"""
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <style>
    html, body {{
      margin: 0;
      padding: 0;
      background: transparent;
      overflow: hidden;
      height: 100%;
      width: 100%;
    }}
    svg {{
      display: block;
      width: 100%;
      height: 100%;
    }}
  </style>
</head>
<body>
  {svg_overview}
</body>
</html>
"""
components.html(html_overview, height=430, scrolling=False)

sel = st.radio(
    "Select gate",
    gates,
    horizontal=True,
    index=gates.index(st.session_state.selected_gate),
    label_visibility="collapsed",
)
if sel != st.session_state.selected_gate:
    st.session_state.selected_gate = sel
    st.rerun()

card_end()
st.markdown("")

# =========================
# Detail area (3 columns)
# =========================
g = get_gate()
opening_pct = g["open_pct"]
opening_m = opening_m_from_pct(opening_pct, g["max_open_m"])

def panel_gate_status_and_manual_controls():
    card_start(f"Gate Status — {st.session_state.selected_gate}",
               "Schematic + Opening. Manual mode provides intuitive sliders for % and meters.",
               "🚪")

    components.html(gate_svg(opening_pct), height=290, scrolling=False)

    row("Opening (Percent)", f"{opening_pct}%")
    bar(opening_pct)
    row("Opening (Meters)", f"{opening_m:.2f} m  (max {g["max_open_m"]:.2f} m)")
    bar(int(round((opening_m / g["max_open_m"]) * 100)) if g["max_open_m"] > 0 else 0)

    # REMOTE MANUAL: provide direct % and meters adjustment (direction targets are NOT shown)
    if st.session_state.mode == "REMOTE MANUAL":
        st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
        pill("BLOCKED" if is_blocked else "READY",
             "hmi-pill hmi-bad" if is_blocked else "hmi-pill hmi-ok")

        c1, c2 = st.columns(2, gap="large")
        with c1:
            pct = st.slider("Manual Opening (%)", 0, 100, int(opening_pct), 1, key="manual_pct")
            if st.button("Apply %", use_container_width=True, disabled=is_blocked):
                send_cmd(f"MANUAL SET {pct}%")
                set_gate_open_pct(pct)

        with c2:
            mm = st.slider("Manual Opening (m)", 0.0, float(g["max_open_m"]), float(opening_m), 0.01, key="manual_m")
            if st.button("Apply m", use_container_width=True, disabled=is_blocked):
                pct2 = opening_pct_from_m(mm, g["max_open_m"])
                send_cmd(f"MANUAL SET {mm:.2f}m ({pct2}%)")
                set_gate_open_pct(pct2)

        # simple jog buttons (intuitive)
        j1, j2, j3, j4 = st.columns(4, gap="small")
        with j1:
            if st.button("−10%", use_container_width=True, disabled=is_blocked):
                send_cmd("JOG -10%")
                set_gate_open_pct(opening_pct - 10)
        with j2:
            if st.button("−2%", use_container_width=True, disabled=is_blocked):
                send_cmd("JOG -2%")
                set_gate_open_pct(opening_pct - 2)
        with j3:
            if st.button("+2%", use_container_width=True, disabled=is_blocked):
                send_cmd("JOG +2%")
                set_gate_open_pct(opening_pct + 2)
        with j4:
            if st.button("+10%", use_container_width=True, disabled=is_blocked):
                send_cmd("JOG +10%")
                set_gate_open_pct(opening_pct + 10)

    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
    st.markdown("<div class='hmi-sub' style='margin-top:2px;'>CCTV</div>", unsafe_allow_html=True)
    st.selectbox(
        "CCTV Camera",
        ["CCTV — Gate Area", "CCTV — Upstream", "CCTV — Downstream"],
        key="cctv_camera",
        label_visibility="collapsed",
    )
    cctv_box(st.session_state.cctv_camera)

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

def panel_trends():
    card_start("Historical Trends", "Gate Opening + Direction Discharge (dummy).", "📈")
    st.session_state.trend_large = st.toggle("Large view", value=st.session_state.trend_large)
    h = 320 if st.session_state.trend_large else 180

    d = get_dir()
    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.line_chart(st.session_state.trend_gate, height=h)
        pill(f"Gate: {opening_pct}%", "hmi-pill hmi-ok")
    with c2:
        st.line_chart(d["trend_q"], height=h)
        pill(f"Direction Q: {d["q_actual"]:.2f} m³/s", "hmi-pill hmi-ok")
    card_end()

left, mid, right = st.columns([1.10, 1.25, 1.05], gap="large")
with left:
    panel_gate_status_and_manual_controls()
with mid:
    panel_trends()
with right:
    panel_alarms()
    panel_power()

# =========================
# Auto refresh
# =========================
if auto_refresh:
    time.sleep(1)
    st.rerun()
