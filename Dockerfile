# ── Stage 1: Builder ─────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# Dependencias de sistema para compilar dlib y OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    cmake build-essential libopenblas-dev \
    && rm -rf /var/lib/apt/lists/*

# Instalar Poetry
RUN pip install --no-cache-dir poetry==1.8.0

# Copiar archivos de configuración de dependencias
COPY pyproject.toml ./

# Configurar Poetry e instalar dependencias (sin crear virtualenv)
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

# ── Stage 2: Runtime ──────────────────────────────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app

# Dependencias de sistema para OpenCV y Audio en runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1 \
    libasound2 libportaudio2 \
    && rm -rf /var/lib/apt/lists/*

# Copiar paquetes Python del builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copiar código fuente y recursos necesarios
COPY src/ ./src/
COPY assets/ ./assets/
COPY models/ ./models/

# Crear usuario no-root por seguridad
RUN useradd -m appuser && chown -R appuser /app
USER appuser

# Crear directorio de logs
RUN mkdir -p logs

# Exponer puertos para API (8000) y Dashboard (8501)
EXPOSE 8000
EXPOSE 8501

# Healthcheck básico usando python
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import http.client; conn = http.client.HTTPConnection('localhost', 8000); conn.request('GET', '/health'); r = conn.getresponse(); exit(0 if r.status == 200 else 1)" || exit 1

# Comando por defecto (será sobrescrito en docker-compose)
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
