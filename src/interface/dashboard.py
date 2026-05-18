#Dashboard principal de DrowsyGuard.
#Interfaz en tiempo real para monitoreo de somnolencia del conductor.
#Consume la API FastAPI en :8000 y refresca automáticamente.
 
 
from __future__ import annotations
 
import time
from collections import deque
from typing import Any
 
import httpx
import plotly.graph_objects as go
import streamlit as st
 
# ── Configuración ────────────────────────────────────────────────────────────
 
API_BASE = "http://localhost:8000"
REFRESH_INTERVAL = 0.5  # segundos entre actualizaciones
HISTORY_SIZE = 60  # puntos en el gráfico (~30 s a 0.5 s/tick)
 
ALERT_COLORS = {
    0: ("#22c55e", "NORMAL", "✅"),      # NONE
    1: ("#facc15", "ALERTA BAJA", "⚠️"),  # LOW
    2: ("#f97316", "ALERTA ALTA", "🔶"),  # HIGH
    3: ("#ef4444", "CRÍTICO", "🚨"),      # CRITICAL
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
 
 
def render_alert_banner(alert_level: int, face_detected: bool) -> None:
    """Muestra banner de alerta con color según el nivel.
 
    Args:
        alert_level: 0-3 según AlertLevelSchema.
        face_detected: True si hay cara detectada en el frame actual.
    """
    color, label, icon = ALERT_COLORS.get(alert_level, ALERT_COLORS[0])
 
    if not face_detected:
        st.warning("👤 Sin rostro detectado — posiciona la cámara correctamente")
        return
 
    st.markdown(
        f"""
        <div style="
            background: {color}22;
            border: 2px solid {color};
            border-radius: 12px;
            padding: 16px 24px;
            display: flex;
            align-items: center;
            gap: 16px;
            margin-bottom: 8px;
        ">
            <span style="font-size: 2rem;">{icon}</span>
            <div>
                <div style="
                    font-size: 1.3rem;
                    font-weight: 700;
                    color: {color};
                    letter-spacing: 0.05em;
                ">{label}</div>
                <div style="font-size: 0.85rem; color: #94a3b8;">
                    Nivel de alerta: {alert_level}/3
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
 
 
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
 
    # EAR — umbral 0.25 (configurado en .env)
    ear_delta = "ojos abiertos" if ear > 0.25 else "ojos cerrados"
    col1.metric(
        label="👁️ EAR",
        value=f"{ear:.3f}",
        delta=ear_delta,
        delta_color="normal" if ear > 0.25 else "inverse",
    )
 
    # MOR — umbral 0.60
    mor_delta = "bostezo detectado" if mor > 0.60 else "normal"
    col2.metric(
        label="😮 MOR",
        value=f"{mor:.3f}",
        delta=mor_delta,
        delta_color="inverse" if mor > 0.60 else "normal",
    )
 
    # PERCLOS — porcentaje
    perclos_pct = perclos * 100
    col3.metric(
        label="📊 PERCLOS",
        value=f"{perclos_pct:.1f}%",
        delta="crítico" if perclos >= 0.60 else ("alto" if perclos >= 0.40 else "ok"),
        delta_color="inverse" if perclos >= 0.20 else "normal",
    )
 
    # FPS
    col4.metric(
        label="🎬 FPS",
        value=f"{fps:.0f}",
        delta="en vivo" if fps > 0 else "detenido",
        delta_color="normal" if fps > 0 else "off",
    )
 
 
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
    t0 = t[0]
    t_rel = [round(ti - t0, 1) for ti in t]
 
    fig = go.Figure()
 
    # EAR
    fig.add_trace(
        go.Scatter(
            x=t_rel,
            y=list(ear_history),
            name="EAR",
            line={"color": "#38bdf8", "width": 2},
            fill="tozeroy",
            fillcolor="rgba(56,189,248,0.08)",
        )
    )
 
    # Línea umbral EAR
    fig.add_hline(
        y=0.25,
        line_dash="dot",
        line_color="#f87171",
        annotation_text="umbral EAR (0.25)",
        annotation_position="top right",
        annotation_font_color="#f87171",
    )
 
    # PERCLOS (eje secundario)
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
        height=260,
        margin={"l": 0, "r": 0, "t": 8, "b": 0},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1,
        },
        xaxis={
            "title": "segundos",
            "gridcolor": "#1e293b",
            "color": "#64748b",
        },
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
 
 
def render_sidebar(health: dict[str, Any]) -> None:
    """Renderiza el panel lateral con controles y estado del sistema.
 
    Args:
        health: Diccionario de salud retornado por la API.
    """
    with st.sidebar:
        st.markdown("## ⚙️ Control")
 
        # Estado de conexión API
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
 
        # Fuente de cámara
        source_input = st.text_input(
            "Fuente de cámara",
            value="0",
            help="0 para webcam, o ruta a un archivo de video",
        )
        try:
            source: int | str = int(source_input)
        except ValueError:
            source = source_input
 
        # Botones de control
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
 
        # Configuración de refresco
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
 
        return auto_refresh  # type: ignore[return-value]
 
 
# ── Página principal ──────────────────────────────────────────────────────────
 
 
def main() -> None:
    """Punto de entrada del dashboard DrowsyGuard."""
    st.set_page_config(
        page_title="DrowsyGuard Monitor",
        page_icon="🚗",
        layout="wide",
        initial_sidebar_state="expanded",
    )
 
    # CSS mínimo para oscurecer el fondo y mejorar contraste
    st.markdown(
        """
        <style>
        .block-container { padding-top: 1.5rem; }
        [data-testid="metric-container"] {
            background: #0f172a;
            border: 1px solid #1e293b;
            border-radius: 12px;
            padding: 16px !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
 
    _init_session_state()
 
    # Encabezado
    st.markdown("# 🚗 DrowsyGuard Monitor")
    st.caption("Sistema de detección de somnolencia en tiempo real")
 
    # Sidebar y controles
    health = fetch_health()
    auto_refresh = render_sidebar(health)
 
    # Datos actuales
    data = fetch_metrics()
    alert_level = data.get("alert_level", 0)
    face_detected = data.get("face_detected", False)
 
    # Actualizar historial si hay datos
    if data:
        st.session_state.ear_history.append(data.get("ear", 0.0))
        st.session_state.perclos_history.append(data.get("perclos", 0.0))
        st.session_state.time_history.append(data.get("timestamp", time.time()))
 
    # Banner de alerta
    render_alert_banner(alert_level, face_detected)
 
    # Layout principal: video | métricas
    col_video, col_right = st.columns([3, 2], gap="large")
 
    with col_video:
        st.subheader("📷 Video en vivo")
        video_placeholder = st.empty()
        if st.session_state.stream_active:
            video_placeholder.image(
                f"{API_BASE}/stream/video",
                use_container_width=True,
                caption="Stream MJPEG — actualiza automáticamente",
            )
        else:
            video_placeholder.info(
                "▶ Pulsa **Iniciar** en el panel lateral para activar la cámara."
            )
 
    with col_right:
        st.subheader("📊 Métricas actuales")
        if data:
            render_metric_cards(data)
        else:
            st.warning("Sin datos — verifica que la API esté corriendo en :8000")
 
        st.markdown("#### 📈 Histórico (últimos 30 s)")
        render_history_chart(
            st.session_state.ear_history,
            st.session_state.perclos_history,
            st.session_state.time_history,
        )
 
    # Auto-refresco
    if auto_refresh:
        time.sleep(REFRESH_INTERVAL)
        st.rerun()
 
 
if __name__ == "__main__":
    main()