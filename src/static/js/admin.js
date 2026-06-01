/* admin.js — DrowsyGuard Panel de Supervisión
 * Polling cada 3s a /drivers/ y /alerts/
 * Chart.js para alertas por conductor
 * Toggle dark/light compartido con dashboard
 */

"use strict";

// ── Configuración ─────────────────────────────────────
const API_BASE        = "";
const POLL_INTERVAL   = 3000;
const ALERTS_LIMIT    = 20;

const STATUS_CONFIG = {
  active:   { label: "Activo",   icon: "🟢", cls: "active",   badge: "status-active" },
  alert:    { label: "Alerta",   icon: "🔴", cls: "alert",    badge: "status-alert" },
  inactive: { label: "Inactivo", icon: "⚪", cls: "inactive", badge: "status-inactive" },
};

const ALERT_CONFIG = {
  0: { label: "NORMAL",  icon: "✅", color: "#00d4aa" },
  1: { label: "BAJA",    icon: "⚠️", color: "#ffa726" },
  2: { label: "ALTA",    icon: "🔴", color: "#ef5350" },
  3: { label: "CRÍTICO", icon: "🚨", color: "#ff1744" },
};

// ── Estado local ──────────────────────────────────────
const state = {
  drivers:    [],
  alerts:     [],
  sortCol:    "name",
  sortAsc:    true,
};

// ── Refs DOM ──────────────────────────────────────────
const $ = id => document.getElementById(id);

const els = {
  connectionDot:   $("connectionDot"),
  connectionText:  $("connectionText"),
  kpiActive:       $("kpiActive"),
  kpiTotal:        $("kpiTotal"),
  kpiAlerts:       $("kpiAlerts"),
  kpiCritical:     $("kpiCritical"),
  driverGrid:      $("driverGrid"),
  driverTableBody: $("driverTableBody"),
  driversUpdate:   $("driversUpdate"),
  alertTimeline:   $("alertTimeline"),
  alertCount:      $("alertCount"),
  btnRegister:     $("btnRegister"),
  btnCloseModal:   $("btnCloseModal"),
  btnCancelModal:  $("btnCancelModal"),
  btnSubmitDriver: $("btnSubmitDriver"),
  modalOverlay:    $("modalOverlay"),
  inputName:       $("inputName"),
  inputPlate:      $("inputPlate"),
  formError:       $("formError"),
  themeToggle:     $("themeToggle"),
};

// ── Tema (compartido con dashboard) ───────────────────
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

// ── Chart.js ──────────────────────────────────────────
const ctxBar = document.getElementById("alertsChart").getContext("2d");

const alertsChart = new Chart(ctxBar, {
  type: "bar",
  data: {
    labels: [],
    datasets: [{
      label: "Total alertas",
      data: [],
      backgroundColor: "rgba(0,212,170,0.5)",
      borderColor: "#00d4aa",
      borderWidth: 1.5,
      borderRadius: 4,
    }],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: { duration: 300 },
    plugins: {
      legend: { display: false },
    },
    scales: {
      x: {
        ticks: { color: "#a0a0a0", font: { size: 11 } },
        grid:  { color: "rgba(255,255,255,0.05)" },
      },
      y: {
        beginAtZero: true,
        ticks: { color: "#a0a0a0", font: { size: 11 }, stepSize: 1 },
        grid:  { color: "rgba(255,255,255,0.05)" },
      },
    },
  },
});

// ── Helpers ───────────────────────────────────────────
function timeStr(dateStr) {
  if (!dateStr) return "—";
  try {
    return new Date(dateStr).toLocaleTimeString("es-PE", { hour12: false });
  } catch {
    return "—";
  }
}

function now() {
  return new Date().toLocaleTimeString("es-PE", { hour12: false });
}

function alertsForDriver(driverId) {
  return state.alerts.filter(a => a.driver_id === driverId).length;
}

function maxPerclosForDriver(driverId) {
  const vals = state.alerts
    .filter(a => a.driver_id === driverId)
    .map(a => a.perclos || 0);
  return vals.length ? Math.max(...vals) : 0;
}

function resolveDriverStatus(driver) {
  const recent = state.alerts
    .filter(a => a.driver_id === driver.id)
    .slice(0, 1)[0];
  if (!recent) return driver.status || "inactive";
  const level = parseInt(recent.alert_level) || 0;
  if (level >= 2) return "alert";
  if (level >= 1) return "active";
  return driver.status || "inactive";
}

// ── Render: Driver Grid ───────────────────────────────
function renderDriverGrid() {
  if (!state.drivers.length) {
    els.driverGrid.innerHTML = "<div class='driver-empty'>Sin conductores registrados</div>";
    return;
  }

  els.driverGrid.innerHTML = state.drivers.map(d => {
    const status  = resolveDriverStatus(d);
    const cfg     = STATUS_CONFIG[status] || STATUS_CONFIG.inactive;
    const alerts  = alertsForDriver(d.id);
    const perclos = (maxPerclosForDriver(d.id) * 100).toFixed(1);
    const updated = timeStr(d.updated_at || d.created_at);

    return `
      <div class="driver-card ${cfg.cls}">
        <div class="driver-card-header">
          <span class="driver-name">${d.name}</span>
          <span class="driver-status-badge ${cfg.badge}">${cfg.icon} ${cfg.label}</span>
        </div>
        ${d.license_plate
          ? `<span class="driver-plate">🪪 ${d.license_plate}</span>`
          : ""}
        <div class="driver-metrics">
          <div class="driver-metric">
            <span class="driver-metric-val">${alerts}</span>
            <span class="driver-metric-lbl">Alertas</span>
          </div>
          <div class="driver-metric">
            <span class="driver-metric-val">${perclos}%</span>
            <span class="driver-metric-lbl">PERCLOS máx</span>
          </div>
        </div>
        <span class="driver-activity">Última actividad: ${updated}</span>
      </div>
    `;
  }).join("");
}

// ── Render: Alert Timeline ────────────────────────────
function renderTimeline() {
  els.alertCount.textContent = `${state.alerts.length} alertas`;

  if (!state.alerts.length) {
    els.alertTimeline.innerHTML = "<div class='timeline-empty'>Sin alertas registradas</div>";
    return;
  }

  const driverMap = Object.fromEntries(state.drivers.map(d => [d.id, d.name]));

  els.alertTimeline.innerHTML = state.alerts.map(a => {
    const level  = parseInt(a.alert_level) || 0;
    const cfg    = ALERT_CONFIG[level] || ALERT_CONFIG[0];
    const name   = driverMap[a.driver_id] || `Conductor #${a.driver_id}`;
    const t      = timeStr(a.timestamp);

    return `
      <div class="timeline-item level-${level}">
        <span class="timeline-time">${t}</span>
        <span class="timeline-icon">${cfg.icon}</span>
        <span class="timeline-text"><strong>${name}</strong> — EAR ${(a.ear || 0).toFixed(3)}</span>
        <span class="timeline-badge badge-${level}">${cfg.label}</span>
      </div>
    `;
  }).join("");
}

// ── Render: Driver Table ──────────────────────────────
function renderTable() {
  if (!state.drivers.length) {
    els.driverTableBody.innerHTML =
      "<tr><td colspan='6' class='table-empty'>Sin conductores registrados</td></tr>";
    return;
  }

  const sorted = [...state.drivers].sort((a, b) => {
    let va, vb;
    switch (state.sortCol) {
      case "name":    va = a.name; vb = b.name; break;
      case "plate":   va = a.license_plate || ""; vb = b.license_plate || ""; break;
      case "status":  va = resolveDriverStatus(a); vb = resolveDriverStatus(b); break;
      case "alerts":  va = alertsForDriver(a.id); vb = alertsForDriver(b.id); break;
      case "perclos": va = maxPerclosForDriver(a.id); vb = maxPerclosForDriver(b.id); break;
      default:        va = a.name; vb = b.name;
    }
    if (va < vb) return state.sortAsc ? -1 : 1;
    if (va > vb) return state.sortAsc ? 1 : -1;
    return 0;
  });

  const driverMap = Object.fromEntries(state.drivers.map(d => [d.id, d.name]));

  els.driverTableBody.innerHTML = sorted.map(d => {
    const status  = resolveDriverStatus(d);
    const cfg     = STATUS_CONFIG[status] || STATUS_CONFIG.inactive;
    const alerts  = alertsForDriver(d.id);
    const perclos = (maxPerclosForDriver(d.id) * 100).toFixed(1);
    const updated = timeStr(d.updated_at || d.created_at);

    return `
      <tr>
        <td>${d.name}</td>
        <td>${d.license_plate || "—"}</td>
        <td><span class="driver-status-badge ${cfg.badge}">${cfg.icon} ${cfg.label}</span></td>
        <td>${alerts}</td>
        <td>${perclos}%</td>
        <td>${updated}</td>
      </tr>
    `;
  }).join("");
}

// ── Render: Chart ─────────────────────────────────────
function renderChart() {
  const labels = state.drivers.map(d => d.name.split(" ")[0]);
  const data   = state.drivers.map(d => alertsForDriver(d.id));

  alertsChart.data.labels           = labels;
  alertsChart.data.datasets[0].data = data;
  alertsChart.update("none");
}

// ── Render: KPIs ──────────────────────────────────────
function renderKPIs() {
  const active   = state.drivers.filter(d => resolveDriverStatus(d) === "active").length;
  const critical = state.alerts.filter(a => parseInt(a.alert_level) === 3).length;

  els.kpiActive.textContent   = active;
  els.kpiTotal.textContent    = state.drivers.length;
  els.kpiAlerts.textContent   = state.alerts.length;
  els.kpiCritical.textContent = critical;
}

// ── Render: Todo ──────────────────────────────────────
function renderAll() {
  renderDriverGrid();
  renderTable();
  renderTimeline();
  renderChart();
  renderKPIs();
  els.driversUpdate.textContent = now();
}

// ── API calls ─────────────────────────────────────────
async function loadDrivers() {
  try {
    const res = await fetch(`${API_BASE}/drivers/`);
    state.drivers = await res.json();
  } catch {
    state.drivers = [];
  }
}

async function loadAlerts() {
  try {
    const res = await fetch(`${API_BASE}/alerts/?limit=${ALERTS_LIMIT}`);
    state.alerts = await res.json();
  } catch {
    state.alerts = [];
  }
}

async function checkConnection() {
  try {
    const res  = await fetch(`${API_BASE}/health`);
    const data = await res.json();
    const ok   = data.status === "ok" || data.status === "degraded";
    els.connectionDot.className    = `connection-dot ${ok ? "ok" : "degraded"}`;
    els.connectionText.textContent = ok ? "Conectado" : "Degradado";
  } catch {
    els.connectionDot.className    = "connection-dot error";
    els.connectionText.textContent = "Sin conexión";
  }
}

async function pollAll() {
  await Promise.all([loadDrivers(), loadAlerts(), checkConnection()]);
  renderAll();
}

// ── Tabla — ordenamiento ──────────────────────────────
document.querySelectorAll(".driver-table th[data-col]").forEach(th => {
  th.addEventListener("click", () => {
    const col = th.dataset.col;
    if (state.sortCol === col) {
      state.sortAsc = !state.sortAsc;
    } else {
      state.sortCol = col;
      state.sortAsc = true;
    }
    renderTable();
  });
});

// ── Modal: Registrar conductor ────────────────────────
function openModal() {
  els.inputName.value  = "";
  els.inputPlate.value = "";
  els.formError.style.display = "none";
  els.modalOverlay.style.display = "flex";
  els.inputName.focus();
}

function closeModal() {
  els.modalOverlay.style.display = "none";
}

els.btnRegister.addEventListener("click", openModal);
els.btnCloseModal.addEventListener("click", closeModal);
els.btnCancelModal.addEventListener("click", closeModal);

els.modalOverlay.addEventListener("click", e => {
  if (e.target === els.modalOverlay) closeModal();
});

els.btnSubmitDriver.addEventListener("click", async () => {
  const name  = els.inputName.value.trim();
  const plate = els.inputPlate.value.trim();

  if (!name) {
    els.formError.textContent    = "El nombre es obligatorio.";
    els.formError.style.display  = "block";
    return;
  }

  els.btnSubmitDriver.disabled      = true;
  els.btnSubmitDriver.textContent   = "Registrando...";
  els.formError.style.display       = "none";

  try {
    const res = await fetch(`${API_BASE}/drivers/`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ name, license_plate: plate || null }),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Error al registrar");
    }

    closeModal();
    await pollAll();
  } catch (e) {
    els.formError.textContent   = e.message;
    els.formError.style.display = "block";
  } finally {
    els.btnSubmitDriver.disabled    = false;
    els.btnSubmitDriver.textContent = "Registrar";
  }
});

// ── Init ──────────────────────────────────────────────
initTheme();
pollAll();
setInterval(pollAll, POLL_INTERVAL);