async function resolveRisk(riskId, btn) {
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';
  try {
    const res = await fetch(`/api/risks/${riskId}/resolve`, { method: 'POST' });
    if (res.ok) {
      const card = btn.closest('.risk-card');
      card.style.opacity = '0.4';
      card.style.pointerEvents = 'none';
      btn.innerHTML = '<i class="bi bi-check-circle-fill"></i> Resolved';
    } else {
      btn.innerHTML = '<i class="bi bi-x-lg"></i> Failed';
    }
  } catch (e) {
    btn.innerHTML = '<i class="bi bi-x-lg"></i> Failed';
  }
}
