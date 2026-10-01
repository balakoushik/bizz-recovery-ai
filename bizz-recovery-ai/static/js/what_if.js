document.querySelectorAll('.wif-slider').forEach(slider => {
  slider.addEventListener('input', () => {
    document.getElementById(slider.id + '_val').textContent = slider.value;
  });
});

function healthColor(v) {
  if (v >= 70) return '#22c55e';
  if (v >= 45) return '#f59e0b';
  return '#ef4444';
}

async function runSimulation() {
  const projectId = document.getElementById('wifProject').value;
  const changes = {};
  document.querySelectorAll('.wif-slider').forEach(slider => {
    changes[slider.id] = parseFloat(slider.value);
  });

  const resultsEl = document.getElementById('wifResults');
  resultsEl.innerHTML = `<div class="chart-card text-center py-5"><div class="spinner-border text-light" role="status"></div><p class="mt-3 text-muted">Running simulation...</p></div>`;

  try {
    const res = await fetch('/api/what-if', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ project_id: parseInt(projectId), changes })
    });
    const data = await res.json();
    if (data.error) {
      resultsEl.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
      return;
    }
    renderResults(data);
  } catch (e) {
    resultsEl.innerHTML = `<div class="alert alert-danger">Simulation failed. Please try again.</div>`;
  }
}

function renderResults(data) {
  const b = data.before.health;
  const a = data.after.health;

  const rows = [
    ['Overall Health', 'overall_health'],
    ['Financial Health', 'financial_health'],
    ['Schedule Health', 'schedule_health'],
    ['Technical Health', 'technical_health'],
    ['Security Health', 'security_health'],
    ['Resource Health', 'resource_health'],
    ['Customer Health', 'customer_health'],
    ['Operational Health', 'operational_health'],
  ].map(([label, key]) => `
    <tr>
      <td class="text-muted">${label}</td>
      <td>${b[key]}</td>
      <td><i class="bi bi-arrow-right text-muted"></i></td>
      <td style="color:${healthColor(a[key])}; font-weight:700;">${a[key]}</td>
      <td>${(a[key] - b[key]) >= 0 ? '+' : ''}${(a[key] - b[key]).toFixed(1)}</td>
    </tr>
  `).join('');

  document.getElementById('wifResults').innerHTML = `
    <div class="chart-card mb-3">
      <h6><i class="bi bi-arrow-left-right me-1"></i>Before vs After</h6>
      <table class="table table-sm align-middle">
        <thead><tr><th>Metric</th><th>Before</th><th></th><th>After</th><th>Δ</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
    <div class="chart-card mb-3">
      <h6><i class="bi bi-diagram-3-fill me-1"></i>Risk Count</h6>
      <p class="mb-0">Before: <strong>${data.before.risk_count}</strong> active risk(s) &nbsp;→&nbsp; After: <strong>${data.after.risk_count}</strong> active risk(s)</p>
    </div>
    <div class="chart-card">
      <h6><i class="bi bi-chat-left-text-fill me-1"></i>What Changed and Why</h6>
      <p class="mb-0">${data.explanation}</p>
    </div>
  `;
}
