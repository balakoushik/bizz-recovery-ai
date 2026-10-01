const CHART_COLORS = {
  primary: '#5b6cff', accent: '#22d3ee', success: '#22c55e',
  warning: '#f59e0b', danger: '#ef4444', critical: '#dc2626', muted: '#93a0bd',
};

function statCard(label, value, icon, accentClass) {
  return `
    <div class="col-6 col-lg-3">
      <div class="stat-card ${accentClass || ''}">
        <div class="stat-label">${label}</div>
        <div class="stat-value">${value}</div>
        <div class="stat-icon"><i class="bi ${icon}"></i></div>
      </div>
    </div>`;
}

Chart.defaults.color = '#93a0bd';
Chart.defaults.borderColor = '#232d45';
Chart.defaults.font.family = "Inter, sans-serif";

async function loadDashboard() {
  let data;
  try {
    const res = await fetch('/api/dashboard');
    data = await res.json();
  } catch (e) {
    document.getElementById('stat-cards').innerHTML =
      `<div class="col-12"><div class="alert alert-danger">Could not load dashboard data.</div></div>`;
    return;
  }

  renderCards(data);
  renderSeverityChart(data.severity_distribution);
  renderTrendChart(data.risk_trend);
  renderCategoryChart(data.category_distribution);
  renderProjectHealthChart(data.projects_summary);
  renderWarnings(data.warnings);
}

function renderCards(data) {
  const cards = [
    statCard('Business Health', data.business_health + '/100', 'bi-heart-pulse-fill', 'accent-primary'),
    statCard('Project Health', data.project_health + '/100', 'bi-speedometer2', 'accent-primary'),
    statCard('Total Projects', data.total_projects, 'bi-kanban-fill', ''),
    statCard('Active Risks', data.active_risks, 'bi-exclamation-diamond-fill', 'accent-warning'),
    statCard('Critical Risks', data.critical_risks, 'bi-fire', 'accent-danger'),
    statCard('High Risks', data.high_risks, 'bi-exclamation-triangle-fill', 'accent-warning'),
    statCard('Risks Resolved', data.resolved_risks, 'bi-check-circle-fill', 'accent-success'),
    statCard('Recovery Plans', data.recovery_plans, 'bi-life-preserver', ''),
    statCard('Predicted Risks', data.predicted_risks, 'bi-cpu-fill', ''),
    statCard('Budget Health', data.budget_health + '/100', 'bi-cash-coin', ''),
    statCard('Schedule Health', data.schedule_health + '/100', 'bi-calendar-check-fill', ''),
    statCard('Security Health', data.security_health + '/100', 'bi-shield-lock-fill', ''),
  ];
  document.getElementById('stat-cards').innerHTML = cards.join('');
}

function renderSeverityChart(dist) {
  new Chart(document.getElementById('chartSeverity'), {
    type: 'doughnut',
    data: {
      labels: ['Low', 'Medium', 'High', 'Critical'],
      datasets: [{
        data: [dist.LOW || 0, dist.MEDIUM || 0, dist.HIGH || 0, dist.CRITICAL || 0],
        backgroundColor: [CHART_COLORS.success, CHART_COLORS.warning, CHART_COLORS.danger, CHART_COLORS.critical],
        borderWidth: 0,
      }]
    },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom' } } }
  });
}

function renderTrendChart(trend) {
  const labels = trend.map(t => t.date);
  const values = trend.map(t => t.avg_risk_score);
  new Chart(document.getElementById('chartTrend'), {
    type: 'line',
    data: {
      labels: labels.length ? labels : ['No data'],
      datasets: [{
        label: 'Avg Risk Score',
        data: values.length ? values : [0],
        borderColor: CHART_COLORS.accent,
        backgroundColor: 'rgba(34,211,238,.15)',
        fill: true, tension: .35, pointRadius: 3,
      }]
    },
    options: { responsive: true, maintainAspectRatio: false, scales: { y: { min: 0, max: 100 } } }
  });
}

function renderCategoryChart(catDist) {
  const labels = Object.keys(catDist);
  const values = Object.values(catDist);
  new Chart(document.getElementById('chartCategory'), {
    type: 'bar',
    data: {
      labels: labels.length ? labels : ['No risks'],
      datasets: [{
        label: 'Active Risks',
        data: values.length ? values : [0],
        backgroundColor: CHART_COLORS.primary,
        borderRadius: 6,
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: { y: { beginAtZero: true, ticks: { precision: 0 } } }
    }
  });
}

function renderProjectHealthChart(summary) {
  const labels = summary.map(p => p.name);
  const values = summary.map(p => p.health);
  new Chart(document.getElementById('chartProjectHealth'), {
    type: 'bar',
    data: {
      labels: labels.length ? labels : ['No projects'],
      datasets: [{
        label: 'Health Score',
        data: values.length ? values : [0],
        backgroundColor: values.map(v => v >= 70 ? CHART_COLORS.success : v >= 45 ? CHART_COLORS.warning : CHART_COLORS.danger),
        borderRadius: 6,
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: { x: { min: 0, max: 100 } }
    }
  });
}

function renderWarnings(warnings) {
  const el = document.getElementById('warningsPanel');
  if (!warnings || warnings.length === 0) {
    el.innerHTML = '<p class="text-muted mb-0"><i class="bi bi-check-circle text-success me-1"></i>No active warnings. All monitored signals look healthy.</p>';
    return;
  }
  el.innerHTML = warnings.map(w => `
    <div class="warning-item sev-${w.severity}">
      <i class="bi bi-exclamation-triangle-fill mt-1"></i>
      <div>
        <span class="badge-severity badge-${w.severity} me-2">${w.severity}</span>
        <strong>${w.project}:</strong> ${w.message}
      </div>
    </div>
  `).join('');
}

loadDashboard();
