import streamlit as st
import time
from datetime import datetime
import random

st.set_page_config(page_title="TC/SPC HMI Demo", layout="wide")

# ---------------------------
# Defaults
# ---------------------------
def init_defaults():
    ss = st.session_state
    if "opening_pct" not in ss: ss.opening_pct = 0
    if "target_pct" not in ss: ss.target_pct = 30
    if "moving" not in ss: ss.moving = "Stop"

    if "prot" not in ss:
        ss.prot = {
            "3E Protection": False,
            "ELR": False,
            "Overload": False,
            "Over Torque Open": False,
            "Over Torque Close": False,
            "Control De-Energize": False,
        }

    if "power" not in ss:
        ss.power = {"Commercial": True, "Generator": False, "GeneratorState": "OFF"}

    if "hydro" not in ss:
        ss.hydro = {
            "Upstream WL (m)": 2.35,
            "Downstream WL (m)": 1.80,
            "Discharge Now (m³/s)": 12.345,
            "Discharge Plan (m³/s)": 13.000,
            "Discharge Est. (m³/s)": 12.800,
            "Flood Level": "Normal",
        }

    if "water_status" not in ss: ss.water_status = 80
    if "program" not in ss:
        ss.program = {"ProgramID": "P-02", "Season": "Dry", "Phase": "Phase-1"}

    if "auto_running" not in ss: ss.auto_running = False
    if "prog_running" not in ss: ss.prog_running = False

init_defaults()

# ---------------------------
# Helpers
# ---------------------------
def badge(label: str, value: str, ok: bool = True):
    color = "#16a34a" if ok else "#ef4444"
    st.markdown(
        f"""
        <div style="padding:10px 12px;border-radius:12px;background:#0b1220;border:1px solid #1f2937;">
          <div style="font-size:12px;color:#94a3b8;">{label}</div>
          <div style="font-size:16px;font-weight:800;color:{color};">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def panel(title: str):
    st.markdown(f"<div style='font-size:16px;font-weight:900;margin:4px 0 8px 0;'>{title}</div>", unsafe_allow_html=True)
    st.markdown("<div style='background:#0b1220;border:1px solid #1f2937;border-radius:16px;padding:14px;'>", unsafe_allow_html=True)

def panel_end():
    st.markdown("</div>", unsafe_allow_html=True)

def gate_visual(opening_pct: int):
    st.progress(opening_pct / 100.0, text=f"Gate Opening: {opening_pct}%")
    st.markdown(
        f"""
        <div style="height:170px;border-radius:14px;border:1px solid #1f2937;background:#050a14;display:flex;align-items:center;justify-content:center;">
          <div style="text-align:center;">
            <div style="font-size:44px;font-weight:900;">{opening_pct}%</div>
            <div style="color:#94a3b8;font-size:12px;">(Dummy Gate Graphic Placeholder)</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def cctv_box(title="CCTV"):
    st.markdown(
        f"""
        <div style="height:220px;border-radius:14px;border:1px solid #1f2937;background:#050a14;display:flex;align-items:center;justify-content:center;">
          <div style="text-align:center;color:#94a3b8;">
            <div style="font-weight:900;margin-bottom:6px;">{title}</div>
            <div style="font-size:12px;">(Video placeholder)</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

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

# ---------------------------
# Sidebar (MODE SWITCH)  ★ここが今回の肝：key="mode" + session_state参照
# ---------------------------
st.sidebar.markdown("## TC/SPC HMI Demo")

st.sidebar.radio(
    "Control Mode Screen",
    [
        "LOCAL (LCP ACTIVE)",
        "REMOTE MANUAL",
        "REMOTE AUTOMATIC",
        "REMOTE PROGRAM",
    ],
    key="mode"
)
mode = st.session_state["mode"]  # 以後は必ずこれで分岐

# Dummy controls
st.sidebar.markdown("---")
st.sidebar.markdown("### Demo Controls (dummy)")
if st.sidebar.button("Simulate comm update / refresh"):
    h = st.session_state.hydro.copy()
    h["Upstream WL (m)"] = round(h["Upstream WL (m)"] + random.uniform(-0.03, 0.03), 2)
    h["Downstream WL (m)"] = round(h["Downstream WL (m)"] + random.uniform(-0.03, 0.03), 2)
    h["Discharge Now (m³/s)"] = round(h["Discharge Now (m³/s)"] + random.uniform(-0.2, 0.2), 3)
    st.session_state.hydro = h

st.sidebar.markdown("### Safety flags")
for k in list(st.session_state.prot.keys()):
    st.session_state.prot[k] = st.sidebar.checkbox(k, value=st.session_state.prot[k])

st.sidebar.markdown("### Power")
st.session_state.power["Commercial"] = st.sidebar.checkbox("Commercial Power", value=st.session_state.power["Commercial"])
st.session_state.power["Generator"] = st.sidebar.checkbox("Generator Available", value=st.session_state.power["Generator"])
st.session_state.power["GeneratorState"] = st.sidebar.selectbox(
    "Generator State",
    ["OFF", "READY", "RUNNING", "ERROR"],
    index=["OFF","READY","RUNNING","ERROR"].index(st.session_state.power["GeneratorState"])
)

st.sidebar.markdown("### Water status / Program")
st.session_state.water_status = st.sidebar.select_slider("Water Status (%)", options=[100, 90, 80, 70, 60], value=st.session_state.water_status)
st.session_state.program["ProgramID"] = st.sidebar.selectbox("Program ID", ["P-01", "P-02", "P-03"], index=["P-01","P-02","P-03"].index(st.session_state.program["ProgramID"]))
st.session_state.program["Season"] = st.sidebar.selectbox("Season", ["Dry", "Wet"], index=["Dry","Wet"].index(st.session_state.program["Season"]))
st.session_state.program["Phase"] = st.sidebar.selectbox("Phase", ["Phase-1", "Phase-2", "Phase-3"], index=["Phase-1","Phase-2","Phase-3"].index(st.session_state.program["Phase"]))

# ---------------------------
# Top header
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

# Ops block rules (demo)
any_trip = any(st.session_state.prot.values())
ops_blocked = (mode == "LOCAL (LCP ACTIVE)") or any_trip or (st.session_state.power["GeneratorState"] == "ERROR")

# ---------------------------
# Views (mode-based)
# ---------------------------
if mode == "LOCAL (LCP ACTIVE)":
    left, mid, right = st.columns([1.2, 1.3, 1.1], gap="large")

    with left:
        panel("Access / Lock")
        st.write("**Remote Control:** Disabled (Local LCP Active)")
        st.write("**Reason:** Operation is currently controlled at site.")
        panel_end()

        panel("Protection / Alarms")
        for k, v in st.session_state.prot.items():
            st.write(f"- {k}: {'ON' if v else 'OFF'}")
        panel_end()

    with mid:
        panel("Gate Status")
        gate_visual(st.session_state.opening_pct)
        st.write(f"Motion: **{st.session_state.moving}**")
        st.write(f"Fully Open: **{'YES' if st.session_state.opening_pct >= 100 else 'NO'}**")
        st.write(f"Fully Close: **{'YES' if st.session_state.opening_pct <= 0 else 'NO'}**")
        panel_end()

        panel("Hydrology (Reference)")
        h = st.session_state.hydro
        st.write(f"Upstream WL: **{h['Upstream WL (m)']} m**")
        st.write(f"Downstream WL: **{h['Downstream WL (m)']} m**")
        st.write(f"Discharge Now: **{h['Discharge Now (m³/s)']} m³/s**")
        st.write(f"Flood Level: **{h['Flood Level']}**")
        panel_end()

    with right:
        panel("CCTV (View only)")
        cctv_box("CCTV — Utara Kidul Uyee")
        st.button("Manage CCTV (disabled in LOCAL)", disabled=True, use_container_width=True)
        panel_end()

        panel("Power")
        p = st.session_state.power
        st.write(f"Commercial: **{'ON' if p['Commercial'] else 'OFF'}**")
        st.write(f"Generator: **{'YES' if p['Generator'] else 'NO'}**")
        st.write(f"Gen. State: **{p['GeneratorState']}**")
        panel_end()

elif mode == "REMOTE MANUAL":
    left, mid, right = st.columns([1.2, 1.3, 1.1], gap="large")

    with left:
        panel("Safety / Interlocks")
        st.write(f"Operations blocked: **{'YES' if ops_blocked else 'NO'}**")
        if any_trip:
            st.error("Protection active: manual operation is blocked.")
        if st.session_state.power["GeneratorState"] == "ERROR":
            st.error("Generator ERROR: operation blocked.")
        panel_end()

        panel("Protection / Alarms")
        for k, v in st.session_state.prot.items():
            st.write(f"- {k}: {'ON' if v else 'OFF'}")
        panel_end()

    with mid:
        panel("Gate Status")
        gate_visual(st.session_state.opening_pct)
        st.write(f"Motion: **{st.session_state.moving}**")
        panel_end()

        panel("Command Panel (Remote Manual)")
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("OPEN", use_container_width=True, disabled=ops_blocked):
                st.session_state.moving = "Opening"
                step_motion()
        with c2:
            if st.button("STOP", use_container_width=True, disabled=ops_blocked):
                st.session_state.moving = "Stop"
        with c3:
            if st.button("CLOSE", use_container_width=True, disabled=ops_blocked):
                st.session_state.moving = "Closing"
                step_motion()
        st.caption("Command status: dummy immediate execution (no real comm).")
        panel_end()

    with right:
        panel("CCTV (PTZ)")
        cctv_box("CCTV — Gate Area")
        r1, r2, r3 = st.columns(3)
        r1.button("Pan ◀", use_container_width=True)
        r2.button("Tilt ▲", use_container_width=True)
        r3.button("Zoom +", use_container_width=True)
        r4, r5, r6 = st.columns(3)
        r4.button("Pan ▶", use_container_width=True)
        r5.button("Tilt ▼", use_container_width=True)
        r6.button("Zoom -", use_container_width=True)
        panel_end()

        panel("Hydrology (Reference)")
        h = st.session_state.hydro
        st.write(f"Upstream WL: **{h['Upstream WL (m)']} m**")
        st.write(f"Downstream WL: **{h['Downstream WL (m)']} m**")
        st.write(f"Discharge Now: **{h['Discharge Now (m³/s)']} m³/s**")
        panel_end()

elif mode == "REMOTE AUTOMATIC":
    left, mid, right = st.columns([1.15, 1.45, 1.0], gap="large")

    with left:
        panel("Auto Context (Why)")
        st.write(f"Water Status: **{st.session_state.water_status}%**")
        h = st.session_state.hydro
        st.write(f"Upstream WL: **{h['Upstream WL (m)']} m**")
        st.write(f"Downstream WL: **{h['Downstream WL (m)']} m**")
        st.write(f"Discharge Now: **{h['Discharge Now (m³/s)']} m³/s**")
        st.write(f"Discharge Plan: **{h['Discharge Plan (m³/s)']} m³/s**")
        st.write(f"Discharge Est.: **{h['Discharge Est. (m³/s)']} m³/s**")
        panel_end()

        panel("Protection / Alarms")
        for k, v in st.session_state.prot.items():
            st.write(f"- {k}: {'ON' if v else 'OFF'}")
        panel_end()

    with mid:
        panel("Set Point Control View")
        st.session_state.target_pct = st.slider("Target Opening (Z_target) [%]", 0, 100, st.session_state.target_pct)
        actual = st.session_state.opening_pct
        target = st.session_state.target_pct
        delta = target - actual

        cA, cB, cC = st.columns(3)
        with cA: badge("Z_actual", f"{actual}%", ok=True)
        with cB: badge("Z_target", f"{target}%", ok=True)
        with cC: badge("ΔZ", f"{delta:+d}%", ok=(abs(delta) <= 10))

        gate_visual(actual)

        b1, b2, b3 = st.columns(3)
        with b1:
            if st.button("START AUTO", use_container_width=True, disabled=ops_blocked):
                st.session_state.auto_running = True
        with b2:
            if st.button("STOP AUTO", use_container_width=True):
                st.session_state.auto_running = False
                st.session_state.moving = "Stop"
        with b3:
            if st.button("SWITCH TO MANUAL (demo)", use_container_width=True):
                st.session_state.auto_running = False
                st.session_state.moving = "Stop"
                st.info("Use sidebar to switch to REMOTE MANUAL.")

        if st.session_state.auto_running and not ops_blocked:
            auto_tick()

        if ops_blocked:
            st.write("Auto Status: **Suspended (Blocked)**")
        else:
            st.write("Auto Status: **Adjusting**" if abs(target - st.session_state.opening_pct) > 1 else "Auto Status: **Reached**")
        st.write(f"Motion: **{st.session_state.moving}**")
        panel_end()

    with right:
        panel("CCTV")
        cctv_box("CCTV — Gate Area")
        st.button("Manage CCTV", use_container_width=True)
        panel_end()

        panel("Exception Reason (demo)")
        if any_trip:
            st.error("Protection active: Auto suspended.")
        elif st.session_state.hydro["Flood Level"] != "Normal":
            st.warning("Flood level not normal: Auto may be limited.")
        else:
            st.success("No exception.")
        panel_end()

elif mode == "REMOTE PROGRAM":
    left, mid, right = st.columns([1.15, 1.45, 1.0], gap="large")

    with left:
        panel("Program Selection / Summary")
        pr = st.session_state.program
        st.write(f"Program ID: **{pr['ProgramID']}**")
        st.write(f"Season: **{pr['Season']}**")
        st.write(f"Phase: **{pr['Phase']}**")
        st.write(f"Water Status: **{st.session_state.water_status}%**")
        st.write("---")
        st.write("Program definition summary (dummy):")
        st.write("- Pattern-based target opening")
        st.write("- Phase-based progression")
        panel_end()

        panel("Safety / Interlocks")
        st.write(f"Operations blocked: **{'YES' if ops_blocked else 'NO'}**")
        if any_trip:
            st.error("Protection active: program operation is blocked.")
        panel_end()

    with mid:
        panel("Program Execution")
        pr = st.session_state.program

        base = {"P-01": 20, "P-02": 35, "P-03": 50}[pr["ProgramID"]]
        season_adj = 10 if pr["Season"] == "Wet" else 0
        phase_adj = {"Phase-1": 0, "Phase-2": 10, "Phase-3": 20}[pr["Phase"]]
        st.session_state.target_pct = min(100, base + season_adj + phase_adj)

        actual = st.session_state.opening_pct
        target = st.session_state.target_pct
        delta = target - actual

        cA, cB, cC = st.columns(3)
        with cA: badge("Program Target", f"{target}%", ok=True)
        with cB: badge("Z_actual", f"{actual}%", ok=True)
        with cC: badge("ΔZ", f"{delta:+d}%", ok=(abs(delta) <= 10))

        gate_visual(actual)

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

        prog = int(100 - min(100, abs(target - st.session_state.opening_pct)))
        st.progress(prog / 100.0, text=f"Program Progress (dummy): {prog}%")

        if ops_blocked:
            st.write("Program Status: **Suspended (Blocked)**")
        else:
            st.write("Program Status: **Running**" if st.session_state.prog_running else "Program Status: **Stopped**")
        panel_end()

    with right:
        panel("CCTV")
        cctv_box("CCTV — Gate Area")
        st.button("Manage CCTV", use_container_width=True)
        panel_end()

        panel("Hydrology (Reference)")
        h = st.session_state.hydro
        st.write(f"Upstream WL: **{h['Upstream WL (m)']} m**")
        st.write(f"Downstream WL: **{h['Downstream WL (m)']} m**")
        st.write(f"Discharge Now: **{h['Discharge Now (m³/s)']} m³/s**")
        panel_end()

# Auto refresh (optional)
st.markdown("---")
auto_refresh = st.checkbox("Auto refresh (1s tick) — useful for auto/program motion demo", value=False)
if auto_refresh:
    time.sleep(1)
    st.rerun()
