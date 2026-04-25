"""Dashboard Streamlit para monitoreo de somnolencia en tiempo real."""
from __future__ import annotations

import time
from collections import deque
import random
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
MAX_HISTORY = 30  # Últimos 30 puntos en el gráfico

# ── Estilos personalizados ────────────────────────────────────────
st.markdown(
    """
    <style>
        .stApp { background-color: #0d1117; color: #e6edf3; }
        .block-container { padding-top: 1rem; }
        .metric-value { font-size: 2.5rem !important; font-weight: 700; }
        .alert-NONE     { color: #3fb950; font-size: 1.8rem; font-weight: bold; }
        .alert-LOW      { color: #d29922; font-size: 1.8rem; font-weight: bold; }
        .alert-HIGH     { color: #f85149; font-size: 1.8rem; font-weight: bold; }
        .alert-CRITICAL {
            color: #ff0000; font-size: 1.8rem; font-weight: bold;
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
@st.cache_data(ttl=1)

def fetch_metrics():
    return {
        "ear": round(random.uniform(0.2, 0.4), 3),
        "mor": round(random.uniform(0.3, 0.7), 3),
        "perclos": round(random.uniform(0.1, 0.6), 2),
        "fps": random.randint(15, 25),
        "alert_level": random.randint(0, 3)
    }


@st.cache_data(ttl=5)
def fetch_health():
    return {
        "status": "ok",
        "camera_connected": True,
        "uptime_seconds": 120
    }


def start_stream(source: int = 0):
    try:
        httpx.post(f"{API_BASE}/stream/start", json={"source": source}, timeout=5.0)
    except Exception:
        st.error("❌ No se pudo conectar con la API en localhost:8000")


def stop_stream():
    try:
        httpx.post(f"{API_BASE}/stream/stop", timeout=5.0)
    except Exception:
        st.error("❌ No se pudo conectar con la API en localhost:8000")


ALERT_NAMES = {0: "NONE", 1: "LOW", 2: "HIGH", 3: "CRITICAL"}
ALERT_ICONS = {0: "✅", 1: "⚠️", 2: "🔴", 3: "🚨"}

# ── UI Principal ──────────────────────────────────────────────────
st.title("🚗 DrowsyGuard — Monitor en Tiempo Real")

# Barra de estado de la API
health = fetch_health()
if health:
    col_h1, col_h2, col_h3 = st.columns(3)
    col_h1.info(f"**API:** {'🟢 OK' if health['status'] == 'ok' else '🔴 ' + health['status']}")
    col_h2.info(f"**Cámara:** {'✅ Conectada' if health['camera_connected'] else '❌ Desconectada'}")
    col_h3.info(f"**Uptime:** {health['uptime_seconds']:.0f}s")
else:
    st.error("⚠️ No se puede conectar con la API. Verifica que esté corriendo en localhost:8000")

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

# ── Área de métricas en tiempo real ──────────────────────────────
ear_history: deque[float] = deque(maxlen=MAX_HISTORY)
placeholder = st.empty()

while True:
    data = fetch_metrics()

    with placeholder.container():
        if not data:
            st.warning("Sin datos. Inicia la detección con el botón ▶ Iniciar.")
        else:
            alert = data.get("alert_level", 0)
            alert_name = ALERT_NAMES.get(alert, "NONE")

            # ── Banner de alerta ──────────────────────────────────
            st.markdown(
                f"<div class='alert-{alert_name}'>"
                f"{ALERT_ICONS.get(alert, '✅')} NIVEL: {alert_name}"
                f"</div>",
                unsafe_allow_html=True,
            )

            # ── Métricas numéricas ────────────────────────────────
            m1, m2, m3, m4 = st.columns(4)
            m1.metric(
                "👁 EAR",
                f"{data['ear']:.3f}",
                help="Eye Aspect Ratio — menor valor = más cerrado (umbral: 0.25)",
            )
            m2.metric(
                "👄 MOR",
                f"{data['mor']:.3f}",
                help="Mouth Open Ratio — mayor valor = bostezo (umbral: 0.6)",
            )
            m3.metric(
                "📊 PERCLOS",
                f"{data['perclos']:.1%}",
                help="% de tiempo con ojos cerrados en ventana de 3s",
            )
            m4.metric(
                "🎯 FPS",
                f"{data['fps']:.0f}",
                help="Frames por segundo procesados",
            )

            # ── Gauge de PERCLOS ──────────────────────────────────
            bar_color = (
                "#3fb950" if alert == 0
                else "#d29922" if alert == 1
                else "#f85149"
            )
            fig_gauge = go.Figure(
                go.Indicator(
                    mode="gauge+number",
                    value=round(data["perclos"] * 100, 1),
                    number={"suffix": "%", "font": {"color": "#e6edf3"}},
                    title={"text": "PERCLOS", "font": {"color": "#e6edf3"}},
                    gauge={
                        "axis": {"range": [0, 100], "tickcolor": "#e6edf3"},
                        "bar": {"color": bar_color},
                        "bgcolor": "#161b22",
                        "bordercolor": "#30363d",
                        "steps": [
                            {"range": [0, 20], "color": "#0d1117"},
                            {"range": [20, 40], "color": "#1a2020"},
                            {"range": [40, 100], "color": "#2d1010"},
                        ],
                        "threshold": {
                            "line": {"color": "#f85149", "width": 3},
                            "value": 40,
                        },
                    },
                )
            )
            fig_gauge.update_layout(
                paper_bgcolor="#0d1117",
                font_color="#e6edf3",
                height=250,
                margin=dict(t=30, b=10, l=20, r=20),
            )
            st.plotly_chart(fig_gauge, use_container_width=True)

            # ── Gráfico histórico EAR ─────────────────────────────
            ear_history.append(data["ear"])

            fig_ear = go.Figure()
            fig_ear.add_trace(
                go.Scatter(
                    y=list(ear_history),
                    mode="lines+markers",
                    name="EAR",
                    line=dict(color="#58a6ff", width=2),
                    marker=dict(size=4),
                )
            )
            fig_ear.add_hline(
                y=0.25,
                line_dash="dash",
                line_color="#f85149",
                annotation_text="Umbral EAR (0.25)",
                annotation_font_color="#f85149",
            )
            fig_ear.update_layout(
                title="📈 Historial EAR (últimos 30s)",
                paper_bgcolor="#0d1117",
                plot_bgcolor="#161b22",
                font_color="#e6edf3",
                height=200,
                margin=dict(t=40, b=20, l=20, r=20),
                yaxis=dict(range=[0, 0.6], gridcolor="#21262d"),
                xaxis=dict(gridcolor="#21262d"),
                showlegend=False,
            )
            st.plotly_chart(fig_ear, use_container_width=True)

    time.sleep(1)
    st.cache_data.clear()