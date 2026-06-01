/* dashboard.js — DrowsyGuard Monitor v2
 * Polling cada 1 s a /metrics/ y /health
 * Chart.js para gráfico EAR temporal (60 puntos)
 * Toggle dark/light con persistencia en localStorage
 */

"use strict";

// ── Configuración ─────────────────────────────────────────────
const API_BASE       = "";          // mismo origen que FastAPI
const POLL_INTERVAL  = 1000;        // ms
const EAR_MAX_POINTS = 60;
const EAR_THRESHOLD  = 0.25;

const ALERT_CONFIG = {
  0: { label: "NORMAL",   icon: "✅", badge: "",       color: "#00d4aa" },
  1: { label: "BAJA",     icon: "⚠️", badge: "LOW",    color: "#ffa726" },
  2: { label: "ALTA",     icon: "🔴", badge: "HIGH",   color: "#ef5350" },
  3: { label: "CRÍTICO",  icon: "🚨", badge: "CRITICAL", color: "#ff1744" },
};

// ── Estado ────────────────────────────────────────────────────
const state = {
  earHistory:    [],
  timeLabels:    [],
  lastAlertLevel: -1,
  timeline:      [],
  startTime:     Date.now(),
};

// ── Refs DOM ──────────────────────────────────────────────────
const $ = id => document.getElementById(id);

const els = {
  connectionDot:   $("connectionDot"),
  connectionText:  $("connectionText"),
  uptimeBadge:     $("uptimeBadge"),
  connectionBadge: $("connectionBadge"),
  cameraStatus:    $("cameraStatus"),
  videoFeed:       $("videoFeed"),
  videoPlaceholder:$("videoPlaceholder"),
  fpsBadge:        $("fpsBadge"),
  btnStart:        $("btnStart"),
  btnStop:         $("btnStop"),
  alertLabel:      $("alertLabel"),
  alertLevelText:  $("alertLevelText"),
  alertPerclos:    $("alertPerclos"),
  faceWarning:     $("faceWarning"),
  lights: [
    $("lightNone"),
    $("lightLow"),
    $("lightHigh"),
    $("lightCrit"),
  ],
  valEar:     $("valEar"),
  valMor:     $("valMor"),
  valPerclos: $("valPerclos"),
  valFps:     $("valFps"),
  valYawPitch:$("valYawPitch"),
  valTime:    $("valTime"),
  descEar:    $("descEar"),
  descMor:    $("descMor"),
  descPerclos:$("descPerclos"),
  descFps:    $("descFps"),
  descYawPitch:$("descYawPitch"),
  descTime:   $("descTime"),
  ringEar:    $("ringEar"),
  ringMor:    $("ringMor"),
  ringPerclos:$("ringPerclos"),
  ringFps:    $("ringFps"),
  ringYaw:    $("ringYaw"),
  ringTime:   $("ringTime"),
  phoneWarning: $("phoneWarning"),
  distractionWarning: $("distractionWarning"),
  lastUpdate: $("lastUpdate"),
  timelineList:  $("timelineList"),
  timelineCount: $("timelineCount"),
  footerVersion: $("footerVersion"),
  footerStatus:  $("footerStatus"),
  themeToggle:   $("themeToggle"),
};

// ── Tema dark / light ─────────────────────────────────────────
function initTheme() {
  const saved = localStorage.getItem("dg-theme") || "dark";
  document.documentElement.setAttribute("data-theme", saved);
  els.themeToggle.textContent = saved === "dark" ? "☀️" : "🌙";
}

els.themeToggle.addEventListener("click", () => {
  const current = document.documentElement.getAttribute("data-theme");
  const next    = current === "dark" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", next);
  localStorage.setItem("dg-theme", next);
  els.themeToggle.textContent = next === "dark" ? "☀️" : "🌙";
});

// ── Chart.js ──────────────────────────────────────────────────
const ctx = document.getElementById("earChart").getContext("2d");

const earChart = new Chart(ctx, {
  type: "line",
  data: {
    labels: [],
    datasets: [
      {
        label: "EAR",
        data: [],
        borderColor: "#42a5f5",
        backgroundColor: "rgba(66,165,245,0.08)",
        borderWidth: 2,
        pointRadius: 0,
        fill: true,
        tension: 0.3,
      },
      {
        label: "Umbral (0.25)",
        data: [],
        borderColor: "#ef5350",
        borderWidth: 1.5,
        borderDash: [6, 4],
        pointRadius: 0,
        fill: false,
      },
    ],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: { duration: 0 },
    plugins: {
      legend: {
        labels: { color: "#a0a0a0", font: { size: 11 } },
      },
    },
    scales: {
      x: {
        ticks: { color: "#a0a0a0", maxTicksLimit: 8, font: { size: 10 } },
        grid:  { color: "rgba(255,255,255,0.05)" },
      },
      y: {
        min: 0,
        max: 0.6,
        ticks: { color: "#a0a0a0", font: { size: 10 } },
        grid:  { color: "rgba(255,255,255,0.05)" },
      },
    },
  },
});

// ── Helpers ───────────────────────────────────────────────────

/** Offset SVG ring: circunferencia 201 px, mapea valor 0-1 a dashoffset */
function setRing(el, value, max = 1) {
  const pct    = Math.min(Math.max(value / max, 0), 1);
  const offset = 201 - pct * 201;
  el.style.strokeDashoffset = offset;
}

/** Hora HH:MM:SS */
function timeStr() {
  return new Date().toLocaleTimeString("es-PE", { hour12: false });
}

/** Actualiza semáforo */
function updateSemaphore(level) {
  els.lights.forEach((l, i) => {
    l.classList.toggle("active", i === level);
  });
  const cfg = ALERT_CONFIG[level] || ALERT_CONFIG[0];
  els.alertLabel.textContent = cfg.label;
  els.alertLabel.className   = `alert-label level-${level}`;
  els.alertLevelText.textContent = `Nivel ${level} / 3`;
}

/** Agrega evento al timeline */
function addTimelineEvent(level, data) {
  let reasons = [];
  if (data.phone_detected) reasons.push("📱 Celular");
  if (data.is_distracted) reasons.push("⚠️ Distracción");
  if (data.yawning) reasons.push("🥱 Bostezo");
  if (level > 0) {
    const cfg = ALERT_CONFIG[level];
    reasons.push(`${cfg.icon} Somnolencia (${cfg.label})`);
  }
  
  if (reasons.length === 0) return;
  const reasonStr = reasons.join(" + ");
  
  const icon = data.phone_detected ? "📱" : (data.is_distracted ? "⚠️" : (ALERT_CONFIG[level] || ALERT_CONFIG[0]).icon);
  const text = `${reasonStr} · EAR: ${data.ear.toFixed(3)} · PERCLOS: ${(data.perclos * 100).toFixed(1)}%`;
  
  const item = {
    time: timeStr(),
    level: level > 0 ? level : 1,
    icon,
    text
  };
  
  state.timeline.unshift(item);
  if (state.timeline.length > 10) state.timeline.pop();
  renderTimeline();
}

function renderTimeline() {
  if (!state.timeline.length) {
    els.timelineList.innerHTML = "<div class='timeline-empty'>Sin alertas registradas aún</div>";
    els.timelineCount.textContent = "0 eventos";
    return;
  }
  els.timelineCount.textContent = `${state.timeline.length} evento${state.timeline.length > 1 ? "s" : ""}`;
  els.timelineList.innerHTML = state.timeline.map(e => `
    <div class="timeline-item level-${e.level}">
      <span class="timeline-time">${e.time}</span>
      <span class="timeline-icon">${e.icon}</span>
      <span class="timeline-text">${e.text}</span>
      <span class="timeline-badge badge-${e.level}">${(ALERT_CONFIG[e.level] || ALERT_CONFIG[1]).badge}</span>
    </div>
  `).join("");
}

/** Actualiza gráfico EAR */
function updateChart(ear) {
  const label = timeStr();
  state.earHistory.push(ear);
  state.timeLabels.push(label);
  if (state.earHistory.length > EAR_MAX_POINTS) {
    state.earHistory.shift();
    state.timeLabels.shift();
  }
  earChart.data.labels              = [...state.timeLabels];
  earChart.data.datasets[0].data    = [...state.earHistory];
  earChart.data.datasets[1].data    = new Array(state.earHistory.length).fill(EAR_THRESHOLD);
  earChart.update("none");
}

// ── Polling /health ───────────────────────────────────────────
async function pollHealth() {
  try {
    const res  = await fetch(`${API_BASE}/health`);
    const data = await res.json();

    const ok  = data.status === "ok";
    const cam = data.camera_connected;

    els.connectionDot.className  = `connection-dot ${ok ? "ok" : "degraded"}`;
    els.connectionText.textContent = ok ? "Conectado" : "Degradado";
    els.footerStatus.textContent = ok ? "API activa" : "API degradada";
    els.footerVersion.textContent = `DrowsyGuard v${data.version || "—"}`;

    // Uptime
    const up = Math.floor(data.uptime_seconds || 0);
    const mm = String(Math.floor(up / 60)).padStart(2, "0");
    const ss = String(up % 60).padStart(2, "0");
    els.uptimeBadge.textContent = `${mm}:${ss}`;

    // Estado cámara
    const dot  = els.cameraStatus.querySelector(".status-dot");
    const span = els.cameraStatus.querySelector("span:last-child");
    if (dot && span) {
      dot.className  = `status-dot ${cam ? "on" : "off"}`;
      span.textContent = cam ? "Activa" : "Sin señal";
    }

    // Habilitar/Deshabilitar botones y sincronizar feed de video
    els.btnStart.disabled = cam;
    els.btnStop.disabled = !cam;

    if (cam) {
      if (els.videoFeed.src !== `${window.location.origin}${API_BASE}/stream/video` && els.videoFeed.src !== `${API_BASE}/stream/video`) {
        els.videoFeed.src = `${API_BASE}/stream/video`;
        els.videoFeed.style.display      = "block";
        els.videoPlaceholder.style.display = "none";
      }
    } else {
      if (els.videoFeed.src !== "" && !els.videoFeed.src.endsWith("#")) {
        els.videoFeed.src = "";
        els.videoFeed.style.display      = "none";
        els.videoPlaceholder.style.display = "flex";
      }
    }

  } catch {
    els.connectionDot.className    = "connection-dot error";
    els.connectionText.textContent = "Sin conexión";
    els.footerStatus.textContent   = "API no responde";
  }
}

// ── Polling /metrics/ ─────────────────────────────────────────
async function pollMetrics() {
  try {
    const res  = await fetch(`${API_BASE}/metrics/`);
    const data = await res.json();

    const ear        = data.ear        ?? 0;
    const mor        = data.mor        ?? 0;
    const perclos    = data.perclos    ?? 0;
    const fps        = data.fps        ?? 0;
    const alertLevel = data.alert_level ?? 0;
    const faceDet    = data.face_detected ?? false;
    const phoneDet   = data.phone_detected ?? false;
    const isDist     = data.is_distracted ?? false;
    const yaw        = data.head_yaw   ?? 0;
    const pitch      = data.head_pitch ?? 0;
    const yawn       = data.yawning    ?? false;
    const driveMin   = data.driving_minutes ?? 0;

    // Rostro y alertas adicionales
    els.faceWarning.style.display = faceDet ? "none" : "block";
    els.phoneWarning.style.display = phoneDet ? "block" : "none";
    els.distractionWarning.style.display = isDist ? "block" : "none";

    // Semáforo
    updateSemaphore(alertLevel);
    els.alertPerclos.textContent = `PERCLOS: ${(perclos * 100).toFixed(1)}%`;

    // Tarjetas numéricas
    els.valEar.textContent     = ear.toFixed(3);
    els.valMor.textContent     = mor.toFixed(3);
    els.valPerclos.textContent = `${(perclos * 100).toFixed(0)}%`;
    els.valFps.textContent     = fps.toFixed(0);
    els.valYawPitch.textContent = `${yaw.toFixed(0)}°/${pitch.toFixed(0)}°`;
    els.valTime.textContent     = `${driveMin.toFixed(1)}m`;

    els.descEar.textContent     = ear > 0.25   ? "Ojos abiertos"      : "⚠ Ojos cerrados";
    els.descMor.textContent     = yawn         ? "Bostezo detectado"  : "Normal";
    els.descPerclos.textContent = perclos < 0.2 ? "Normal"
                                : perclos < 0.4 ? "Atención"
                                : perclos < 0.6 ? "Alerta"
                                : "⚠ Crítico";
    els.descFps.textContent     = fps > 0 ? "En vivo" : "Detenido";
    els.descYawPitch.textContent = isDist ? "⚠ Distraído" : "Mirada al frente";
    els.descTime.textContent     = driveMin < 30 ? "Viaje reciente"
                                 : driveMin < 90 ? "Conducción media"
                                 : "Sugerido descansar";

    // Anillos SVG
    setRing(els.ringEar,     ear,     0.5);
    setRing(els.ringMor,     mor,     1.0);
    setRing(els.ringPerclos, perclos, 1.0);
    setRing(els.ringFps,     fps,     30);
    
    const avgDeviation = Math.min(Math.sqrt(yaw*yaw + pitch*pitch), 45);
    setRing(els.ringYaw,     avgDeviation, 45);
    setRing(els.ringTime,    driveMin,     120);

    // Color anillo EAR según umbral
    els.ringEar.style.stroke = ear < 0.25 ? "#ef5350" : "#42a5f5";

    // FPS badge
    els.fpsBadge.textContent = `${fps.toFixed(0)} FPS`;

    // Timeline — cuando hay cualquier alerta activa o cambio de estado de fatiga/teléfono
    const isAlerting = alertLevel > 0 || phoneDet || isDist || yawn;
    const currentStateKey = `${alertLevel}-${phoneDet}-${isDist}-${yawn}`;
    if (isAlerting && currentStateKey !== state.lastStateKey) {
      addTimelineEvent(alertLevel, data);
    }
    state.lastStateKey = currentStateKey;

    // Gráfico
    updateChart(ear);

    // Hora última actualización
    els.lastUpdate.textContent = timeStr();

  } catch {
    // API no responde — no crashear, solo esperar
  }
}

// ── Controles de stream ───────────────────────────────────────
els.btnStart.addEventListener("click", async () => {
  try {
    await fetch(`${API_BASE}/stream/start`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ source: 0 }),
    });
    els.videoFeed.src = `${API_BASE}/stream/video`;
    els.videoFeed.style.display      = "block";
    els.videoPlaceholder.style.display = "none";
  } catch {
    alert("No se pudo iniciar el stream. Verifica que la API esté activa.");
  }
});

els.btnStop.addEventListener("click", async () => {
  try {
    await fetch(`${API_BASE}/stream/stop`, { method: "POST" });
    els.videoFeed.src               = "";
    els.videoFeed.style.display     = "none";
    els.videoPlaceholder.style.display = "flex";
  } catch {
    alert("No se pudo detener el stream.");
  }
});

// ── Timeline — botón limpiar ──────────────────────────────────
$("btnClearTimeline").addEventListener("click", () => {
  state.timeline = [];
  renderTimeline();
});

// ── Init ──────────────────────────────────────────────────────
initTheme();
pollHealth();
pollMetrics();
setInterval(pollHealth,  5000);
setInterval(pollMetrics, POLL_INTERVAL);