# 🚗 DriverDrowsGuard v1.0

> Sistema de detección de somnolencia en conductores en tiempo real.  
> Basado en **Mediapipe FaceMesh** + análisis temporal **PERCLOS**.

[![CI](https://github.com/FrancoBenites24/ProyectoDesarrollo/actions/workflows/ci.yml/badge.svg)](https://github.com/FrancoBenites24/ProyectoDesarrollo/actions)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-UTP-green.svg)](LICENSE)

---

## ⚡ Quick Start

```bash
git clone https://github.com/FrancoBenites24/ProyectoDesarrollo
cd ProyectoDesarrollo
cp .env.example .env
pip install poetry && poetry install
poetry run uvicorn src.api.main:app --reload
```

Dashboard: `http://localhost:8501` | API Docs: `http://localhost:8000/docs`

---

## 🏗️ Arquitectura

```
Webcam → VideoStream (Thread) → DrowsinessDetector (Mediapipe)
                                       ↓
                               TemporalAnalyzer (PERCLOS)
                                       ↓
                               AlertSystem (Sonido + Webhook)
                                       ↓
                     FastAPI ←→ Streamlit Dashboard
```

## 📸 Hardware Mínimo

| Item | Especificación |
|------|----------------|
| Cámara | Webcam USB 720p@30fps |
| RAM | 8 GB mínimo |
| CPU | Intel i5 / AMD Ryzen 5 o superior |
| OS | Windows 10+, Ubuntu 20.04+, macOS 12+ |

## 🤝 Contribuir

Ver [CONTRIBUTING.md](CONTRIBUTING.md)

## 📜 Licencia

UTP
