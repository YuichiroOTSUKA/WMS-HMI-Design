import streamlit as st
import time
from datetime import datetime
import random
import math

st.set_page_config(page_title="TC/SPC HMI Demo", layout="wide")

# =========================
# Global UI (CSS)
# =========================
st.markdown("""
<style>
/* Background */
[data-testid="stAppViewContainer"]{
  background: radial-gradient(1200px 600px at 30% 10%, #0f1b2d 0%, #070b14 55%, #050812 100%);
}
[data-testid="stSidebar"] { background: #0b1220; }
header, footer { visibility: hidden; }

/* Typography */
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
  display:flex;
  align-items:center;
  gap:8px;
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

/* Metric */
.hmi-metric{
  display:flex;
  justify-content:space-between;
  gap:10px;
  padding:10px 12px;
  border-radius:14px;
  border:1px solid #223049;
  background:#0b1220;
}
.hmi-metric .k{ color:#94a3b8; font-size:12px; font-weight:700; }
.hmi-metric .v{ font-size:18px; font-weight:900; }

/* Segmented buttons (fake tabs) */
.seg{
  display:flex;
  gap:8px;
  margin: 6px 0 10px 0;
}
.seg button{
  width:100%;
  border-radius:999px !important;
}
</style>
""", unsafe_allow_html=True)

# =========================
# State init
# =========================
def init_defaults():
    ss = st.session_state
    if "mode" not in ss: ss.mode = "REMOTE AUTOMATIC"  # default show the best view
    if "station" not in ss: ss.station = "BUT10"
    if "gate_group" not in ss: ss.gate_group = "UtaraMainGate"
    if "gate_no" not in ss: ss.gate_no = "Gate1"

    if "opening_pct" not in ss: ss.opening_pct = 49
    if "opening_m" not in ss: ss.opening_m = 1.63  # just a dummy display number

    if "target_pct" not in ss: ss.target_pct = 55
    if "moving" not in ss: ss.moving = "Stop"

    if "prot" not in ss:
        ss.prot = {
            "ELR": False,
            "Overload": False,
            "Over Torque Open": False,
            "Over Torque Close": False,
            "Control De-Energize": False,
        }

    if "power" not in ss:
        ss.power = {"Commercial": True, "GeneratorState": "OFF"}

    if "water_status" not in ss: ss.water_status = 75  # Y%
    if "pattern" not in ss: ss.pattern = "C"
    if "season" not in ss: ss.season = "Dry"

    if "q_plan" not in ss: ss.q_plan = 12.50
    if "q_now" not in ss: ss.q_now = 12.72
    if "q_est" not in ss: ss.q_est = 12.65

    if "wl_std" not in ss: ss.wl_std = 3.20
    if "wl_meas" not in ss: ss.wl_meas = 3.23
    if "time_lag_min" not in ss: ss.time_lag_min = 45

    if "auto_running" not in ss: ss.auto_running = False
    if "prog_running" not in ss: ss.prog_running = False

    if "trend" not in ss:
        # Keep short history for charts
        ss.trend = {
            "t": [i for i in range(180)],  # last 3 hours if 1-min steps (dummy)
            "gate": [],
            "q": [],
            "wl": [],
        }
        # seed
        g0 = ss.opening_pct
        q0 = ss.q_now
        w0 = ss.wl_meas
        for i in range(180):
            ss.trend["gate"].append(max(0, min(100, g0 + int(8*math.sin(i/18)) + random.randint(-1, 1))))
            ss.trend["q"].append(round(q0 + 0.12*math.sin(i/15) + random.uniform(-0.05, 0.05), 2))
            ss.trend["wl"].append(round(w0 + 0.03*math.sin(i/21) + random.uniform(-0.01, 0.01), 2))

init_defaults()

# =========================
# UI helpers
# =========================
def badge(label: str, value: str, klass: str = "hmi-pill"):
    st.markdown(f"<span class='{klass}'>{label}: {value}</span>", unsafe_allow_html=True)

def metric_row(key: str, val: str, suffix_badge: str | None = None, badge_class: str = "hmi-ok"):
    b = f"<span class='hmi-pill {badge_class}' style='margin-left:10px;'>{suffix_badge}</span>" if suffix_badge else ""
    st.markdown(f"""
<div class="hmi-metric">
  <div class="k">{key}</div>
  <div class="v">{val}{b}</div>
</div>
""", unsafe_allow_html=True)

def card_start(title: str, subtitle: str | None = None, icon: str = "◼"):
    st.markdown(f"""
<div class="hmi-card">
  <div class="hmi-title">{icon} {title}</div>
  {"<div class='hmi-sub'>"+subtitle+"</div>" if subtitle else ""}
""", unsafe_allow_html=True)

def card_end():
    st.markdown("</div>", unsafe_allow_html=True)

def cctv_box(title="CCTV — Gate Area"):
    st.markdown(
        f"""
<div style="height:230px;border-radius:14px;border:1px solid #223049;background:#050a14;
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
    y = 120 - int(open_pct * 0.8)   # move up when open
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

  <text x="48" y="60" fill="#94a3b8" font-size="14" font-family="sans-serif">Gate Opening</text>
  <text x="48" y="92" fill="#e2e8f0" font-size="34" font-weight="900" font-family="sans-serif">{open_pct}%</text>

  <text x="470" y="60" fill="#94a3b8" font-size="14" font-family="sans-serif" text-anchor="end">Opening</text>
  <text x="470" y="92" fill="#e2e8f0" font-size="28" font-weight="900" font-family="sans-serif" text-anchor="end">{opening_m:.2f} m</text>
</svg>
"""

def trend_update_tick():
    ss = st.session_state

    # jitter baseline values
    ss.q_now = max(0.0, round(ss.q_now + random.uniform(-0.06, 0.06), 2))
    ss.wl_meas = round(ss.wl_meas + random.uniform(-0.01, 0.01), 2)

    # extend arrays, keep max len 180
    ss.trend["t"].append(ss.trend["t"][-1] + 1)
    ss.trend["gate"].append(ss.opening_pct)
    ss.trend["q"].append(ss.q_now)
    ss.trend["wl"].append(ss.wl_meas)

    for k in ["t", "gate", "q", "wl"]:
        if len(ss.trend[k]) > 180:
            ss.trend[k] = ss.trend[k][-180:]

def step_motion():
    ss = st.session_state
    if ss.moving == "Opening":
        ss.opening_pct = min(100, ss.opening_pct + 2)
    elif ss.moving == "Closing":
        ss.opening_pct = max(0, ss.opening_pct - 2)
    if ss.opening_pct in (0, 100):
        ss.moving = "Stop"

def auto_tick():
    ss = st.session_state
    if abs(ss.opening_pct - ss.target_pct) <= 1:
        ss.moving = "Stop"
        return
    ss.moving = "Opening" if ss.opening_pct < ss.target_pct else "Closing"
    step_motion()

def deviation_pct(plan: float, now: float):
    if plan <= 0:
        return 0.0
    return (now - plan) / plan * 100.0

# =========================
# Sidebar (Navigation + demo controls)
# =========================
st.sidebar.markdown("## TC/SPC HMI Demo")

# Station/Gate selectors (visual parity with real UI)
st.sidebar.markdown("### Station / Gate")
st.sidebar.selectbox("Station", ["BUT10", "B.Sd.1", "B.Ut.2"], key="station")
st.sidebar.selectbox("Gate Group", ["UtaraMainGate", "WaruGate"], key="gate_group")
st.sidebar.selectbox("Gate No.", ["Gate1", "Gate2", "Gate3", "Gate4"], key="gate_no")

st.sidebar.markdown("---")
st.sidebar.radio(
    "Control Mode Screen",
    ["LOCAL (LCP ACTIVE)", "REMOTE MANUAL", "REMOTE AUTOMATIC", "REMOTE PROGRAM"],
    key="mode"
)
mode = st.session_state["mode"]

st.sidebar.markdown("---")
st.sidebar.markdown("### Demo Controls")
if st.sidebar.button("Simulate comm update / refresh"):
    # some realistic-ish shifts
    st.session_state.q_plan = round(st.session_state.q_plan + random.uniform(-0.10, 0.10), 2)
    st.session_state.q_est  = round(st.session_state.q_est  + random.uniform(-0.10, 0.10), 2)
    st.session_state.wl_std = round(st.session_state.wl_std + random.uniform(-0.03, 0.03), 2)
    st.session_state.wl_meas= round(st.session_state.wl_meas+ random.uniform(-0.03, 0.03), 2)
    st.session_state.time_lag_min = int(max(0, st.session_state.time_lag_min + random.randint(-2, 2)))

st.sidebar.markdown("### Safety flags")
for k in list(st.session_state.prot.keys()):
    st.session_state.prot[k] = st.sidebar.checkbox(k, value=st.session_state.prot[k])

st.sidebar.markdown("### Plan / Context")
st.session_state.pattern = st.sidebar.selectbox("Pattern", ["A", "B", "C", "D"], index=["A","B","C","D"].index(st.session_state.pattern))
st.session_state.season  = st.sidebar.selectbox("Season", ["Dry", "Wet"], index=["Dry","Wet"].index(st.session_state.season))
st.session_state.water_status = st.sidebar.select_slider("Water Availability Y (%)", options=[100, 90, 80, 75, 70, 60], value=st.session_state.water_status)

st.sidebar.markdown("### Power")
st.session_state.power["Commercial"] = st.sidebar.checkbox("Commercial Power", value=st.session_state.power["Commercial"])
st.session_state.power["GeneratorState"] = st.sidebar.selectbox(
    "Generator State", ["OFF", "READY", "RUNNING", "ERROR"],
    index=["OFF","READY","RUNNING","ERROR"].index(st.session_state.power["GeneratorState"])
)

# Auto refresh option (for trend/motion)
st.sidebar.markdown("---")
auto_refresh = st.sidebar.checkbox("Auto refresh (1s tick)", value=False)

# =========================
# Header bar (top)
# =========================
st.markdown(
    f"### {st.session_state.station}  ›  {st.session_state.gate_group} — {st.session_state.gate_no}",
)
top1, top2, top3, top4 = st.columns([1.4, 1.2, 1.2, 1.2])
with top1:
    badge("MODE", "AUTO" if mode == "REMOTE AUTOMATIC" else ("PROGRAM" if mode == "REMOTE PROGRAM" else ("MANUAL" if mode == "REMOTE MANUAL" else "LOCAL")),
          "hmi-pill hmi-ok" if mode != "LOCAL (LCP ACTIVE)" else "hmi-pill hmi-bad")
with top2:
    badge("WATER STATUS", f"NORMAL  •  Y={st.session_state.water_status}%", "hmi-pill hmi-ok")
with top3:
    badge("SYSTEM", "ACTIVE", "hmi-pill hmi-ok")
with top4:
    badge("LAST UPDATE", datetime.now().strftime("%H:%M:%S"), "hmi-pill")

st.markdown("")

# =========================
# Common status computations
# =========================
any_trip = any(st.session_state.prot.values())
ops_blocked = (mode == "LOCAL (LCP ACTIVE)") or any_trip or (st.session_state.power["GeneratorState"] == "ERROR")

dev = deviation_pct(st.session_state.q_plan, st.session_state.q_now)
within = abs(dev) <= 2.0
dev_label = f"Deviation {dev:+.1f}%"
range_label = "Within range" if within else "Out of range"
range_class = "hmi-ok" if within else "hmi-warn"

# =========================
# Views (mode-based)
# =========================

# ---- Left column shared "Gate Control" card with segmented mode selector (visual-only)
def gate_control_card():
    ss = st.session_state
    card_start("Gate Control", icon="🧰")

    # Segmented buttons (visual parity; actual mode switching still uses sidebar radio)
    st.markdown("""
<div class="seg">
""", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("AUTO", use_container_width=True):
            ss.mode = "REMOTE AUTOMATIC"
            st.rerun()
    with c2:
        if st.button("PROGRAM", use_container_width=True):
            ss.mode = "REMOTE PROGRAM"
            st.rerun()
    with c3:
        if st.button("MANUAL", use_container_width=True):
            ss.mode = "REMOTE MANUAL"
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(gate_svg(ss.opening_pct, ss.opening_m), unsafe_allow_html=True)

    if mode == "REMOTE AUTOMATIC":
        st.markdown("<span class='hmi-pill hmi-ok'>AUTO CONTROL ENABLED</span> <span class='hmi-pill'>Target Source: DSS</span>", unsafe_allow_html=True)
    elif mode == "REMOTE PROGRAM":
        st.markdown("<span class='hmi-pill hmi-ok'>PROGRAM CONTROL ENABLED</span> <span class='hmi-pill'>Target Source: Pattern</span>", unsafe_allow_html=True)
    elif mode == "REMOTE MANUAL":
        st.markdown("<span class='hmi-pill hmi-warn'>REMOTE MANUAL</span> <span class='hmi-pill'>Operator command</span>", unsafe_allow_html=True)
    else:
        st.markdown("<span class='hmi-pill hmi-bad'>LOCAL (LCP ACTIVE)</span> <span class='hmi-pill'>Remote disabled</span>", unsafe_allow_html=True)

    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

    # Protection switches list (display only)
    st.markdown("<div class='hmi-sub'>Protection / Interlocks</div>", unsafe_allow_html=True)
    for k, v in ss.prot.items():
        st.write(f"- {k}: {'ON' if v else 'OFF'}")

    card_end()


# ---- Main view layouts
if mode == "REMOTE AUTOMATIC":
    # Layout similar to your reference image:
    # [Gate Control] [Control Target] [Hydraulic Status]
    # [             ] [Control Target detail] [Water Level]
    # [             ] [Historical Trends (full width center+right)]
    left, mid, right = st.columns([1.05, 1.25, 1.15], gap="large")

    with left:
        gate_control_card()

    with mid:
        card_start("Control Target (Plan)", subtitle="Context from DSS / Pattern selection", icon="🎯")
        metric_row("Pattern", ss := st.session_state.pattern)
        metric_row("Season", st.session_state.season)
        metric_row("Water Availability", f"Y = {st.session_state.water_status}%")
        card_end()

        st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)

        card_start("Control Target (Plan)", subtitle="Set-point and required discharge", icon="🧠")
        # Q required = plan in this demo
        q_req = st.session_state.q_plan
        # Target opening derived from target_pct (dummy)
        z_target_m = round(st.session_state.opening_m * (st.session_state.target_pct/100), 2)

        cA, cB = st.columns([1.1, 1.0])
        with cA:
            metric_row("Required Discharge", f"{q_req:.2f} m³/s")
            metric_row("Qreq", f"{q_req:.2f} m³/s")
        with cB:
            metric_row("Z_target (ref)", f"{z_target_m:.2f} m")
            metric_row("Time (Tx)", f"{int(abs(st.session_state.target_pct-st.session_state.opening_pct)/2)} s")

        # Target slider and auto buttons
        st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
        st.session_state.target_pct = st.slider("Target Opening (Z_target) [%]", 0, 100, st.session_state.target_pct)

        b1, b2, b3 = st.columns(3)
        with b1:
            if st.button("START AUTO", use_container_width=True, disabled=ops_blocked):
                st.session_state.auto_running = True
        with b2:
            if st.button("STOP AUTO", use_container_width=True):
                st.session_state.auto_running = False
                st.session_state.moving = "Stop"
        with b3:
            if st.button("SWITCH TO MANUAL", use_container_width=True):
                st.session_state.auto_running = False
                st.session_state.moving = "Stop"
                st.session_state.mode = "REMOTE MANUAL"
                st.rerun()

        # Auto tick (one step per rerun)
        if st.session_state.auto_running and not ops_blocked:
            auto_tick()

        delta = st.session_state.target_pct - st.session_state.opening_pct
        auto_status = "Suspended (Blocked)" if ops_blocked else ("Reached" if abs(delta) <= 1 else "Adjusting")
        st.markdown(
            f"<span class='hmi-pill {('hmi-bad' if ops_blocked else 'hmi-ok')}'>{auto_status}</span> "
            f"<span class='hmi-pill'>ΔZ = {delta:+d}%</span> "
            f"<span class='hmi-pill'>Motion = {st.session_state.moving}</span>",
            unsafe_allow_html=True
        )

        if any_trip:
            st.error("Protection active: operation is blocked.")
        if st.session_state.power["GeneratorState"] == "ERROR":
            st.error("Generator ERROR: operation is blocked.")
        card_end()

    with right:
        card_start("Hydraulic Status", subtitle="Discharge monitoring (Plan / Now / Est.)", icon="💧")
        metric_row("Plan", f"{st.session_state.q_plan:.2f} m³/s")
        metric_row("Now",  f"{st.session_state.q_now:.2f} m³/s", suffix_badge=dev_label, badge_class=range_class)
        metric_row("Est.",  f"{st.session_state.q_est:.2f} m³/s", suffix_badge=range_label, badge_class=range_class)
        card_end()

        st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)

        card_start("Water Level", subtitle="Standard / Measured + time lag", icon="📏")
        metric_row("Stand.", f"{st.session_state.wl_std:.2f} m")
        metric_row("Measured", f"{st.session_state.wl_meas:.2f} m", suffix_badge="NORMAL", badge_class="hmi-ok")
        metric_row("Time Lag", f"{st.session_state.time_lag_min} min")
        card_end()

    st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)

    # Trends (full width)
    card_start("Historical Trends", subtitle="Gate opening / Discharge / Water level (dummy 3h window)", icon="📈")
    # Use built-in charts without extra libs
    t = st.session_state.trend["t"]
    gate_series = st.session_state.trend["gate"]
    q_series = st.session_state.trend["q"]
    wl_series = st.session_state.trend["wl"]

    c1, c2, c3 = st.columns(3)
    with c1:
        st.line_chart(gate_series, height=170)
        st.markdown(f"<span class='hmi-pill'>Gate Opening</span> <span class='hmi-pill hmi-ok'>{st.session_state.opening_pct}%</span>", unsafe_allow_html=True)
    with c2:
        st.line_chart(q_series, height=170)
        st.markdown(f"<span class='hmi-pill'>Discharge</span> <span class='hmi-pill hmi-ok'>{st.session_state.q_now:.2f} m³/s</span>", unsafe_allow_html=True)
    with c3:
        st.line_chart(wl_series, height=170)
        st.markdown(f"<span class='hmi-pill'>Water Level</span> <span class='hmi-pill hmi-ok'>{st.session_state.wl_meas:.2f} m</span>", unsafe_allow_html=True)

    st.caption(f"Hydraulic response reflects operation {st.session_state.time_lag_min} minutes earlier. (dummy)")
    card_end()

elif mode == "REMOTE MANUAL":
    left, mid, right = st.columns([1.05, 1.45, 1.10], gap="large")

    with left:
        gate_control_card()

    with mid:
        card_start("Command Panel", subtitle="Remote manual operation", icon="🕹️")

        st.markdown(
            f"<span class='hmi-pill {('hmi-bad' if ops_blocked else 'hmi-ok')}'>"
            f"{'BLOCKED' if ops_blocked else 'READY'}</span> "
            f"<span class='hmi-pill'>Motion={st.session_state.moving}</span>",
            unsafe_allow_html=True
        )

        b1, b2, b3 = st.columns(3)
        with b1:
            if st.button("OPEN", use_container_width=True, disabled=ops_blocked):
                st.session_state.moving = "Opening"
                step_motion()
        with b2:
            if st.button("STOP", use_container_width=True, disabled=ops_blocked):
                st.session_state.moving = "Stop"
        with b3:
            if st.button("CLOSE", use_container_width=True, disabled=ops_blocked):
                st.session_state.moving = "Closing"
                step_motion()

        st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
        metric_row("Current Opening", f"{st.session_state.opening_pct}%  /  {st.session_state.opening_m:.2f} m")
        metric_row("Discharge Now", f"{st.session_state.q_now:.2f} m³/s")
        metric_row("Measured WL", f"{st.session_state.wl_meas:.2f} m")
        card_end()

        st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)

        card_start("Safety / Interlocks", icon="🛡️")
        if any_trip:
            st.error("Protection active: operation is blocked.")
        if st.session_state.power["GeneratorState"] == "ERROR":
            st.error("Generator ERROR: operation is blocked.")
        st.write(f"- Commercial Power: {'ON' if st.session_state.power['Commercial'] else 'OFF'}")
        st.write(f"- Generator State: {st.session_state.power['GeneratorState']}")
        card_end()

    with right:
        card_start("CCTV", subtitle="(placeholder)", icon="📹")
        cctv_box("CCTV — Utara Kidul Uyee")
        card_end()

        st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)

        card_start("Hydraulic Status", icon="💧")
        metric_row("Plan", f"{st.session_state.q_plan:.2f} m³/s")
        metric_row("Now",  f"{st.session_state.q_now:.2f} m³/s", suffix_badge=dev_label, badge_class=range_class)
        metric_row("Measured WL", f"{st.session_state.wl_meas:.2f} m")
        card_end()

elif mode == "REMOTE PROGRAM":
    left, mid, right = st.columns([1.05, 1.45, 1.10], gap="large")

    with left:
        gate_control_card()

    with mid:
        card_start("Program Control", subtitle="Pattern/Season/Phase driven operation", icon="🧩")

        prg1, prg2, prg3 = st.columns(3)
        with prg1:
            st.session_state.pattern = st.selectbox("Pattern", ["A","B","C","D"], index=["A","B","C","D"].index(st.session_state.pattern))
        with prg2:
            st.session_state.season = st.selectbox("Season", ["Dry","Wet"], index=["Dry","Wet"].index(st.session_state.season))
        with prg3:
            phase = st.selectbox("Phase", ["Phase-1","Phase-2","Phase-3"], index=0)

        # derive program target from selection (dummy)
        base = {"A": 35, "B": 45, "C": 55, "D": 65}[st.session_state.pattern]
        season_adj = 5 if st.session_state.season == "Wet" else 0
        phase_adj = {"Phase-1": 0, "Phase-2": 8, "Phase-3": 15}[phase]
        st.session_state.target_pct = min(100, base + season_adj + phase_adj)

        metric_row("Program Target", f"{st.session_state.target_pct}%")
        metric_row("Current Opening", f"{st.session_state.opening_pct}%")

        b1, b2, b3 = st.columns(3)
        with b1:
            if st.button("START PROGRAM", use_container_width=True, disabled=ops_blocked):
                st.session_state.prog_running = True
        with b2:
            if st.button("STOP PROGRAM", use_container_width=True):
                st.session_state.prog_running = False
                st.session_state.moving = "Stop"
        with b3:
            if st.button("EMERGENCY STOP", use_container_width=True):
                st.session_state.prog_running = False
                st.session_state.moving = "Stop"
                st.warning("Emergency stop executed (dummy).")

        if st.session_state.prog_running and not ops_blocked:
            auto_tick()

        delta = st.session_state.target_pct - st.session_state.opening_pct
        prog_status = "Suspended (Blocked)" if ops_blocked else ("Completed" if abs(delta) <= 1 else "Running")
        st.markdown(
            f"<span class='hmi-pill {('hmi-bad' if ops_blocked else 'hmi-ok')}'>{prog_status}</span> "
            f"<span class='hmi-pill'>ΔZ={delta:+d}%</span> "
            f"<span class='hmi-pill'>Motion={st.session_state.moving}</span>",
            unsafe_allow_html=True
        )
        card_end()

        st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)

        card_start("Historical Trends", icon="📈")
        st.line_chart(st.session_state.trend["gate"], height=170)
        st.caption("Gate opening trend (dummy)")
        card_end()

    with right:
        card_start("CCTV", icon="📹")
        cctv_box("CCTV — Gate Area")
        card_end()

        st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)

        card_start("Hydraulic Status", icon="💧")
        metric_row("Plan", f"{st.session_state.q_plan:.2f} m³/s")
        metric_row("Now",  f"{st.session_state.q_now:.2f} m³/s", suffix_badge=dev_label, badge_class=range_class)
        metric_row("Water Level", f"{st.session_state.wl_meas:.2f} m")
        metric_row("Time Lag", f"{st.session_state.time_lag_min} min")
        card_end()

else:
    # LOCAL (monitor only)
    left, mid, right = st.columns([1.05, 1.45, 1.10], gap="large")

    with left:
        card_start("Access / Lock", subtitle="Local LCP active (remote disabled)", icon="🔒")
        st.markdown("<span class='hmi-pill hmi-bad'>REMOTE DISABLED</span>", unsafe_allow_html=True)
        st.write("Reason: Operation is currently controlled at site.")
        card_end()

        st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)
        gate_control_card()

    with mid:
        card_start("Monitor", subtitle="Read-only status", icon="👁️")
        metric_row("Current Opening", f"{st.session_state.opening_pct}% / {st.session_state.opening_m:.2f} m")
        metric_row("Discharge Now", f"{st.session_state.q_now:.2f} m³/s", suffix_badge=range_label, badge_class=range_class)
        metric_row("Measured WL", f"{st.session_state.wl_meas:.2f} m")
        metric_row("Time Lag", f"{st.session_state.time_lag_min} min")
        card_end()

        st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)
        card_start("Protection / Alarms", icon="🛡️")
        for k, v in st.session_state.prot.items():
            st.write(f"- {k}: {'ON' if v else 'OFF'}")
        card_end()

    with right:
        card_start("CCTV (View only)", icon="📹")
        cctv_box("CCTV — Utara Kidul Uyee")
        st.button("Manage CCTV (disabled in LOCAL)", disabled=True, use_container_width=True)
        card_end()

# =========================
# Tick update (optional)
# =========================
trend_update_tick()

if auto_refresh:
    time.sleep(1)
    st.rerun()
