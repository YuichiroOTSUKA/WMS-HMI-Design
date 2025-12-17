import streamlit as st
import time
from datetime import datetime
import random
import math

st.set_page_config(page_title="TC/SPC HMI Demo (TS-aligned)", layout="wide")

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

/* Metric row */
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
    # visual only: gate plate moves by open_pct
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

  <text x="48" y="60" fill="#94a3b8" font-size="14" font-family="sans-serif">Gate Opening</text>
  <text x="48" y="92" fill="#e2e8f0" font-size="34" font-weight="900" font-family="sans-serif">{open_pct}%</text>

  <text x="470" y="60" fill="#94a3b8" font-size="14" font-family="sans-serif" text-anchor="end">Opening</text>
  <text x="470" y="92" fill="#e2e8f0" font-size="28" font-weight="900" font-family="sans-serif" text-anchor="end">{opening_m:.2f} m</text>
</svg>
"""

# =========================
# TS-aligned state model (dummy values)
# =========================
def init():
    ss = st.session_state
    if "station" not in ss: ss.station = "BUT10"
    if "gate_group" not in ss: ss.gate_group = "UtaraMainGate"
    if "gate_no" not in ss: ss.gate_no = "Gate1"

    # Control mode screens
    if "mode" not in ss: ss.mode = "REMOTE AUTOMATIC"  # default best demo

    # Gate / LCP / Access
    if "access" not in ss: ss.access = "REMOTE"  # REMOTE or LOCAL
    if "remote_enabled" not in ss: ss.remote_enabled = True
    if "door_open" not in ss: ss.door_open = False

    # Gate status
    if "opening_pct" not in ss: ss.opening_pct = 49
    if "opening_m" not in ss: ss.opening_m = 1.63
    if "fully_open" not in ss: ss.fully_open = False
    if "fully_close" not in ss: ss.fully_close = True
    if "motion" not in ss: ss.motion = "STOP"  # OPENING/CLOSING/STOP
    if "last_cmd" not in ss: ss.last_cmd = "—"
    if "last_cmd_time" not in ss: ss.last_cmd_time = "—"

    # Protection / alarms (examples; align with typical TS I/O)
    if "prot" not in ss:
        ss.prot = {
            "ELR": False,
            "Overload": False,
            "Over Torque Open": False,
            "Over Torque Close": False,
            "Control De-Energize": False,
        }

    # Communication (TS: normal wired + backup mobile; SPC is mobile normal)
    if "comm_main" not in ss: ss.comm_main = "NORMAL"  # NORMAL/DOWN
    if "comm_backup" not in ss: ss.comm_backup = "STANDBY"  # STANDBY/ACTIVE/DOWN

    # Water status (TS: auto determined OR manual input depending on mode)
    if "water_status" not in ss: ss.water_status = 80  # %
    if "water_status_source" not in ss: ss.water_status_source = "AUTO"  # AUTO/MANUAL

    # Program selection (TS: pattern program A/B/C/D etc)
    if "pattern" not in ss: ss.pattern = "C"
    if "season" not in ss: ss.season = "Dry"
    if "program_source" not in ss: ss.program_source = "AUTO"  # AUTO/MANUAL

    # Hydrology / reference from TM (TS: WL + discharge from relevant TM; compare to target)
    if "wl_up" not in ss: ss.wl_up = 3.23
    if "wl_down" not in ss: ss.wl_down = 3.20
    if "q_actual" not in ss: ss.q_actual = 12.72

    # Targets used by automatic/program logic (TS: target discharge; computed gate opening value)
    if "q_target" not in ss: ss.q_target = 12.50
    if "open_target_pct" not in ss: ss.open_target_pct = 55  # “value” to LCP
    if "control_cycle" not in ss: ss.control_cycle = "IDLE"  # IDLE/RUNNING/WAITING
    if "eval_interval_min" not in ss: ss.eval_interval_min = 15
    if "time_lag_min" not in ss: ss.time_lag_min = 45  # TS mentions time lag concept in later clauses

    # Generator (TS: generator information + control)
    if "commercial_power" not in ss: ss.commercial_power = True
    if "gen_state" not in ss: ss.gen_state = "OFF"  # OFF/READY/RUNNING/ERROR

    # Trend buffers (for display only)
    if "trend_gate" not in ss:
        ss.trend_gate = [max(0, min(100, ss.opening_pct + int(7*math.sin(i/18)) + random.randint(-1,1))) for i in range(120)]
        ss.trend_q    = [round(ss.q_actual + 0.12*math.sin(i/15) + random.uniform(-0.05,0.05), 2) for i in range(120)]
        ss.trend_wl   = [round(ss.wl_up + 0.03*math.sin(i/21) + random.uniform(-0.01,0.01), 2) for i in range(120)]

init()

# =========================
# Logic helpers
# =========================
def is_blocked():
    ss = st.session_state
    if ss.mode == "LOCAL (LCP ACTIVE)":
        return True
    if any(ss.prot.values()):
        return True
    if ss.gen_state == "ERROR":
        return True
    # Example: if remote disabled
    if not ss.remote_enabled:
        return True
    return False

def deviation_pct(target, actual):
    if target <= 0:
        return 0.0
    return (actual - target) / target * 100.0

def send_cmd(cmd: str):
    ss = st.session_state
    ss.last_cmd = cmd
    ss.last_cmd_time = datetime.now().strftime("%H:%M:%S")

def step_gate_toward(target_pct: int):
    ss = st.session_state
    if ss.opening_pct < target_pct:
        ss.motion = "OPENING"
        ss.opening_pct = min(100, ss.opening_pct + 2)
    elif ss.opening_pct > target_pct:
        ss.motion = "CLOSING"
        ss.opening_pct = max(0, ss.opening_pct - 2)
    else:
        ss.motion = "STOP"

    ss.fully_open = (ss.opening_pct >= 100)
    ss.fully_close = (ss.opening_pct <= 0)

def tick_trends():
    ss = st.session_state
    # dummy dynamics
    ss.q_actual = round(max(0.0, ss.q_actual + random.uniform(-0.06, 0.06)), 2)
    ss.wl_up = round(ss.wl_up + random.uniform(-0.01, 0.01), 2)

    ss.trend_gate = (ss.trend_gate + [ss.opening_pct])[-120:]
    ss.trend_q = (ss.trend_q + [ss.q_actual])[-120:]
    ss.trend_wl = (ss.trend_wl + [ss.wl_up])[-120:]

tick_trends()

# =========================
# Sidebar
# =========================
st.sidebar.markdown("## TC/SPC HMI Demo")
st.sidebar.markdown("### Station / Gate")
st.sidebar.selectbox("Station", ["BUT10", "B.Sd.1", "B.Cpl.5", "B.Ut.10"], key="station")
st.sidebar.selectbox("Gate Group", ["UtaraMainGate", "WaruGate"], key="gate_group")
st.sidebar.selectbox("Gate No.", ["Gate1", "Gate2", "Gate3", "Gate4"], key="gate_no")

st.sidebar.markdown("---")
st.sidebar.radio(
    "Control Mode Screen",
    ["LOCAL (LCP ACTIVE)", "REMOTE MANUAL", "REMOTE AUTOMATIC", "REMOTE PROGRAM"],
    key="mode"
)

st.sidebar.markdown("---")
st.sidebar.markdown("### Demo toggles (dummy)")
st.session_state.remote_enabled = st.sidebar.checkbox("Remote enabled", value=st.session_state.remote_enabled)
st.session_state.comm_main = st.sidebar.selectbox("Main comm", ["NORMAL", "DOWN"], index=["NORMAL","DOWN"].index(st.session_state.comm_main))
st.session_state.comm_backup = st.sidebar.selectbox("Backup comm", ["STANDBY", "ACTIVE", "DOWN"], index=["STANDBY","ACTIVE","DOWN"].index(st.session_state.comm_backup))

st.sidebar.markdown("### Protection / alarms")
for k in list(st.session_state.prot.keys()):
    st.session_state.prot[k] = st.sidebar.checkbox(k, value=st.session_state.prot[k])

st.sidebar.markdown("### Water status / program (TS concepts)")
st.session_state.water_status = st.sidebar.select_slider("Water status (%)", options=[100, 90, 80, 70, 60, 50, 30], value=st.session_state.water_status)
st.session_state.season = st.sidebar.selectbox("Season", ["Dry", "Wet"], index=["Dry","Wet"].index(st.session_state.season))
st.session_state.pattern = st.sidebar.selectbox("Pattern program", ["A","B","C","D"], index=["A","B","C","D"].index(st.session_state.pattern))

st.sidebar.markdown("### Generator / power")
st.session_state.commercial_power = st.sidebar.checkbox("Commercial power", value=st.session_state.commercial_power)
st.session_state.gen_state = st.sidebar.selectbox("Generator state", ["OFF","READY","RUNNING","ERROR"],
                                                index=["OFF","READY","RUNNING","ERROR"].index(st.session_state.gen_state))

st.sidebar.markdown("---")
auto_refresh = st.sidebar.checkbox("Auto refresh (1s)", value=False)

# =========================
# Header
# =========================
mode = st.session_state.mode
blocked = is_blocked()

st.markdown(f"### {st.session_state.station}  ›  {st.session_state.gate_group} — {st.session_state.gate_no}")

h1, h2, h3, h4 = st.columns([1.4, 1.2, 1.2, 1.2])
with h1:
    pill(f"MODE: {('AUTO' if mode=='REMOTE AUTOMATIC' else 'PROGRAM' if mode=='REMOTE PROGRAM' else 'MANUAL' if mode=='REMOTE MANUAL' else 'LOCAL')}",
         "hmi-pill hmi-ok" if mode != "LOCAL (LCP ACTIVE)" else "hmi-pill hmi-bad")
with h2:
    pill(f"COMM: MAIN={st.session_state.comm_main} / BK={st.session_state.comm_backup}",
         "hmi-pill hmi-ok" if st.session_state.comm_main=="NORMAL" else "hmi-pill hmi-warn")
with h3:
    pill(f"GEN: {st.session_state.gen_state}", "hmi-pill hmi-ok" if st.session_state.gen_state in ["OFF","READY","RUNNING"] else "hmi-pill hmi-bad")
with h4:
    pill(f"LAST UPDATE: {datetime.now().strftime('%H:%M:%S')}", "hmi-pill")

st.markdown("")

# =========================
# Common panels (TS-aligned)
# =========================
def panel_gate_status():
    ss = st.session_state
    card_start("Gate Status", "Gate opening indication + motion + limit switches (dummy)", "🚪")
    st.markdown(gate_svg(ss.opening_pct, ss.opening_m), unsafe_allow_html=True)
    row("Motion", ss.motion)
    row("Fully Open", "YES" if ss.fully_open else "NO")
    row("Fully Close", "YES" if ss.fully_close else "NO")
    row("Last Command", ss.last_cmd, f"@ {ss.last_cmd_time}" if ss.last_cmd_time != "—" else None, "hmi-pill")
    card_end()

def panel_hydrology_reference():
    ss = st.session_state
    dev = deviation_pct(ss.q_target, ss.q_actual)
    within = abs(dev) <= 2.0
    card_start("Hydrology (Reference TM)", "Water level & discharge for monitoring / control reference (dummy)", "💧")
    row("Upstream WL", f"{ss.wl_up:.2f} m")
    row("Downstream WL", f"{ss.wl_down:.2f} m")
    row("Actual Discharge (Q)", f"{ss.q_actual:.2f} m³/s", f"Δ vs Qtarget {dev:+.1f}%", "hmi-ok" if within else "hmi-warn")
    row("Time Lag (concept)", f"{ss.time_lag_min} min")
    card_end()

def panel_alarms_interlocks():
    ss = st.session_state
    card_start("Protection / Alarms", "Interlocks must be visible in any control mode (dummy)", "🛡️")
    if any(ss.prot.values()):
        pill("ACTIVE ALARM / TRIP PRESENT", "hmi-pill hmi-bad")
    else:
        pill("NO ACTIVE TRIP", "hmi-pill hmi-ok")

    for k, v in ss.prot.items():
        row(k, "ON" if v else "OFF", None, "hmi-bad" if v else "hmi-ok")
    row("Door sensor", "OPEN" if ss.door_open else "CLOSED", None, "hmi-warn" if ss.door_open else "hmi-ok")
    card_end()

def panel_power_generator():
    ss = st.session_state
    card_start("Power / Generator", "Generator info + power source status (dummy)", "⚡")
    row("Commercial power", "ON" if ss.commercial_power else "OFF", None, "hmi-ok" if ss.commercial_power else "hmi-warn")
    row("Generator state", ss.gen_state, None, "hmi-ok" if ss.gen_state in ["OFF","READY","RUNNING"] else "hmi-bad")
    card_end()

def panel_cctv():
    card_start("CCTV (Observation)", "Observation of gate/water surface/security (placeholder)", "📹")
    cctv_box("CCTV — Gate Area (PTZ placeholder)")
    card_end()

def panel_trends():
    ss = st.session_state
    card_start("Historical Trends", "Trends for gate opening / discharge / WL (dummy)", "📈")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.line_chart(ss.trend_gate, height=160)
        pill(f"Gate: {ss.opening_pct}%", "hmi-pill hmi-ok")
    with c2:
        st.line_chart(ss.trend_q, height=160)
        pill(f"Q: {ss.q_actual:.2f} m³/s", "hmi-pill hmi-ok")
    with c3:
        st.line_chart(ss.trend_wl, height=160)
        pill(f"WL: {ss.wl_up:.2f} m", "hmi-pill hmi-ok")
    card_end()

# =========================
# Mode-specific panels (TS aligned)
# =========================
def view_local():
    # TS intent: local full manual at site; remote disabled; HMI = monitor-only
    left, mid, right = st.columns([1.15, 1.15, 1.0], gap="large")
    with left:
        card_start("Access / Lock", "Local control selected at site (remote disabled)", "🔒")
        pill("LOCAL (LCP ACTIVE) — Remote operations disabled", "hmi-pill hmi-bad")
        row("Remote enabled", "YES" if st.session_state.remote_enabled else "NO")
        row("Main comm", st.session_state.comm_main)
        row("Backup comm", st.session_state.comm_backup)
        card_end()

        panel_gate_status()

    with mid:
        panel_hydrology_reference()
        panel_alarms_interlocks()

    with right:
        panel_power_generator()
        panel_cctv()

    st.markdown("")
    panel_trends()

def view_remote_manual():
    # TS intent: operator can rise/down/stop; must see gate status + interlocks + reference hydrology
    left, mid, right = st.columns([1.15, 1.20, 1.0], gap="large")

    with left:
        panel_gate_status()

    with mid:
        card_start("Manual Command", "Direct control (Rise / Down / Stop) with safety interlocks (dummy)", "🕹️")
        pill("BLOCKED" if blocked else "READY", "hmi-pill hmi-bad" if blocked else "hmi-pill hmi-ok")

        b1, b2, b3 = st.columns(3)
        with b1:
            if st.button("OPEN (Rise)", use_container_width=True, disabled=blocked):
                send_cmd("OPEN")
                step_gate_toward(100)
        with b2:
            if st.button("STOP", use_container_width=True, disabled=blocked):
                send_cmd("STOP")
                st.session_state.motion = "STOP"
        with b3:
            if st.button("CLOSE (Down)", use_container_width=True, disabled=blocked):
                send_cmd("CLOSE")
                step_gate_toward(0)

        row("Command path (concept)", "Water & Gate Mgmt Terminal → TC/SPC RTU → LCP")
        row("Last command", st.session_state.last_cmd, f"@ {st.session_state.last_cmd_time}" if st.session_state.last_cmd_time != "—" else None, "hmi-pill")
        card_end()

        panel_hydrology_reference()

    with right:
        panel_alarms_interlocks()
        panel_power_generator()
        panel_cctv()

    st.markdown("")
    panel_trends()

def view_remote_automatic():
    # TS intent: water status auto determined; servers compute gate opening value; compare actual discharge and readjust
    left, mid, right = st.columns([1.10, 1.25, 1.05], gap="large")

    with left:
        panel_gate_status()

    with mid:
        card_start("Automatic Control (TS concept)", "Water status → parameters → computed gate opening value → readjust by Q comparison (dummy)", "🤖")

        # Water status source fixed to AUTO in this view
        st.session_state.water_status_source = "AUTO"
        row("Water status source", st.session_state.water_status_source, f"{st.session_state.water_status}%", "hmi-ok")

        # Automatic computation (dummy mapping)
        # target discharge derived from water status + season/pattern (placeholder only)
        base_q = 12.50
        adj = (st.session_state.water_status - 80) * 0.03
        st.session_state.q_target = round(base_q + adj, 2)

        # computed gate opening "value" (dummy)
        st.session_state.open_target_pct = int(max(0, min(100, 55 + (st.session_state.q_target - base_q) * 25)))

        dev = deviation_pct(st.session_state.q_target, st.session_state.q_actual)
        within = abs(dev) <= 2.0

        row("Q_target (required)", f"{st.session_state.q_target:.2f} m³/s")
        row("Q_actual", f"{st.session_state.q_actual:.2f} m³/s", f"Δ {dev:+.1f}%", "hmi-ok" if within else "hmi-warn")
        row("Computed gate opening value", f"{st.session_state.open_target_pct}% (to LCP)")
        row("Evaluation interval (concept)", f"{st.session_state.eval_interval_min} min")

        b1, b2, b3 = st.columns(3)
        with b1:
            if st.button("START AUTO", use_container_width=True, disabled=blocked):
                st.session_state.control_cycle = "RUNNING"
                send_cmd("AUTO START")
        with b2:
            if st.button("STOP AUTO", use_container_width=True):
                st.session_state.control_cycle = "IDLE"
                st.session_state.motion = "STOP"
                send_cmd("AUTO STOP")
        with b3:
            if st.button("APPLY 1 STEP", use_container_width=True, disabled=blocked):
                send_cmd("AUTO STEP")
                step_gate_toward(st.session_state.open_target_pct)

        row("Control cycle", st.session_state.control_cycle, None, "hmi-ok" if st.session_state.control_cycle=="RUNNING" else "hmi-warn")
        card_end()

        panel_hydrology_reference()

    with right:
        panel_alarms_interlocks()
        panel_power_generator()
        panel_cctv()

    st.markdown("")
    panel_trends()

def view_remote_program():
    # TS intent: operator selects pattern program; in some cases manual water status/program selection; higher priority (SPC) concept
    left, mid, right = st.columns([1.10, 1.25, 1.05], gap="large")

    with left:
        panel_gate_status()

    with mid:
        card_start("Program Control (TS concept)", "Manual selection: water status + pattern program → computed gate opening value (dummy)", "🧩")

        # In this view, show MANUAL selection concept
        st.session_state.water_status_source = "MANUAL"
        st.session_state.program_source = "MANUAL"

        row("Water status source", st.session_state.water_status_source, f"{st.session_state.water_status}%", "hmi-warn")
        row("Pattern program source", st.session_state.program_source, st.session_state.pattern, "hmi-warn")
        row("Season", st.session_state.season)

        # derive targets from pattern program (dummy)
        prog_map = {"A": 35, "B": 45, "C": 55, "D": 65}
        season_adj = 5 if st.session_state.season == "Wet" else 0
        status_adj = int((st.session_state.water_status - 80) * 0.4)
        st.session_state.open_target_pct = int(max(0, min(100, prog_map[st.session_state.pattern] + season_adj + status_adj)))

        # target discharge also shown (concept)
        st.session_state.q_target = round(12.50 + (st.session_state.open_target_pct - 55) * 0.02, 2)

        dev = deviation_pct(st.session_state.q_target, st.session_state.q_actual)
        within = abs(dev) <= 2.0

        row("Q_target (program)", f"{st.session_state.q_target:.2f} m³/s")
        row("Computed gate opening value", f"{st.session_state.open_target_pct}% (to LCP)")
        row("Q_actual", f"{st.session_state.q_actual:.2f} m³/s", f"Δ {dev:+.1f}%", "hmi-ok" if within else "hmi-warn")

        b1, b2, b3 = st.columns(3)
        with b1:
            if st.button("START PROGRAM", use_container_width=True, disabled=blocked):
                st.session_state.control_cycle = "RUNNING"
                send_cmd("PROGRAM START")
        with b2:
            if st.button("STOP PROGRAM", use_container_width=True):
                st.session_state.control_cycle = "IDLE"
                st.session_state.motion = "STOP"
                send_cmd("PROGRAM STOP")
        with b3:
            if st.button("APPLY 1 STEP", use_container_width=True, disabled=blocked):
                send_cmd("PROGRAM STEP")
                step_gate_toward(st.session_state.open_target_pct)

        row("Control cycle", st.session_state.control_cycle, None, "hmi-ok" if st.session_state.control_cycle=="RUNNING" else "hmi-warn")
        card_end()

        panel_hydrology_reference()

    with right:
        panel_alarms_interlocks()
        panel_power_generator()
        panel_cctv()

    st.markdown("")
    panel_trends()

# =========================
# Render mode
# =========================
if mode == "LOCAL (LCP ACTIVE)":
    view_local()
elif mode == "REMOTE MANUAL":
    view_remote_manual()
elif mode == "REMOTE AUTOMATIC":
    view_remote_automatic()
else:
    view_remote_program()

# =========================
# Auto refresh
# =========================
if auto_refresh:
    time.sleep(1)
    st.rerun()
