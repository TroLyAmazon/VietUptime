let chart;

async function loadLatency(targetId) {
  const res = await fetch(`/api/target/${targetId}/latency`);
  const data = await res.json();

  const canvas = document.getElementById("latencyChart");
  if (!canvas) return;

  if (chart) chart.destroy();

  chart = new Chart(canvas, {
    type: "line",
    data: {
      labels: data.labels,
      datasets: [{
        label: "Latency (ms)",
        data: data.values,
        tension: 0.25,
        spanGaps: true
      }]
    },
    options: {
      responsive: true,
      plugins: { legend: { display: true } },
      scales: {
        x: { ticks: { maxTicksLimit: 8 } },
        y: { beginAtZero: true }
      }
    }
  });
}

function getDefaultTargetId() {
  const el = document.getElementById("dotstatusData");
  if (!el) return null;

  const v = el.dataset.defaultTarget; // lấy từ data-default-target
  const n = parseInt(v, 10);

  return Number.isFinite(n) ? n : null;
}

function init() {
  const select = document.getElementById("targetSelect");
  if (!select) return;

  const defaultId = getDefaultTargetId();
  if (defaultId) {
    select.value = String(defaultId);
    loadLatency(defaultId);
  } else {
    // fallback: lấy option đang selected
    loadLatency(select.value);
  }

  select.addEventListener("change", () => {
    loadLatency(select.value);
  });

  // Refresh chart data mỗi 30s (UI-only)
  setInterval(() => {
    loadLatency(select.value);
  }, 30000);
}

document.addEventListener("DOMContentLoaded", init);
