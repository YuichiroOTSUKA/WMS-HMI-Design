import streamlit as st
import streamlit.components.v1 as components
import time
from datetime import datetime
import random
import math

# =========================================================
# Page
# =========================================================
st.set_page_config(page_title="WMS HMI Demo (Gate Control Spec-aligned)", layout="wide")

# =========================================================
# UI / CSS
# =========================================================
st.markdown(
    """
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

/* Diverging bar (centered at 0) */
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
""",
    unsafe_allow_html=True,
)

# =========================================================
# Helpers (UI)
# =========================================================
def card_start(title: str, subtitle: str | None = None, icon: str = "◼"):
    st.markdown(
        f"""
<div class="hmi-card">
  <div class="hmi-title">{icon} {title}</div>
  {("<div class='hmi-sub'>" + subtitle + "</div>") if subtitle else ""}
""",
        unsafe_allow_html=True,
    )


def card_end():
    st.markdown("</div>", unsafe_allow_html=True)


def pill(label: str, klass="hmi-pill"):
    st.markdown(f"<span class='{klass}'>{label}</span>", unsafe_allow_html=True)


def row(key: str, val: str, badge_text: str | None = None, badge_class="hmi-ok"):
    b = (
        f"<span class='hmi-pill {badge_class}' style='margin-left:10px;'>{badge_text}</span>"
        if badge_text
        else ""
    )
    st.markdown(
        f"""
<div class="hmi-row">
  <div class="k">{key}</div>
  <div class="v">{val}{b}</div>
</div>
""",
        unsafe_allow_html=True,
    )


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
    st.markdown(
        f"<div class='bar-wrap'><div class='bar-fill' style='width:{p}%;'></div></div>",
        unsafe_allow_html=True,
    )


def diverging_bar(dev_pct: float, scale_pct: float = 10.0):
    d = max(-scale_pct, min(scale_pct, dev_pct))
    half = abs(d) / scale_pct * 50.0  # 0..50
    if d >= 0:
        st.markdown(
            f"""
<div class="div-wrap">
  <div class="div-center"></div>
  <div class="div-fill-pos" style='width:{half}%;'></div>
</div>
""",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
<div class="div-wrap">
  <div class="div-center"></div>
  <div class="div-fill-neg" style='width:{half}%;'></div>
</div>
""",
            unsafe_allow_html=True,
        )

    st.markdown(
        f"""
<div class="div-scale">
  <div>-{scale_pct:.0f}%</div>
  <div>0%</div>
  <div>+{scale_pct:.0f}%</div>
</div>
""",
        unsafe_allow_html=True,
    )


def pct_delta(base: float, value: float) -> float:
    if base == 0:
        return 0.0
    return (value - base) / base * 100.0


def dev_badge(abs_pct: float) -> str:
    if abs_pct <= 2.0:
        return "hmi-ok"
    if abs_pct <= 5.0:
        return "hmi-warn"
    return "hmi-bad"


# =========================================================
# Domain helpers (Gate Control)
# =========================================================
# Spec: gate speed is 0.3 m/min (global)
GATE_SPEED_M_PER_MIN = 0.3

# Spec: Remote Automatic checks Ktarget-Kact with ±5%
K_TOL_PCT = 5.0

# Spec: If cannot achieve target for > 1 hour after first execution, stop and alarm
AUTO_FAIL_TIMEOUT_SEC = 60 * 60


def opening_m_from_pct(open_pct: in
