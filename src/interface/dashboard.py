"""Dashboard Streamlit para monitoreo de somnolencia en tiempo real."""

import os

import httpx
import streamlit as st

API_BASE = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="DrowsyGuard", layout="wide")

st.title("🚗 DrowsyGuard Monitor")


def fetch_metrics() -> dict:
    """Obtiene las métricas actuales desde la API.

    Returns:
        Diccionario con métricas (ear, mor, perclos, fps, etc.).
        Retorna un dict vacío si la API no está disponible.
    """
    try:
        r = httpx.get(f"{API_BASE}/metrics/", timeout=2.0)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPError:
        return {}


def start_stream() -> None:
    """Envía la señal de inicio del stream a la API."""
    try:
        httpx.post(f"{API_BASE}/stream/start", timeout=5.0)
    except httpx.HTTPError:
        st.error("No se pudo conectar con la API para iniciar el stream.")


def stop_stream() -> None:
    """Envía la señal de detención del stream a la API."""
    try:
        httpx.post(f"{API_BASE}/stream/stop", timeout=5.0)
    except httpx.HTTPError:
        st.error("No se pudo conectar con la API para detener el stream.")


# ── Botones de control ────────────────────────────────────────────────────────
col1, col2 = st.columns(2)
with col1:
    if st.button("▶ Iniciar"):
        start_stream()

with col2:
    if st.button("⏹ Detener"):
        stop_stream()

st.divider()

# ── Cámara ────────────────────────────────────────────────────────────────────
st.subheader("📷 Cámara")
st.image(f"{API_BASE}/stream/video")

st.divider()

# ── Métricas ──────────────────────────────────────────────────────────────────
data = fetch_metrics()

st.subheader("📊 Métricas")
col1, col2 = st.columns(2)
col1.metric("EAR", f"{data.get('ear', 0):.3f}")
col2.metric("PERCLOS", f"{data.get('perclos', 0):.1%}")

col3, col4 = st.columns(2)
col3.metric("MOR", f"{data.get('mor', 0):.3f}")
col4.metric("FPS", f"{data.get('fps', 0):.0f}")
