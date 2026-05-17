import streamlit as st
import httpx

API_BASE = "http://localhost:8000"

st.set_page_config(page_title="DrowsyGuard", layout="wide")

st.title("🚗 DrowsyGuard Monitor")

def fetch_metrics():
    try:
        r = httpx.get(f"{API_BASE}/metrics/")
        return r.json()
    except:
        return {}

def start_stream():
    httpx.post(f"{API_BASE}/stream/start")

def stop_stream():
    httpx.post(f"{API_BASE}/stream/stop")

# Botones
col1, col2 = st.columns(2)
with col1:
    if st.button("▶ Iniciar"):
        start_stream()

with col2:
    if st.button("⏹ Detener"):
        stop_stream()

st.divider()

# Cámara
st.subheader("📷 Cámara")
st.image(f"{API_BASE}/stream/video")

st.divider()

# Métricas
data = fetch_metrics()

st.subheader("📊 Métricas")
col1, col2 = st.columns(2)
col1.metric("EAR", f"{data.get('ear', 0):.3f}")
col2.metric("PERCLOS", f"{data.get('perclos', 0):.1%}")

col3, col4 = st.columns(2)
col3.metric("MOR", f"{data.get('mor', 0):.3f}")
col4.metric("FPS", f"{data.get('fps', 0):.0f}")