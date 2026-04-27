"""Dashboard Streamlit para monitoreo de somnolencia en tiempo real."""

from __future__ import annotations

import time
from collections import deque

import httpx
import plotly.graph_objects as go
import streamlit as st

# ── Configuración de la página ────────────────────────────────────
st.set_page_config(
    page_title="DrowsyGuard Monitor",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="collapsed",
)

API_BASE = "http://localhost:8000"
MAX_HISTORY = 60

# ── Estilos personalizados ────────────────────────────────────────
st.markdown(
    """
    <style>
        .stApp { background-color: #0d1117; color: #e6edf3; }
        .block-container { padding-top: 1rem; }
        .metric-value { font-size: 2.5rem !important; font-weight: 700; }
        .alert-NONE     { color: #3fb950; font-size: 1.8rem; font-weight: bold;
                          text-align:center; padding: 0.4rem 1rem;
                          border: 2px solid #3fb950; border-radius: 10px; }
        .alert-LOW      { color: #d29922; font-size: 1.8rem; font-weight: bold;
                          text-align:center; padding: 0.4rem 1rem;
                          border: 2px solid #d29922; border-radius: 10px; }
        .alert-HIGH     { color: #f85149; font-size: 1.8rem; font-weight: bold;
                          text-align:center; padding: 0.4rem 1rem;
                          border: 2px solid #f85149; border-radius: 10px; }
        .alert-CRITICAL {
            color: #ff0000; font-size: 1.8rem; font-weight: bold;
            text-align:center; padding: 0.4rem 1rem;
            border: 2px solid #ff0000; border-radius: 10px;
            animation: blink 0.4s step-start infinite;
        }
        @keyframes blink { 50% { opacity: 0; } }
        div[data-testid="metric-container"] {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 10px;
            padding: 1rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ── Funciones helper ──────────────────────────────────────────────
def fetch_metrics() -> dict:
    try:
        r = httpx.get(f"{API_BASE}/metrics/", timeout=1.0)
        return r.json()
    except Exception:
        return {}


def fetch_health() -> dict:
    try:
        r = httpx.get(f"{API_BASE}/health", timeout=1.0)
        return r.json()
    except Exception:
        return {}


def start_stream(source: int = 0) -> None:
    try:
        httpx.post(f"{API_BASE}/stream/start", json={"source": source}, timeout=5.0)
    except Exception:
        st.error("❌ No se pudo conectar con la API")


def stop_stream() -> None:
    try:
        httpx.post(f"{API_BASE}/stream/stop", timeout=5.0)
    except Exception:
        st.error("❌ No se pudo conectar con la API")


ALERT_NAMES = {0: "NONE", 1: "LOW", 2: "HIGH", 3: "CRITICAL"}
ALERT_ICONS = {0: "✅", 1: "⚠️", 2: "🔴", 3: "🚨"}
ALERT_COLORS = {0: "#3fb950", 1: "#d29922", 2: "#f85149", 3: "#ff0000"}

# ── Historial ─────────────────────────────────────────────────────
if "ear_history" not in st.session_state:
    st.session_state.ear_history = deque(maxlen=MAX_HISTORY)

# ── UI Principal ──────────────────────────────────────────────────
st.title("🚗 DrowsyGuard — Monitor en Tiempo Real")

health = fetch_health()
is_running = health.get("camera_connected", False)

# Controles
c1, c2, c3 = st.columns([1, 1, 6])
with c1:
    if st.button("▶ Iniciar", use_container_width=True, type="primary"):
        start_stream(source=0)
        st.rerun()
with c2:
    if st.button("⏹ Detener", use_container_width=True):
        stop_stream()
        st.rerun()

st.divider()

# ── Layout: Cámara | Métricas ─────────────────────────────────────
col_cam, col_metrics = st.columns([1.2, 1])

with col_cam:
    st.subheader("📷 Feed en Tiempo Real")
    if is_running:
        # Usamos el stream MJPEG directamente de la API
        st.image(f"{API_BASE}/stream/video")
    else:
        st.info("▶ Pulsa **Iniciar** para activar la cámara")

with col_metrics:
    data = fetch_metrics()
    alert = data.get("alert_level", 0)
    alert_name = ALERT_NAMES.get(alert, "NONE")

    if data:
        st.session_state.ear_history.append(data.get("ear", 0))

    # Banner de alerta
    st.markdown(
        f"<div class='alert-{alert_name}'>"
        f"{ALERT_ICONS.get(alert, '✅')} NIVEL: {alert_name}"
        f"</div>",
        unsafe_allow_html=True,
    )
    st.write("")

    # Métricas numéricas
    m1, m2 = st.columns(2)
    m1.metric("👁 EAR", f"{data.get('ear', 0):.3f}")
    m2.metric("📊 PERCLOS", f"{data.get('perclos', 0):.1%}")
    
    m3, m4 = st.columns(2)
    m3.metric("👄 MOR", f"{data.get('mor', 0):.3f}")
    m4.metric("🎯 FPS", f"{data.get('fps', 0):.0f}")

    # Gauge de PERCLOS
    fig_gauge = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=round(data.get("perclos", 0) * 100, 1),
            number={"suffix": "%", "font": {"color": "#e6edf3", "size": 28}},
            gauge={
                "axis": {"range": [0, 100], "tickcolor": "#e6edf3"},
                "bar": {"color": ALERT_COLORS.get(alert, "#3fb950")},
                "bgcolor": "#161b22",
                "steps": [
                    {"range": [0, 20], "color": "#0d1117"},
                    {"range": [20, 40], "color": "#1a2020"},
                    {"range": [40, 100], "color": "#2d1010"},
                ],
            },
        )
    )
    fig_gauge.update_layout(
        paper_bgcolor="#0d1117", font_color="#e6edf3", height=220, margin=dict(t=30, b=10, l=20, r=20)
    )
    st.plotly_chart(fig_gauge, use_container_width=True, key="gauge")

st.divider()

# ── Gráfico histórico EAR ──────────────────────────────
fig_ear = go.Figure()
fig_ear.add_trace(go.Scatter(y=list(st.session_state.ear_history), mode="lines", name="EAR", line=dict(color="#58a6ff", width=2)))
fig_ear.add_hline(y=0.25, line_dash="dash", line_color="#f85149")
fig_ear.update_layout(title="📈 Historial EAR", paper_bgcolor="#0d1117", plot_bgcolor="#161b22", font_color="#e6edf3", height=180, margin=dict(t=40, b=20, l=20, r=20), yaxis=dict(range=[0, 0.6]))
st.plotly_chart(fig_ear, use_container_width=True)

# Auto-update
if is_running:
    time.sleep(0.1)
    st.rerun()
