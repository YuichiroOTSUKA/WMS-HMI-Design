import streamlit as st
import time
from datetime import datetime
import random

st.set_page_config(page_title="TC/SPC HMI Demo", layout="wide")

# ---------------------------
# Dummy data generator
# ---------------------------
def dummy_state(mode: str):
    # Gate status
    opening_pct = st.session_state.get("opening_pct", 0)
    target_pct  = st.session_state.get("target_pct", 0)

    moving = st.session_state.get("moving", "Stop")
    fully_open = opening_pct >= 100
    fully_close = opening_pct <= 0

    # protection flags
    prot = st.session_state.get("prot", {
        "3E Protection": False,
        "ELR": False,
        "Overload": False,
        "Over Torque Open": False,
        "Over Torque Close": False,
        "Control De-Energize": False,
    })

    # power
    power = st.session_state.get("power", {"Commercial": True, "Generator": False, "GeneratorState": "OFF"})

    # hydro/meteo (dummy)
    hydro = st.session_state.get("hydro", {
        "Upstream WL (m)": 2.35,
        "Downstream WL (m)": 1.80,
        "Discharge Now (m³/s)": 12.345,
        "Discharge Plan (m³/s)": 13.000,
        "Discharge Est. (m³/s)": 12.800,
        "Flood Level": "Normal"
    })

    water_status = st.session_state.get("water_status", 80)
    program = st.session_state.get("program", {"ProgramID": "P-02", "Season": "Dry", "Phase": "Phase-1"})

    # mode lock rules (demo)
    remote_enabled = mode != "LOCAL (LCP ACTIVE)"
    operation_allowed = mode in ["REMOTE MANUAL", "REMOTE AUTOMATIC", "REMOTE PROGRAM"]

    return {
        "opening_pct": opening_pct,
        "target_pct": target_pct,
        "moving": moving,
        "fully_open": fully_open,
        "fully_close": fully_close,
        "prot": prot,
        "power": power,
        "hydro": hydro,
        "water_status": water_status,
        "program": program,
        "remote_enabled": remote_enabled,
        "operation_allowed": operation_allowed,
    }

def set_moving(status: str):
    st.session_state["moving"] = status

def step_motion():
    # simple motion model: +2/-2 per tick
    opening_pct = st.session_state.get("opening_pct", 0)
    moving = st.session_state.get("moving", "Stop")

    if moving == "Opening":
        opening_pct = min(100, opening_pct + 2)
    elif moving == "Closing":
        opening_pct = max(0, opening_pct - 2)

    # auto stop at ends
    if opening_pct in (0, 100):
        st.session_state["moving"] = "Stop"

    st.session_state["opening_pct"] = opening_pct

def auto_control_tick():
    # move toward target
    opening_pct = st.session_state.get("opening_pct", 0)
    target_pct = st.session_state.get("target_pct", 0)

    if abs(opening_pct - target_pct) <= 1:
        st.session_state["moving"] = "Stop"
        return

    if opening_pct < target_pct:
        st.session_state["moving"] = "Opening"
    else:
        st.session_state["moving"] = "Closing"

    step_motion()

def init_defaults():
    if "opening_pct" not in st.session_state:
        st.session_state["opening_pct"] = 0
    if "target_pct" not in st.session_state:
        st.session_state["target_pct"] = 30
    if "moving" not in st.session_state:
        st.session_state["moving"] = "Stop"
    if "prot" not in st.session_state:
        st.session_state["prot"] = {
            "3E Protection": False,
            "ELR": False,
            "Overload": False,
            "Over Torque Open": False,
            "Over Torque Close": False,
            "Control De-Energize": False,
        }
    if "power" not in st.session_state:
        st.session_state["power"] = {"Commercial": True, "Generator": False, "GeneratorState": "OFF"}
    if "hydro" not in st.session_state:
        st.session_state["hydro"] = {
            "Upstream WL (m)": 2.35,
            "Downstream WL (m)": 1.80,
            "Discharge Now (m³/s)": 12.345,
            "Discharge Plan (m³/s)": 13.000,
            "Discharge Est. (m³/s)": 12.800,
            "Flood Level": "Normal"
        }
    if "water_status" not in st.session_state:
        st.session_state["water_status"] = 80
    if "program" not in st.session_state:
        st.session_state["program"] = {"ProgramID": "P-02", "Season": "Dry", "Phase": "Phase-1"}
    if "auto_running" not in st.session_state:
        st.session_state["auto_running"] = False
    if "prog_running" not in st.session_state:
        st.session_state["prog_running"] = False

init_defaults()

# ---------------------------
# UI helpers
# ---------------------------
def badge(label: str, value: str, ok: bool = True):
    color = "#16a34a" if ok else "#dc2626"
    st.markdown(
        f"""
        <div style="padding:10px 12px;border-radius:12px;background:#0b1220;border:1px solid #1f2937;">
          <div style="font-size:12px;color:#94a3b8;">{label}</div>
          <div style="font-size:16px;font-weight:700;color:{color};">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def section_title(text: str):
    st.markdown(f"<div style='font-size:18px;font-weight:800;margin:6px 0 10px 0;'>{text}</div>", unsafe_allow_html=True)

def panel_box_start():
    st.markdown(
        "<div style='background:#0b1220;border:1px solid #1f2937;border-radius:16px;padding:14px 14px 10px 14px;'>",
        unsafe_allow_html=True,
    )

def panel_box_end():
    st.markdown("</div>", unsafe_allow_html=True)

def gate_visual(opening_pct: int):
    # simple progress + status
    st.progress(opening_pct / 100.0, text=f"Gate Opening: {opening_pct}%")
    st.markdown(
        f"""
        <div style="height:180px;border-radius:14px;border:1px solid #1f2937;background:#0b1220;display:flex;align-items:center;justify-content:center;">
          <div style="text-align:center;">
            <div style="font-size:44px;font-weight:900;">{opening_pct}%</div>
            <div style="color:#94a3b8;">(Dummy Gate Graphic Placeholder)</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def cctv_placeholder(title="CCTV"):
    st.markdown(
        f"""
        <div style="height:220px;border-radius:14px;border:1px solid #1f2937;background:#050a14;display:flex;align-items:center;justify-content:center;">
          <div style="text-align:center;color:#94a3b8;">
            <div style="font-weight:800;margin-bottom:6px;">{title}</div>
            <div style="font-size:12px;">(Video placeholder)</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------------------------
# Sidebar navigation
# ---------------------------
st.sidebar.markdown("## TC/SPC HMI Demo")
mode = st.sidebar.radio(
    "Control Mode Screen",
    ["LOCAL (LCP ACTIVE)", "REMOTE MANUAL", "REMOTE AUTOMATIC", "REMOTE PROGRAM"],
    index=1
)

st.sidebar.markdown("---")
st.sidebar.markdown("### Demo Controls (dummy)")
if st.sidebar.button("Simulate comm update / refresh"):
    # jitter hydrology a bit
    h = st.session_state["hydro"].copy()
    h["Upstream WL (m)"] = round(h["Upstream WL (m)"] + random.uniform(-0.03, 0.03), 2)
    h["Downstream WL (m)"] = round(h["Downstream WL (m)"] + random.uniform(-0.03, 0.03), 2)
    h["Discharge Now (m³/s)"] = round(h["Discharge Now (m³/s)"] + random.uniform(-0.2, 0.2), 3)
    st.session_state["hydro"] = h

st.sidebar.markdown("### Safety flags")
for k in list(st.session_state["prot"].keys()):
    st.session_state["prot"][k] = st.sidebar.checkbox(k, value=st.session_state["prot"][k])

st.sidebar.markdown("### Power")
st.session_state["power"]["Commercial"] = st.sidebar.checkbox("Commercial Power", value=st.session_state["power"]["Commercial"])
st.session_state["power"]["Generator"] = st.sidebar.checkbox("Generator Available", value=st.session_state["power"]["Generator"])
st.session_state["power"]["GeneratorState"] = st.sidebar.selectbox("Generator State", ["OFF", "READY", "RUNNING", "ERROR"],
                                                                  index=["OFF","READY","RUNNING","ERROR"].index(st.session_state["power"]["GeneratorState"]))

st.sidebar.markdown("### Water status / Program")
st.session_state["water_status"] = st.sidebar.select_slider("Water Status (%)", options=[100, 90, 80, 70, 60], value=st.session_state["water_status"])
st.session_state["program"]["ProgramID"] = st.sidebar.selectbox("Program ID", ["P-01", "P-02", "P-03"], index=["P-01","P-02","P-03"].index(st.session_state["program"]["ProgramID"]))
st.session_state["program"]["Season"] = st.sidebar.selectbox("Season", ["Dry", "Wet"], index=["Dry","Wet"].index(st.session_state["program"]["Season"]))
st.session_state["program"]["Phase"] = st.sidebar.selectbox("Phase", ["Phase-1", "Phase-2", "Phase-3"], index=["Phase-1","Phase-2","Phase-3"].index(st.session_state["program"]["Phase"]))

# ---------------------------
# Header
# ---------------------------
colA, colB, colC, colD = st.columns([2.2, 1.2, 1.2, 1.4])
with colA:
    st.markdown("## BUT10 — Gate1 Control (Demo)")
    st.caption("Reference layout inspired by provided BUT10 screenshot. Dummy data only.")
with colB:
    badge("CONTROL MODE", mode, ok=(mode != "LOCAL (LCP ACTIVE)"))
with colC:
    badge("SYSTEM STATUS", "ACTIVE", ok=True)
with colD:
    badge("LAST UPDATE", datetime.now().strftime("%d/%m/%Y %H:%M:%S"), ok=True)

state = dummy_state(mode)

# Helper: determine if operations should be disabled (e.g., protections or local)
any_trip = any(state["prot"].values())
ops_blocked = (mode == "LOCAL (LCP ACTIVE)") or any_trip or (state["power"]["GeneratorState"] == "ERROR")

# ---------------------------
# Screen layouts per mode
# ---------------------------
if mode == "LOCAL (LCP ACTIVE)":
    # LOCAL: monitor only, controls disabled
    left, mid, right = st.columns([1.2, 1.3, 1.1], gap="large")

    with left:
        section_title("Access / Lock")
        panel_box_start()
        st.markdown("**Remote Control:** Disabled (Local LCP Active)")
        st.markdown("**Reason:** Operation is currently controlled at site.")
        st.divider()
        section_title("Protection / Alarms")
        for k, v in state["prot"].items():
            st.write(f"- {k}: {'ON' if v else 'OFF'}")
        panel_box_end()

    with mid:
        section_title("Gate Status")
        panel_box_start()
        gate_visual(state["opening_pct"])
        st.write(f"Motion: **{state['moving']}**")
        st.write(f"Fully Open: **{'YES' if state['fully_open'] else 'NO'}**")
        st.write(f"Fully Close: **{'YES' if state['fully_close'] else 'NO'}**")
        panel_box_end()

        section_title("Hydrology (Reference)")
        panel_box_start()
        h = state["hydro"]
        st.write(f"Upstream WL: **{h['Upstream WL (m)']} m**")
        st.write(f"Downstream WL: **{h['Downstream WL (m)']} m**")
        st.write(f"Discharge Now: **{h['Discharge Now (m³/s)']} m³/s**")
        st.write(f"Flood Level: **{h['Flood Level']}**")
        panel_box_end()

    with right:
        section_title("CCTV (View only)")
        cctv_placeholder("CCTV — Utara Kidul Uyee")
        st.button("Manage CCTV (disabled in LOCAL)", disabled=True)

        section_title("Power")
        panel_box_start()
        p = state["power"]
        st.write(f"Commercial: **{'ON' if p['Commercial'] else 'OFF'}**")
        st.write(f"Generator: **{'YES' if p['Generator'] else 'NO'}**")
        st.write(f"Gen. State: **{p['GeneratorState']}**")
        panel_box_end()

elif mode == "REMOTE MANUAL":
    # MANUAL: big controls
    left, mid, right = st.columns([1.2, 1.3, 1.1], gap="large")

    with left:
        section_title("Safety / Interlocks")
        panel_box_start()
        st.write(f"Operations blocked: **{'YES' if ops_blocked else 'NO'}**")
        if any_trip:
            st.error("Protection active: manual operation is blocked.")
        if state["power"]["GeneratorState"] == "ERROR":
            st.error("Generator ERROR: operation blocked.")
        st.divider()
        for k, v in state["prot"].items():
            st.write(f"- {k}: {'ON' if v else 'OFF'}")
        panel_box_end()

        section_title("Power")
        panel_box_start()
        p = state["power"]
        st.write(f"Commercial: **{'ON' if p['Commercial'] else 'OFF'}**")
        st.write(f"Generator State: **{p['GeneratorState']}**")
        panel_box_end()

    with mid:
        section_title("Gate Status")
        panel_box_start()
        gate_visual(state["opening_pct"])
        st.write(f"Motion: **{state['moving']}**")
        st.write(f"Fully Open: **{'YES' if state['fully_open'] else 'NO'}**")
        st.write(f"Fully Close: **{'YES' if state['fully_close'] else 'NO'}**")
        panel_box_end()

        section_title("Command Panel (Remote Manual)")
        panel_box_start()
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("OPEN", use_container_width=True, disabled=ops_blocked):
                set_moving("Opening")
                step_motion()
        with c2:
            if st.button("STOP", use_container_width=True, disabled=ops_blocked):
                set_moving("Stop")
        with c3:
            if st.button("CLOSE", use_container_width=True, disabled=ops_blocked):
                set_moving("Closing")
                step_motion()

        st.caption("Command status: dummy immediate execution (no real comm).")
        panel_box_end()

    with right:
        section_title("CCTV (PTZ)")
        cctv_placeholder("CCTV — Utara Kidul Uyee")
        cptz1, cptz2, cptz3 = st.columns(3)
        with cptz1:
            st.button("Pan ◀", use_container_width=True)
        with cptz2:
            st.button("Tilt ▲", use_container_width=True)
        with cptz3:
            st.button("Zoom +", use_container_width=True)
        cptz4, cptz5, cptz6 = st.columns(3)
        with cptz4:
            st.button("Pan ▶", use_container_width=True)
        with cptz5:
            st.button("Tilt ▼", use_container_width=True)
        with cptz6:
            st.button("Zoom -", use_container_width=True)

        section_title("Hydrology (Reference)")
        panel_box_start()
        h = state["hydro"]
        st.write(f"Upstream WL: **{h['Upstream WL (m)']} m**")
        st.write(f"Downstream WL: **{h['Downstream WL (m)']} m**")
        st.write(f"Discharge Now: **{h['Discharge Now (m³/s)']} m³/s**")
        panel_box_end()

elif mode == "REMOTE AUTOMATIC":
    # AUTOMATIC: show target vs actual and auto control
    left, mid, right = st.columns([1.15, 1.45, 1.0], gap="large")

    with left:
        section_title("Auto Context (Why)")
        panel_box_start()
        st.write(f"Water Status: **{state['water_status']}%**")
        h = state["hydro"]
        st.write(f"Upstream WL: **{h['Upstream WL (m)']} m**")
        st.write(f"Downstream WL: **{h['Downstream WL (m)']} m**")
        st.write(f"Discharge Now: **{h['Discharge Now (m³/s)']} m³/s**")
        st.write(f"Discharge Plan: **{h['Discharge Plan (m³/s)']} m³/s**")
        st.write(f"Discharge Est.: **{h['Discharge Est. (m³/s)']} m³/s**")
        st.divider()
        st.write(f"Operations blocked: **{'YES' if ops_blocked else 'NO'}**")
        panel_box_end()

        section_title("Protection / Alarms")
        panel_box_start()
        for k, v in state["prot"].items():
            st.write(f"- {k}: {'ON' if v else 'OFF'}")
        panel_box_end()

    with mid:
        section_title("Set Point Control View")
        panel_box_start()

        # target setting (dummy)
        st.session_state["target_pct"] = st.slider("Target Opening (Z_target) [%]", 0, 100, st.session_state["target_pct"])

        actual = st.session_state["opening_pct"]
        target = st.session_state["target_pct"]
        delta = target - actual

        cA, cB, cC = st.columns(3)
        with cA:
            badge("Z_actual", f"{actual}%", ok=True)
        with cB:
            badge("Z_target", f"{target}%", ok=True)
        with cC:
            badge("ΔZ", f"{delta:+d}%", ok=(abs(delta) <= 10))

        gate_visual(actual)

        # Auto control buttons
        c1, c2, c3 = st.columns([1,1,1])
        with c1:
            if st.button("START AUTO", use_container_width=True, disabled=ops_blocked):
                st.session_state["auto_running"] = True
        with c2:
            if st.button("STOP AUTO", use_container_width=True, disabled=False):
                st.session_state["auto_running"] = False
                set_moving("Stop")
        with c3:
            if st.button("SWITCH TO MANUAL (demo)", use_container_width=True):
                st.session_state["auto_running"] = False
                set_moving("Stop")
                st.info("Use sidebar to switch to REMOTE MANUAL.")

        # Run one tick per rerun if auto_running
        if st.session_state["auto_running"] and not ops_blocked:
            auto_control_tick()

        auto_status = "Adjusting" if st.session_state["auto_running"] and not ops_blocked and abs(delta) > 1 else "Reached"
        if ops_blocked:
            auto_status = "Suspended (Blocked)"
        st.write(f"Auto Status: **{auto_status}**")
        st.write(f"Motion: **{st.session_state['moving']}**")

        panel_box_end()

    with right:
        section_title("CCTV")
        cctv_placeholder("CCTV — Gate Area")
        st.button("Manage CCTV", use_container_width=True)

        section_title("Exception Reason (demo)")
        panel_box_start()
        if any_trip:
            st.error("Protection active: Auto suspended.")
        elif state["hydro"]["Flood Level"] != "Normal":
            st.warning("Flood level not normal: Auto may be limited.")
        else:
            st.success("No exception.")
        panel_box_end()

elif mode == "REMOTE PROGRAM":
    # PROGRAM: select program, run/stop, show progress
    left, mid, right = st.columns([1.15, 1.45, 1.0], gap="large")

    with left:
        section_title("Program Selection / Summary")
        panel_box_start()
        st.write(f"Program ID: **{state['program']['ProgramID']}**")
        st.write(f"Season: **{state['program']['Season']}**")
        st.write(f"Phase: **{state['program']['Phase']}**")
        st.write(f"Water Status: **{state['water_status']}%**")
        st.divider()
        st.write("Program definition summary (dummy):")
        st.write("- Pattern-based target opening")
        st.write("- Phase-based progression")
        panel_box_end()

        section_title("Safety / Interlocks")
        panel_box_start()
        st.write(f"Operations blocked: **{'YES' if ops_blocked else 'NO'}**")
        if any_trip:
            st.error("Protection active: program operation is blocked.")
        panel_box_end()

    with mid:
        section_title("Program Execution")
        panel_box_start()

        # Derive a dummy target from program selection
        prog_id = state["program"]["ProgramID"]
        season = state["program"]["Season"]
        phase = state["program"]["Phase"]

        base = {"P-01": 20, "P-02": 35, "P-03": 50}[prog_id]
        season_adj = 10 if season == "Wet" else 0
        phase_adj = {"Phase-1": 0, "Phase-2": 10, "Phase-3": 20}[phase]
        target = min(100, base + season_adj + phase_adj)
        st.session_state["target_pct"] = target

        actual = st.session_state["opening_pct"]
        delta = target - actual

        cA, cB, cC = st.columns(3)
        with cA:
            badge("Program Target", f"{target}%", ok=True)
        with cB:
            badge("Z_actual", f"{actual}%", ok=True)
        with cC:
            badge("ΔZ", f"{delta:+d}%", ok=(abs(delta) <= 10))

        gate_visual(actual)

        # Program controls
        c1, c2, c3 = st.columns([1,1,1])
        with c1:
            if st.button("START PROGRAM", use_container_width=True, disabled=ops_blocked):
                st.session_state["prog_running"] = True
        with c2:
            if st.button("STOP PROGRAM", use_container_width=True):
                st.session_state["prog_running"] = False
                set_moving("Stop")
        with c3:
            if st.button("EMERGENCY STOP", use_container_width=True, disabled=False):
                st.session_state["prog_running"] = False
                set_moving("Stop")
                st.warning("Emergency stop executed (dummy).")

        # Run one tick per rerun if prog_running
        if st.session_state["prog_running"] and not ops_blocked:
            auto_control_tick()

        progress = int(100 - min(100, abs(delta)))  # dummy
        st.progress(progress / 100.0, text=f"Program Progress (dummy): {progress}%")
        run_status = "Running" if st.session_state["prog_running"] and not ops_blocked else "Stopped"
        if ops_blocked:
            run_status = "Suspended (Blocked)"
        st.write(f"Program Status: **{run_status}**")

        panel_box_end()

    with right:
        section_title("CCTV")
        cctv_placeholder("CCTV — Gate Area")
        st.button("Manage CCTV", use_container_width=True)

        section_title("Hydrology (Reference)")
        panel_box_start()
        h = state["hydro"]
        st.write(f"Upstream WL: **{h['Upstream WL (m)']} m**")
        st.write(f"Downstream WL: **{h['Downstream WL (m)']} m**")
        st.write(f"Discharge Now: **{h['Discharge Now (m³/s)']} m³/s**")
        panel_box_end()

# Small auto-refresh option
st.markdown("---")
auto_refresh = st.checkbox("Auto refresh (1s tick) — useful for auto/program motion demo", value=False)
if auto_refresh:
    time.sleep(1)
    st.rerun()
