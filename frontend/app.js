/**
 * NEXUS SUPPLY CHAIN AI - EXECUTIVE DASHBOARD LOGIC
 * Connects to FastAPI Backend with Chart.js visualization,
 * K-Means clustering telemetry, GPT simulation, and STRIDE security.
 */

// Determine API Base URL
const isDirectFile = window.location.protocol === 'file:';
const API_BASE = isDirectFile ? 'http://127.0.0.1:8000' : '';

// Global State
const state = {
  apiKey: localStorage.getItem('retail_api_key') || 'dev-key',
  selectedScenario: 'Normal',
  salesData: [],
  warehouseData: [],
  clusterCounts: {},
  inventory: [],
  charts: {
    sales: null,
    warehouse: null
  }
};

// DOM Elements
const el = {
  statusDot: document.querySelector('.status-dot'),
  statusLabel: document.getElementById('status-label'),
  btnRefresh: document.getElementById('btn-refresh'),
  btnOpenUpload: document.getElementById('btn-open-upload'),
  btnTriggerPipeline: document.getElementById('btn-trigger-pipeline'),
  
  // KPIs
  kpiRevenue: document.getElementById('kpi-revenue'),
  kpiUnits: document.getElementById('kpi-units'),
  kpiNetwork: document.getElementById('kpi-network'),
  kpiHighDemand: document.getElementById('kpi-high-demand'),

  // Tabs
  navTabs: document.querySelectorAll('.nav-tab'),
  tabPanes: document.querySelectorAll('.tab-pane'),

  // Clustering
  clusterLowCount: document.getElementById('cluster-low-count'),
  clusterMedCount: document.getElementById('cluster-med-count'),
  clusterHighCount: document.getElementById('cluster-high-count'),
  clusterLowPct: document.getElementById('cluster-low-pct'),
  clusterMedPct: document.getElementById('cluster-med-pct'),
  clusterHighPct: document.getElementById('cluster-high-pct'),
  clusterImg: document.getElementById('cluster-img'),
  btnReloadPlot: document.getElementById('btn-reload-plot'),
  inventoryFilter: document.getElementById('inventory-filter'),
  inventoryTbody: document.getElementById('inventory-tbody'),

  // AI Sim
  scenarioBtns: document.querySelectorAll('.scenario-btn'),
  selectedScenarioName: document.getElementById('selected-scenario-name'),
  btnRunSim: document.getElementById('btn-run-sim'),
  simResExpected: document.getElementById('sim-res-expected'),
  simResDelta: document.getElementById('sim-res-delta'),
  simResRisk: document.getElementById('sim-res-risk'),
  simResRec: document.getElementById('sim-res-recommendation'),
  simResExp: document.getElementById('sim-res-explanation'),
  aiSourceBadge: document.getElementById('ai-source-badge'),
  aiTimestamp: document.getElementById('ai-timestamp'),
  simBaseUnits: document.getElementById('sim-base-units'),
  simBaseStock: document.getElementById('sim-base-stock'),
  simBaseHigh: document.getElementById('sim-base-high'),

  // Warehouses
  warehouseTbody: document.getElementById('warehouse-tbody'),
  whQuickStats: document.getElementById('wh-quick-stats'),

  // STRIDE
  strideTbody: document.getElementById('stride-tbody'),

  // Modals
  uploadModal: document.getElementById('upload-modal'),
  btnCloseUpload: document.getElementById('btn-close-upload'),
  btnCancelUpload: document.getElementById('btn-cancel-upload'),
  btnSubmitUpload: document.getElementById('btn-submit-upload'),
  dropZone: document.getElementById('drop-zone'),
  fileInput: document.getElementById('file-input'),
  fileInfo: document.getElementById('file-info'),

  pipelineModal: document.getElementById('pipeline-modal'),
  btnClosePipeline: document.getElementById('btn-close-pipeline'),
  btnCancelPipeline: document.getElementById('btn-cancel-pipeline'),
  btnConfirmPipeline: document.getElementById('btn-confirm-pipeline'),
  pipelineTerminal: document.getElementById('pipeline-terminal'),

  toastContainer: document.getElementById('toast-container')
};

/* ==========================================================================
   INITIALIZATION
   ========================================================================== */
document.addEventListener('DOMContentLoaded', () => {
  initControls();
  initTabs();
  initModals();
  initScenarioSelector();
  renderStrideMatrix();
  checkHealthAndLoad();
});

function initControls() {
  el.btnRefresh.addEventListener('click', () => {
    showToast('Refreshing telemetry...', 'info');
    loadAllData();
  });
}

function initTabs() {
  el.navTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const target = tab.dataset.tab;
      el.navTabs.forEach(t => t.classList.remove('active'));
      el.tabPanes.forEach(p => p.classList.remove('active'));

      tab.classList.add('active');
      const pane = document.getElementById(target);
      if (pane) pane.classList.add('active');
    });
  });

  // Inventory table filter
  el.inventoryFilter.addEventListener('input', (e) => {
    const query = e.target.value.toLowerCase().trim();
    filterInventoryTable(query);
  });

  // Reload cluster image
  el.btnReloadPlot.addEventListener('click', () => {
    el.clusterImg.src = `${API_BASE}/cluster-plot?t=${Date.now()}`;
    showToast('Reloaded cluster plot', 'info');
  });
}

/* ==========================================================================
   DATA LOADING & HEALTH CHECK
   ========================================================================== */
async function checkHealthAndLoad() {
  try {
    const res = await fetch(`${API_BASE}/`, { headers: { Accept: 'application/json' } });
    if (res.ok) {
      el.statusDot.className = 'status-dot online';
      el.statusLabel.textContent = 'API Live (Connected)';
      loadAllData();
    } else {
      throw new Error(`HTTP ${res.status}`);
    }
  } catch (err) {
    el.statusDot.className = 'status-dot offline';
    el.statusLabel.textContent = 'API Offline';
    showToast(`Failed to connect to backend: ${err.message}`, 'error');
  }
}

async function loadAllData() {
  await Promise.allSettled([
    fetchSalesSummary(),
    fetchWarehouseSummary(),
    fetchClusterDemand(),
    fetchInventory()
  ]);
  updateOverallKPIs();
}

/* ==========================================================================
   API CALLS
   ========================================================================== */
async function fetchSalesSummary() {
  try {
    const res = await fetch(`${API_BASE}/sales-summary`);
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();
    state.salesData = data;
    renderSalesChart(data);
  } catch (err) {
    console.error('Error fetching sales-summary:', err);
  }
}

async function fetchWarehouseSummary() {
  try {
    const res = await fetch(`${API_BASE}/warehouse-summary`);
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();
    state.warehouseData = data;
    renderWarehouseChart(data);
    renderWarehouseTable(data);
  } catch (err) {
    console.error('Error fetching warehouse-summary:', err);
  }
}

async function fetchClusterDemand() {
  try {
    const res = await fetch(`${API_BASE}/cluster-demand`);
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();
    
    let total = 0;
    const counts = { Low: 0, Medium: 0, High: 0 };
    data.forEach(item => {
      counts[item.demand_level] = item.products;
      total += item.products;
    });
    state.clusterCounts = counts;

    el.clusterLowCount.textContent = counts.Low || 0;
    el.clusterMedCount.textContent = counts.Medium || 0;
    el.clusterHighCount.textContent = counts.High || 0;

    if (total > 0) {
      el.clusterLowPct.textContent = `${Math.round((counts.Low / total) * 100)}% of Catalog`;
      el.clusterMedPct.textContent = `${Math.round((counts.Medium / total) * 100)}% of Catalog`;
      el.clusterHighPct.textContent = `${Math.round((counts.High / total) * 100)}% of Catalog`;
    }

    el.kpiHighDemand.textContent = `${counts.High || 9} SKUs`;
  } catch (err) {
    console.error('Error fetching cluster-demand:', err);
  }
}

async function fetchInventory() {
  try {
    const res = await fetch(`${API_BASE}/inventory-summary`);
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();
    state.inventory = data;
    renderInventoryTable(data);
  } catch (err) {
    console.error('Error fetching inventory-summary:', err);
  }
}

function updateOverallKPIs() {
  if (state.salesData.length > 0) {
    const totalRev = state.salesData.reduce((acc, row) => acc + (row.revenue || 0), 0);
    const totalUnits = state.salesData.reduce((acc, row) => acc + (row.units || 0), 0);

    el.kpiRevenue.textContent = `$${(totalRev / 1000000).toFixed(2)}M`;
    el.kpiUnits.textContent = totalUnits.toLocaleString();
    el.simBaseUnits.textContent = `${totalUnits.toLocaleString()} units`;
  }

  if (state.warehouseData.length > 0) {
    el.kpiNetwork.textContent = `${state.warehouseData.length} WH / 20 Stores`;
  }
}

/* ==========================================================================
   CHARTS RENDERING (Chart.js)
   ========================================================================== */
function renderSalesChart(data) {
  const ctx = document.getElementById('salesChart');
  if (!ctx) return;

  const labels = data.map(d => `${d.year}-${String(d.month).padStart(2, '0')}`);
  const revenues = data.map(d => d.revenue);
  const units = data.map(d => d.units);

  if (state.charts.sales) {
    state.charts.sales.destroy();
  }

  state.charts.sales = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Revenue ($)',
          data: revenues,
          yAxisID: 'yRev',
          backgroundColor: '#0F172A',
          borderColor: '#0F172A',
          borderWidth: 1,
          borderRadius: 4,
          order: 2
        },
        {
          label: 'Units Sold',
          data: units,
          yAxisID: 'yUnits',
          type: 'line',
          borderColor: '#64748B',
          backgroundColor: 'transparent',
          borderWidth: 2,
          pointBackgroundColor: '#0F172A',
          pointRadius: 4,
          tension: 0.3,
          fill: false,
          order: 1
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#FFFFFF',
          titleColor: '#0F172A',
          bodyColor: '#334155',
          borderColor: '#E2E8F0',
          borderWidth: 1,
          padding: 10,
          titleFont: { family: 'Outfit', size: 12, weight: '700' },
          bodyFont: { family: 'Plus Jakarta Sans', size: 11 },
          callbacks: {
            label: function(context) {
              if (context.dataset.label === 'Revenue ($)') {
                return ` Revenue: $${context.raw.toLocaleString()}`;
              }
              return ` Units: ${context.raw.toLocaleString()}`;
            }
          }
        }
      },
      scales: {
        x: {
          grid: { color: '#F1F5F9' },
          ticks: { color: '#64748B', font: { family: 'JetBrains Mono', size: 11 } }
        },
        yRev: {
          position: 'left',
          grid: { color: '#F1F5F9' },
          ticks: {
            color: '#0F172A',
            font: { family: 'JetBrains Mono', size: 11 },
            callback: value => `$${(value / 1000000).toFixed(1)}M`
          }
        },
        yUnits: {
          position: 'right',
          grid: { drawOnChartArea: false },
          ticks: {
            color: '#64748B',
            font: { family: 'JetBrains Mono', size: 11 },
            callback: value => `${(value / 1000).toFixed(0)}k`
          }
        }
      }
    }
  });
}

function renderWarehouseChart(data) {
  const ctx = document.getElementById('warehouseChart');
  if (!ctx) return;

  const labels = data.map(d => `WH ${d.warehouse_id}`);
  const units = data.map(d => d.units_sold);

  if (state.charts.warehouse) {
    state.charts.warehouse.destroy();
  }

  state.charts.warehouse = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Units Dispatched',
          data: units,
          backgroundColor: [
            '#0F172A',
            '#1E293B',
            '#334155',
            '#475569',
            '#64748B',
            '#0F172A',
            '#1E293B',
            '#334155',
            '#475569',
            '#64748B'
          ],
          borderRadius: 4
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#FFFFFF',
          titleColor: '#0F172A',
          bodyColor: '#334155',
          borderColor: '#E2E8F0',
          borderWidth: 1,
          padding: 10,
          callbacks: {
            label: context => ` Units Sold: ${context.raw.toLocaleString()}`
          }
        }
      },
      scales: {
        x: {
          grid: { color: '#F1F5F9' },
          ticks: { color: '#64748B', font: { family: 'JetBrains Mono', size: 10 } }
        },
        y: {
          grid: { color: '#F1F5F9' },
          ticks: {
            color: '#64748B',
            font: { family: 'JetBrains Mono', size: 10 },
            callback: value => `${(value / 1000).toFixed(0)}k`
          }
        }
      }
    }
  });

  // Render Mini stats below warehouse chart
  if (data.length > 0) {
    const topWH = [...data].sort((a, b) => b.units_sold - a.units_sold)[0];
    const avgStock = Math.round(data.reduce((acc, d) => acc + d.avg_stock, 0) / data.length);
    const totalRev = data.reduce((acc, d) => acc + d.revenue, 0);

    el.whQuickStats.innerHTML = `
      <div class="mini-stat-item">
        <div class="mini-stat-label">Top Hub</div>
        <div class="mini-stat-val">WH ${topWH.warehouse_id} (${(topWH.units_sold / 1000).toFixed(0)}k)</div>
      </div>
      <div class="mini-stat-item">
        <div class="mini-stat-label">Avg Stock / Hub</div>
        <div class="mini-stat-val">${avgStock.toLocaleString()}</div>
      </div>
      <div class="mini-stat-item">
        <div class="mini-stat-label">WH Network Rev</div>
        <div class="mini-stat-val">$${(totalRev / 1000000).toFixed(1)}M</div>
      </div>
    `;
  }
}

/* ==========================================================================
   TABLES RENDERING
   ========================================================================== */
function renderInventoryTable(items) {
  if (!items || items.length === 0) {
    el.inventoryTbody.innerHTML = `<tr><td colspan="5" class="loading-cell">No inventory records available.</td></tr>`;
    return;
  }

  el.inventoryTbody.innerHTML = items.map(p => {
    let badgeClass = 'badge-cyan';
    if (p.demand_level === 'High') badgeClass = 'badge-rose';
    else if (p.demand_level === 'Medium') badgeClass = 'badge-amber';
    else if (p.demand_level === 'Low') badgeClass = 'badge-emerald';

    const stockRatio = (p.avg_stock / Math.max(p.avg_daily_sales, 0.1)).toFixed(1);
    const riskStatus = stockRatio < 2 ? '<span class="badge badge-rose">Stockout Risk</span>' : '<span class="badge badge-emerald">Healthy</span>';

    return `
      <tr data-product-id="${p.product_id}">
        <td><strong>#${p.product_id}</strong></td>
        <td><span class="badge ${badgeClass}">${p.demand_level}</span></td>
        <td>${p.avg_daily_sales ? p.avg_daily_sales.toFixed(1) : '—'}</td>
        <td>${p.avg_stock ? Math.round(p.avg_stock).toLocaleString() : '—'}</td>
        <td>${riskStatus}</td>
      </tr>
    `;
  }).join('');
}

function filterInventoryTable(query) {
  const rows = el.inventoryTbody.querySelectorAll('tr[data-product-id]');
  rows.forEach(row => {
    const id = row.getAttribute('data-product-id');
    const text = row.textContent.toLowerCase();
    if (!query || text.includes(query) || id.includes(query)) {
      row.style.display = '';
    } else {
      row.style.display = 'none';
    }
  });
}

function renderWarehouseTable(items) {
  if (!items || items.length === 0) {
    el.warehouseTbody.innerHTML = `<tr><td colspan="6" class="loading-cell">No warehouse data found.</td></tr>`;
    return;
  }

  el.warehouseTbody.innerHTML = items.map(w => {
    const ratio = (w.avg_stock / Math.max(w.units_sold / 1000, 0.01)).toFixed(2);
    let riskTag = '<span class="badge badge-emerald">Balanced</span>';
    if (ratio < 4.5) riskTag = '<span class="badge badge-amber">Understock</span>';
    else if (ratio > 7.0) riskTag = '<span class="badge badge-rose">Overstock</span>';

    return `
      <tr>
        <td><strong>Warehouse ${w.warehouse_id}</strong></td>
        <td>${w.units_sold ? w.units_sold.toLocaleString() : 0} units</td>
        <td>${w.avg_stock ? w.avg_stock.toLocaleString() : 0}</td>
        <td>$${w.revenue ? w.revenue.toLocaleString() : 0}</td>
        <td><code>${ratio}x</code></td>
        <td>${riskTag}</td>
      </tr>
    `;
  }).join('');
}

/* ==========================================================================
   AI SCENARIO SIMULATION
   ========================================================================== */
function initScenarioSelector() {
  el.scenarioBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      el.scenarioBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      state.selectedScenario = btn.dataset.scenario;
      el.selectedScenarioName.textContent = state.selectedScenario;
    });
  });

  el.btnRunSim.addEventListener('click', runSimulation);
}

async function runSimulation() {
  const scenario = state.selectedScenario;
  el.btnRunSim.disabled = true;
  el.btnRunSim.querySelector('span').textContent = 'Simulating via AI...';

  try {
    const res = await fetch(`${API_BASE}/demand-simulation`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': state.apiKey
      },
      body: JSON.stringify({ scenario: scenario })
    });

    if (!res.ok) {
      const errText = await res.text();
      throw new Error(`Simulation failed: ${errText}`);
    }

    const data = await res.json();
    displaySimulationResult(data);
    showToast(`Simulation completed for scenario: ${scenario}`, 'success');
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    el.btnRunSim.disabled = false;
    el.btnRunSim.querySelector('span').innerHTML = `Run Simulation for <strong>${scenario}</strong>`;
  }
}

function displaySimulationResult(sim) {
  el.simResExpected.textContent = `${sim.expected_units ? sim.expected_units.toLocaleString() : '—'} units`;

  // Calculate delta %
  if (sim.baseline_units && sim.expected_units) {
    const delta = (((sim.expected_units - sim.baseline_units) / sim.baseline_units) * 100).toFixed(1);
    const isPositive = delta >= 0;
    el.simResDelta.textContent = `${isPositive ? '+' : ''}${delta}%`;
    el.simResDelta.className = `delta-badge ${isPositive ? 'delta-pos' : 'delta-neg'}`;
  }

  // Risk styling
  const risk = (sim.risk || 'low').toLowerCase();
  el.simResRisk.textContent = risk.toUpperCase();
  el.simResRisk.className = `risk-pill risk-${risk}`;

  // Recommendation & Explanation
  el.simResRec.textContent = sim.recommendation || 'No recommendation received.';
  el.simResExp.textContent = sim.explanation || '';

  // Source attribution
  const isGpt = sim.source === 'gpt';
  el.aiSourceBadge.textContent = isGpt ? 'Source: GPT-4o-mini' : 'Source: Rule Fallback Engine';
  el.aiSourceBadge.className = `badge ${isGpt ? 'badge-violet' : 'badge-amber'}`;
  el.aiTimestamp.textContent = `Generated: ${new Date().toLocaleTimeString()} (baseline: ${sim.baseline_from || 'sqlite'})`;

  if (sim.baseline_units) el.simBaseUnits.textContent = `${sim.baseline_units.toLocaleString()} units`;
  if (sim.baseline_stock) el.simBaseStock.textContent = `${sim.baseline_stock.toLocaleString()} units`;
  if (sim.high_demand_products) el.simBaseHigh.textContent = `${sim.high_demand_products} Products`;
}

/* ==========================================================================
   STRIDE SECURITY MATRIX
   ========================================================================== */
function renderStrideMatrix() {
  const strideData = [
    {
      endpoint: "POST /upload",
      s: "Fake client uploads data",
      t: "Malicious/poisoned CSV alters sales",
      r: "User denies uploading",
      i: "Uploaded file exposed on disk",
      d: "Huge files exhaust disk/memory",
      e: "Upload path abuse to overwrite files"
    },
    {
      endpoint: "POST /process",
      s: "Unauthorised pipeline trigger",
      t: "Process step scripts modified",
      r: "No durable audit of who ran it",
      i: "Stack traces leak internals",
      d: "Repeated Spark runs overload CPU/RAM",
      e: "Caller triggers privileged batch jobs"
    },
    {
      endpoint: "GET /*-summary",
      s: "Impersonating partner",
      t: "Response manipulated in transit",
      r: "—",
      i: "Competitors read stock/demand",
      d: "Request flooding",
      e: "Read APIs used to recon"
    },
    {
      endpoint: "GET /cluster-plot",
      s: "Unauthorized caller",
      t: "Image swapped / MITM",
      r: "—",
      i: "Cluster strategy visible to rivals",
      d: "Bandwidth abuse",
      e: "—"
    },
    {
      endpoint: "POST /demand-sim",
      s: "Stolen API key",
      t: "Prompt injection alters GPT",
      r: "No log of simulations",
      i: "Business baselines sent to GPT",
      d: "Cost/rate abuse of GPT",
      e: "Unlisted scenarios / privilege"
    }
  ];

  el.strideTbody.innerHTML = strideData.map(row => `
    <tr>
      <td><code>${row.endpoint}</code></td>
      <td>${row.s}</td>
      <td>${row.t}</td>
      <td>${row.r}</td>
      <td>${row.i}</td>
      <td>${row.d}</td>
      <td>${row.e}</td>
    </tr>
  `).join('');
}

/* ==========================================================================
   MODALS: UPLOAD & PIPELINE
   ========================================================================== */
function initModals() {
  // Upload modal events
  el.btnOpenUpload.addEventListener('click', () => {
    el.uploadModal.classList.add('show');
    resetUploadModal();
  });
  el.btnCloseUpload.addEventListener('click', () => el.uploadModal.classList.remove('show'));
  el.btnCancelUpload.addEventListener('click', () => el.uploadModal.classList.remove('show'));

  let selectedFile = null;

  el.dropZone.addEventListener('click', () => el.fileInput.click());
  el.fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
      handleFileSelected(e.target.files[0]);
    }
  });

  el.dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    el.dropZone.classList.add('dragover');
  });

  el.dropZone.addEventListener('dragleave', () => el.dropZone.classList.remove('dragover'));
  el.dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    el.dropZone.classList.remove('dragover');
    if (e.dataTransfer.files.length > 0) {
      handleFileSelected(e.dataTransfer.files[0]);
    }
  });

  function handleFileSelected(file) {
    if (!file.name.endsWith('.csv')) {
      showToast('Please select a valid .csv file', 'error');
      return;
    }
    if (file.size > 20 * 1024 * 1024) {
      showToast('File exceeds 20 MB limit (STRIDE DoS policy)', 'error');
      return;
    }
    selectedFile = file;
    el.fileInfo.textContent = `Selected: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
    el.btnSubmitUpload.disabled = false;
  }

  function resetUploadModal() {
    selectedFile = null;
    el.fileInput.value = '';
    el.fileInfo.textContent = '';
    el.btnSubmitUpload.disabled = true;
  }

  el.btnSubmitUpload.addEventListener('click', async () => {
    if (!selectedFile) return;

    el.btnSubmitUpload.disabled = true;
    el.btnSubmitUpload.textContent = 'Uploading...';

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const res = await fetch(`${API_BASE}/upload`, {
        method: 'POST',
        headers: { 'x-api-key': state.apiKey },
        body: formData
      });

      if (!res.ok) {
        throw new Error(await res.text());
      }

      showToast('Dataset uploaded successfully to data/sales.csv!', 'success');
      el.uploadModal.classList.remove('show');
    } catch (err) {
      showToast(`Upload failed: ${err.message}`, 'error');
    } finally {
      el.btnSubmitUpload.disabled = false;
      el.btnSubmitUpload.textContent = 'Upload to Server';
    }
  });

  // Pipeline modal events
  el.btnTriggerPipeline.addEventListener('click', () => {
    el.pipelineModal.classList.add('show');
    el.pipelineTerminal.innerHTML = `<div class="term-line">&gt; Ready. Click "Start Full Run" to execute Spark ETL + SQLite + K-Means.</div>`;
    el.btnConfirmPipeline.disabled = false;
  });

  el.btnClosePipeline.addEventListener('click', () => el.pipelineModal.classList.remove('show'));
  el.btnCancelPipeline.addEventListener('click', () => el.pipelineModal.classList.remove('show'));

  el.btnConfirmPipeline.addEventListener('click', async () => {
    el.btnConfirmPipeline.disabled = true;
    el.pipelineTerminal.innerHTML = `
      <div class="term-line">&gt; Initiating POST /process with auth key...</div>
      <div class="term-line">&gt; [1/3] Running PySpark: ingest sales.csv &rarr; clean DQ &rarr; MapReduce...</div>
      <div class="term-line">&gt; [2/3] Building SQLite Star Schema (dimensions + fact_sales)...</div>
      <div class="term-line">&gt; [3/3] Running K-Means clustering (k=3) & updating product_clusters...</div>
      <div class="term-line">&gt; Waiting for subprocess execution...</div>
    `;

    try {
      const res = await fetch(`${API_BASE}/process`, {
        method: 'POST',
        headers: { 'x-api-key': state.apiKey }
      });

      if (!res.ok) {
        throw new Error(await res.text());
      }

      const out = await res.json();
      el.pipelineTerminal.innerHTML += `<div class="term-line" style="color: #06B6D4;">&gt; Pipeline Finished Successfully! Status: ${out.status}</div>`;
      showToast('Full pipeline executed successfully!', 'success');
      
      // Auto-reload fresh data
      setTimeout(() => {
        loadAllData();
        el.clusterImg.src = `${API_BASE}/cluster-plot?t=${Date.now()}`;
      }, 1000);
    } catch (err) {
      el.pipelineTerminal.innerHTML += `<div class="term-line" style="color: #F43F5E;">&gt; Execution Failed: ${err.message}</div>`;
      showToast(`Pipeline failed: ${err.message}`, 'error');
    } finally {
      el.btnConfirmPipeline.disabled = false;
    }
  });
}

/* ==========================================================================
   TOAST NOTIFICATION HELPER
   ========================================================================== */
function showToast(message, type = 'info') {
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  
  const icon = type === 'success' ? '✓' : type === 'error' ? '✕' : 'ℹ';
  toast.innerHTML = `<span style="font-weight: bold;">${icon}</span> <span>${message}</span>`;
  
  el.toastContainer.appendChild(toast);
  
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(20px)';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}
