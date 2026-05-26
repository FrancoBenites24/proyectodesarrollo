"""Dashboard principal de DrowsyGuard.

Interfaz en tiempo real para monitoreo de somnolencia del conductor.
Consume la API FastAPI en :8000 y refresca automáticamente.
"""

from __future__ import annotations

import time
from collections import deque
from typing import Any

import httpx
import plotly.graph_objects as go
import streamlit as st

# ── Configuración ─────────────────────────────────────────────────────────────

API_BASE = "http://localhost:8000"
REFRESH_INTERVAL = 0.5
HISTORY_SIZE = 60

ALERT_NAMES = {0: "NONE", 1: "LOW", 2: "HIGH", 3: "CRITICAL"}
ALERT_ICONS = {0: "✅", 1: "⚠️", 2: "🔶", 3: "🚨"}
ALERT_COLORS = {
    0: "#22c55e",
    1: "#facc15",
    2: "#f97316",
    3: "#ef4444",
}

# ── Helpers de API ────────────────────────────────────────────────────────────


def fetch_metrics() -> dict[str, Any]:
    """Obtiene métricas actuales desde la API.

    Returns:
        Diccionario con ear, mor, perclos, alert_level, face_detected,
        fps, timestamp — o dict vacío si la API no responde.
    """
    try:
        r = httpx.get(f"{API_BASE}/metrics/", timeout=1.0)
        r.raise_for_status()
        return r.json()
    except Exception:
        return {}


def fetch_health() -> dict[str, Any]:
    """Obtiene el estado de salud del sistema.

    Returns:
        Diccionario con status, camera_connected, uptime_seconds, version.
    """
    try:
        r = httpx.get(f"{API_BASE}/health", timeout=1.0)
        r.raise_for_status()
        return r.json()
    except Exception:
        return {}


def start_stream(source: int | str = 0) -> bool:
    """Envía orden de inicio del stream a la API.

    Args:
        source: índice de cámara (int) o ruta de video (str).

    Returns:
        True si la solicitud fue exitosa.
    """
    try:
        r = httpx.post(
            f"{API_BASE}/stream/start",
            json={"source": source},
            timeout=3.0,
        )
        return r.status_code == 200
    except Exception:
        return False


def stop_stream() -> bool:
    """Envía orden de parada del stream a la API.

    Returns:
        True si la solicitud fue exitosa.
    """
    try:
        r = httpx.post(f"{API_BASE}/stream/stop", timeout=3.0)
        return r.status_code == 200
    except Exception:
        return False


# ── Inicialización de estado de sesión ───────────────────────────────────────


def _init_session_state() -> None:
    """Inicializa variables de estado de la sesión si no existen."""
    if "ear_history" not in st.session_state:
        st.session_state.ear_history: deque[float] = deque(maxlen=HISTORY_SIZE)
    if "perclos_history" not in st.session_state:
        st.session_state.perclos_history: deque[float] = deque(maxlen=HISTORY_SIZE)
    if "time_history" not in st.session_state:
        st.session_state.time_history: deque[float] = deque(maxlen=HISTORY_SIZE)
    if "stream_active" not in st.session_state:
        st.session_state.stream_active = False


# ── Componentes de UI ─────────────────────────────────────────────────────────


def render_page_config() -> None:
    """Configura la página y los estilos globales."""
    st.set_page_config(
        page_title="DrowsyGuard Monitor",
        page_icon="🚗",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(
        """
        <style>
        .stApp { background-color: #0d1117; color: #e6edf3; }
        .block-container { padding-top: 1rem; }
        .alert-NONE {
            color: #22c55e; font-size: 1.8rem; font-weight: bold;
            text-align: center; padding: 0.4rem 1rem;
            border: 2px solid #22c55e; border-radius: 10px;
        }
        .alert-LOW {
            color: #facc15; font-size: 1.8rem; font-weight: bold;
            text-align: center; padding: 0.4rem 1rem;
            border: 2px solid #facc15; border-radius: 10px;
        }
        .alert-HIGH {
            color: #f97316; font-size: 1.8rem; font-weight: bold;
            text-align: center; padding: 0.4rem 1rem;
            border: 2px solid #f97316; border-radius: 10px;
        }
        .alert-CRITICAL {
            color: #ef4444; font-size: 1.8rem; font-weight: bold;
            text-align: center; padding: 0.4rem 1rem;
            border: 2px solid #ef4444; border-radius: 10px;
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


def render_sidebar(health: dict[str, Any]) -> tuple[bool, int | str]:
    """Renderiza el panel lateral con controles y estado del sistema.

    Args:
        health: Diccionario de salud retornado por la API.

    Returns:
        Tupla (auto_refresh, source) con las preferencias del usuario.
    """
    with st.sidebar:
        st.markdown("## ⚙️ Control")

        api_ok = bool(health)
        status_color = "#22c55e" if api_ok else "#ef4444"
        status_text = "API conectada" if api_ok else "API sin respuesta"
        st.markdown(
            f'<span style="color:{status_color}">● {status_text}</span>',
            unsafe_allow_html=True,
        )

        if api_ok:
            cam_ok = health.get("camera_connected", False)
            cam_color = "#22c55e" if cam_ok else "#facc15"
            cam_text = "Cámara activa" if cam_ok else "Cámara desconectada"
            st.markdown(
                f'<span style="color:{cam_color}">● {cam_text}</span>',
                unsafe_allow_html=True,
            )
            uptime = health.get("uptime_seconds", 0)
            st.caption(f"Uptime: {uptime:.0f} s  |  v{health.get('version', '?')}")

        st.divider()

        source_input = st.text_input(
            "Fuente de cámara",
            value="0",
            help="0 para webcam, o ruta a un archivo de video",
        )
        try:
            source: int | str = int(source_input)
        except ValueError:
            source = source_input

        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("▶ Iniciar", use_container_width=True, type="primary"):
                if start_stream(source):
                    st.session_state.stream_active = True
                    st.success("Stream iniciado")
                else:
                    st.error("No se pudo iniciar")
        with col_b:
            if st.button("⏹ Detener", use_container_width=True):
                if stop_stream():
                    st.session_state.stream_active = False
                    st.success("Stream detenido")
                else:
                    st.error("No se pudo detener")

        st.divider()
        st.markdown("### 🔄 Refresco")
        auto_refresh = st.toggle("Auto-refresco", value=True)
        st.caption(f"Intervalo: {REFRESH_INTERVAL} s")

        st.divider()
        st.markdown("### 📋 Leyenda PERCLOS")
        st.markdown(
            """
            | Nivel | PERCLOS |
            |-------|---------|
            | ✅ Normal | < 20% |
            | ⚠️ Bajo   | 20–40% |
            | 🔶 Alto   | 40–60% |
            | 🚨 Crítico | > 60% |
            """
        )

        return auto_refresh, source  # type: ignore[return-value]


def render_alert_banner(alert_level: int, face_detected: bool) -> None:
    """Muestra banner de alerta con color y animación según el nivel.

    Args:
        alert_level: 0-3 según AlertLevelSchema.
        face_detected: True si hay cara detectada en el frame actual.
    """
    if not face_detected:
        st.warning("👤 Sin rostro detectado — posiciona la cámara correctamente")
        return

    alert_name = ALERT_NAMES.get(alert_level, "NONE")
    icon = ALERT_ICONS.get(alert_level, "✅")
    st.markdown(
        f"<div class='alert-{alert_name}'>{icon} NIVEL: {alert_name}</div>",
        unsafe_allow_html=True,
    )
    st.write("")


def render_metric_cards(data: dict[str, Any]) -> None:
    """Renderiza las tarjetas de métricas principales.

    Args:
        data: Diccionario de métricas retornado por la API.
    """
    ear = data.get("ear", 0.0)
    mor = data.get("mor", 0.0)
    perclos = data.get("perclos", 0.0)
    fps = data.get("fps", 0.0)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(
        label="👁️ EAR",
        value=f"{ear:.3f}",
        delta="abiertos" if ear > 0.25 else "cerrados",
        delta_color="normal" if ear > 0.25 else "inverse",
    )
    col2.metric(
        label="😮 MOR",
        value=f"{mor:.3f}",
        delta="bostezo" if mor > 0.60 else "normal",
        delta_color="inverse" if mor > 0.60 else "normal",
    )
    col3.metric(
        label="📊 PERCLOS",
        value=f"{perclos * 100:.1f}%",
        delta="crítico" if perclos >= 0.60 else ("alto" if perclos >= 0.40 else "ok"),
        delta_color="inverse" if perclos >= 0.20 else "normal",
    )
    col4.metric(
        label="🎬 FPS",
        value=f"{fps:.0f}",
        delta="en vivo" if fps > 0 else "detenido",
        delta_color="normal" if fps > 0 else "off",
    )


def render_perclos_gauge(perclos: float, alert_level: int) -> None:
    """Renderiza el gauge circular de PERCLOS.

    Args:
        perclos: Valor de PERCLOS entre 0 y 1.
        alert_level: Nivel de alerta para el color del gauge.
    """
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=round(perclos * 100, 1),
            number={"suffix": "%", "font": {"color": "#e6edf3", "size": 28}},
            gauge={
                "axis": {"range": [0, 100], "tickcolor": "#e6edf3"},
                "bar": {"color": ALERT_COLORS.get(alert_level, "#22c55e")},
                "bgcolor": "#161b22",
                "steps": [
                    {"range": [0, 20], "color": "#0d1117"},
                    {"range": [20, 40], "color": "#1a2020"},
                    {"range": [40, 100], "color": "#2d1010"},
                ],
            },
        )
    )
    fig.update_layout(
        paper_bgcolor="#0d1117",
        font_color="#e6edf3",
        height=220,
        margin={"t": 30, "b": 10, "l": 20, "r": 20},
    )
    st.plotly_chart(fig, use_container_width=True, key="gauge")


def render_history_chart(
    ear_history: deque[float],
    perclos_history: deque[float],
    time_history: deque[float],
) -> None:
    """Renderiza el gráfico de histórico EAR y PERCLOS con Plotly.

    Args:
        ear_history: Cola circular con valores de EAR.
        perclos_history: Cola circular con valores de PERCLOS.
        time_history: Cola circular con timestamps relativos (segundos).
    """
    if not time_history:
        st.info("El gráfico aparecerá cuando el stream esté activo.")
        return
    t = list(time_history)
    t_rel = [round(ti - t[0], 1) for ti in t]
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=t_rel,
            y=list(ear_history),
            name="EAR",
            line={"color": "#58a6ff", "width": 2},
            fill="tozeroy",
            fillcolor="rgba(88,166,255,0.08)",
        )
    )
    fig.add_hline(
        y=0.25,
        line_dash="dot",
        line_color="#f87171",
        annotation_text="umbral EAR (0.25)",
        annotation_position="top right",
        annotation_font_color="#f87171",
    )
    fig.add_trace(
        go.Scatter(
            x=t_rel,
            y=[p * 100 for p in perclos_history],
            name="PERCLOS %",
            line={"color": "#fb923c", "width": 2, "dash": "dash"},
            yaxis="y2",
        )
    )
    fig.update_layout(
        title="📈 Histórico EAR y PERCLOS (últimos 30 s)",
        height=220,
        margin={"l": 0, "r": 0, "t": 40, "b": 0},
        paper_bgcolor="#0d1117",
        plot_bgcolor="#161b22",
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "x": 1,
            "xanchor": "right",
        },
        xaxis={"title": "segundos", "gridcolor": "#1e293b", "color": "#64748b"},
        yaxis={
            "title": "EAR",
            "range": [0, 0.6],
            "gridcolor": "#1e293b",
            "color": "#64748b",
        },
        yaxis2={
            "title": "PERCLOS %",
            "overlaying": "y",
            "side": "right",
            "range": [0, 100],
            "color": "#64748b",
            "showgrid": False,
        },
        font={"color": "#94a3b8"},
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ── Página principal ──────────────────────────────────────────────────────────


def main() -> None:
    """Punto de entrada del dashboard DrowsyGuard."""
    render_page_config()
    _init_session_state()

    st.markdown("# 🚗 DrowsyGuard Monitor")
    st.caption("Sistema de detección de somnolencia en tiempo real")

    health = fetch_health()
    auto_refresh, source = render_sidebar(health)

    data = fetch_metrics()
    alert_level = data.get("alert_level", 0)
    face_detected = data.get("face_detected", False)

    if data:
        st.session_state.ear_history.append(data.get("ear", 0.0))
        st.session_state.perclos_history.append(data.get("perclos", 0.0))
        st.session_state.time_history.append(data.get("timestamp", time.time()))

    render_alert_banner(alert_level, face_detected)

    col_video, col_right = st.columns([3, 2], gap="large")

    with col_video:
        st.subheader("📷 Video en vivo")
        if st.session_state.stream_active:
            st.image(
                f"{API_BASE}/stream/video",
                use_container_width=True,
                caption="Stream MJPEG — actualiza automáticamente",
            )
        else:
            st.info("▶ Pulsa **Iniciar** en el panel lateral para activar la cámara.")

    with col_right:
        st.subheader("📊 Métricas actuales")
        if data:
            render_metric_cards(data)
            render_perclos_gauge(data.get("perclos", 0.0), alert_level)
        else:
            st.warning("Sin datos — verifica que la API esté corriendo en :8000")

    st.divider()
    render_history_chart(
        st.session_state.ear_history,
        st.session_state.perclos_history,
        st.session_state.time_history,
    )

    if auto_refresh:
        time.sleep(REFRESH_INTERVAL)
        st.rerun()


if __name__ == "__main__":
    main()
