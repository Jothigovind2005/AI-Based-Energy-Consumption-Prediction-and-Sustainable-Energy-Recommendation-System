/**
 * Dashboard & Interactive Client Logic
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Theme Switcher Logic
  const themeToggleBtn = document.getElementById('themeToggleBtn');
  const savedTheme = localStorage.getItem('energy_app_theme') || 'dark';
  document.documentElement.setAttribute('data-theme', savedTheme);
  updateThemeIcon(savedTheme);

  if (themeToggleBtn) {
    themeToggleBtn.addEventListener('click', () => {
      const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
      const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', newTheme);
      localStorage.setItem('energy_app_theme', newTheme);
      updateThemeIcon(newTheme);
    });
  }

  function updateThemeIcon(theme) {
    if (!themeToggleBtn) return;
    const icon = themeToggleBtn.querySelector('i');
    if (!icon) return;
    if (theme === 'light') {
      icon.className = 'bi bi-moon-stars-fill text-warning';
    } else {
      icon.className = 'bi bi-sun-fill text-warning';
    }
  }

  // 2. Interactive Prediction Sliders Real-time Sync
  const sliderInputs = document.querySelectorAll('.slider-sync');
  sliderInputs.forEach(input => {
    const outputBadge = document.getElementById(input.id + 'Val');
    if (outputBadge) {
      input.addEventListener('input', () => {
        outputBadge.textContent = input.value;
      });
    }
  });

  // 3. Live Prediction AJAX Trigger
  const livePredictForm = document.getElementById('predictionForm');
  if (livePredictForm) {
    const debouncedLivePredict = debounce(performLivePrediction, 250);
    livePredictForm.querySelectorAll('input, select').forEach(el => {
      el.addEventListener('input', debouncedLivePredict);
      el.addEventListener('change', debouncedLivePredict);
    });
  }

  function performLivePrediction() {
    const form = document.getElementById('predictionForm');
    if (!form) return;

    const payload = {
      occupants: parseInt(document.getElementById('occupants')?.value || 2),
      temperature: parseFloat(document.getElementById('temperature')?.value || 28),
      humidity: parseFloat(document.getElementById('humidity')?.value || 50),
      ac_hours: parseFloat(document.getElementById('ac_hours')?.value || 0.5),
      computer_hours: parseFloat(document.getElementById('computer_hours')?.value || 0.5),
      appliance_hours: parseFloat(document.getElementById('appliance_hours')?.value || 0.5),
      lights: parseInt(document.getElementById('lights')?.value || 3),
      fans: parseInt(document.getElementById('fans')?.value || 2),
      is_weekend: parseInt(document.getElementById('is_weekend')?.value || 0),
      model_name: document.getElementById('model_name')?.value || 'Gradient Boosting'
    };

    fetch('/api/predict-live', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
      .then(res => res.json())
      .then(data => {
        updatePredictionLiveUI(data);
      })
      .catch(err => console.error('Live prediction error:', err));
  }

  function updatePredictionLiveUI(res) {
    const kwhEl = document.getElementById('livePredictedKwh');
    const dailyKwhEl = document.getElementById('liveDailyKwh');
    const monthlyCostEl = document.getElementById('liveMonthlyCost');
    const monthlyCo2El = document.getElementById('liveMonthlyCo2');

    if (kwhEl) kwhEl.textContent = `${res.predicted_hourly_kwh} kWh`;
    if (dailyKwhEl) dailyKwhEl.textContent = `${res.predicted_daily_kwh} kWh/day`;
    if (monthlyCostEl) monthlyCostEl.textContent = `₹${res.monthly_cost}`;
    if (monthlyCo2El) monthlyCo2El.textContent = `${res.monthly_co2_kg} kg CO₂`;

    // Update model comparison table live values if present
    if (res.model_comparisons) {
      for (const [model, val] of Object.entries(res.model_comparisons)) {
        const rowVal = document.querySelector(`[data-model-pred="${model}"]`);
        if (rowVal) rowVal.textContent = `${val} kWh`;
      }
    }
  }

  function debounce(func, delay) {
    let timeout;
    return function (...args) {
      clearTimeout(timeout);
      timeout = setTimeout(() => func.apply(this, args), delay);
    };
  }

  // 4. Print / PDF Button
  const printBtn = document.getElementById('printReportBtn');
  if (printBtn) {
    printBtn.addEventListener('click', () => {
      window.print();
    });
  }

  // 5. Client Table Search
  const searchInput = document.getElementById('tableSearchInput');
  if (searchInput) {
    searchInput.addEventListener('keyup', () => {
      const filter = searchInput.value.toLowerCase();
      const rows = document.querySelectorAll('#dataTable tbody tr');
      rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(filter) ? '' : 'none';
      });
    });
  }
});
