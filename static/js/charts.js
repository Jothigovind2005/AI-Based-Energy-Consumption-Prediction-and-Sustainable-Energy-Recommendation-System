/**
 * Chart.js Integration Module for AI Energy Prediction System.
 * Renders smooth gradients, time-series curves, hourly load distributions,
 * appliance breakdowns, and actual vs predicted comparisons.
 */

const ChartManager = {
  charts: {},

  initDashboardCharts() {
    fetch('/api/dashboard-charts')
      .then(response => response.json())
      .then(data => {
        this.renderTimeSeriesChart('energyTimeSeriesChart', data.time_series);
        this.renderHourlyProfileChart('hourlyProfileChart', data.hourly_profile);
        this.renderApplianceDonut('applianceDonutChart', data.appliance_share);
      })
      .catch(err => console.error('Error fetching dashboard charts:', err));
  },

  renderTimeSeriesChart(canvasId, timeSeriesData) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    if (this.charts[canvasId]) {
      this.charts[canvasId].destroy();
    }

    const gradient = ctx.getContext('2d').createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, 'rgba(16, 185, 129, 0.4)');
    gradient.addColorStop(1, 'rgba(16, 185, 129, 0.0)');

    this.charts[canvasId] = new Chart(ctx, {
      type: 'line',
      data: {
        labels: timeSeriesData.labels,
        datasets: [
          {
            label: 'Energy Consumption (kWh)',
            data: timeSeriesData.values,
            borderColor: '#10b981',
            backgroundColor: gradient,
            borderWidth: 2.5,
            fill: true,
            tension: 0.35,
            pointRadius: 2,
            pointHoverRadius: 6,
            pointHoverBackgroundColor: '#06b6d4',
            pointHoverBorderColor: '#ffffff'
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: 'rgba(17, 24, 39, 0.9)',
            titleColor: '#f3f4f6',
            bodyColor: '#34d399',
            borderColor: 'rgba(255,255,255,0.1)',
            borderWidth: 1,
            padding: 10,
            displayColors: false,
            callbacks: {
              label: (context) => `Consumption: ${context.parsed.y} kWh`
            }
          }
        },
        scales: {
          x: {
            grid: { color: 'rgba(255, 255, 255, 0.05)' },
            ticks: { color: '#9ca3af', maxTicksLimit: 8 }
          },
          y: {
            grid: { color: 'rgba(255, 255, 255, 0.05)' },
            ticks: { color: '#9ca3af' },
            title: { display: true, text: 'Energy (kWh)', color: '#6b7280' }
          }
        }
      }
    });
  },

  renderHourlyProfileChart(canvasId, hourlyData) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    if (this.charts[canvasId]) {
      this.charts[canvasId].destroy();
    }

    this.charts[canvasId] = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: hourlyData.labels,
        datasets: [{
          label: 'Avg Load (kWh)',
          data: hourlyData.values,
          backgroundColor: hourlyData.values.map(val => val > 2.0 ? '#f43f5e' : (val > 1.2 ? '#f59e0b' : '#06b6d4')),
          borderRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (context) => `Avg Hourly Usage: ${context.parsed.y} kWh`
            }
          }
        },
        scales: {
          x: {
            grid: { display: false },
            ticks: { color: '#9ca3af', maxTicksLimit: 12 }
          },
          y: {
            grid: { color: 'rgba(255, 255, 255, 0.05)' },
            ticks: { color: '#9ca3af' }
          }
        }
      }
    });
  },

  renderApplianceDonut(canvasId, applianceData) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    if (this.charts[canvasId]) {
      this.charts[canvasId].destroy();
    }

    const palette = ['#10b981', '#06b6d4', '#6366f1', '#f59e0b', '#ec4899', '#8b5cf6', '#14b8a6', '#f43f5e'];

    this.charts[canvasId] = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: applianceData.labels,
        datasets: [{
          data: applianceData.values,
          backgroundColor: palette.slice(0, applianceData.labels.length),
          borderWidth: 2,
          borderColor: '#111827'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom',
            labels: { color: '#9ca3af', boxWidth: 12, padding: 12 }
          },
          tooltip: {
            callbacks: {
              label: (context) => `${context.label}: ${context.parsed} kWh/day`
            }
          }
        },
        cutout: '70%'
      }
    });
  },

  renderActualVsPredicted(canvasId, samplePoints) {
    const ctx = document.getElementById(canvasId);
    if (!ctx || !samplePoints) return;

    if (this.charts[canvasId]) {
      this.charts[canvasId].destroy();
    }

    const labels = samplePoints.map(p => `Sample #${p.sample_index}`);
    const actuals = samplePoints.map(p => p.actual);
    const predicted = samplePoints.map(p => p.predicted_best);

    this.charts[canvasId] = new Chart(ctx, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'Actual Ground Truth (kWh)',
            data: actuals,
            borderColor: '#3b82f6',
            backgroundColor: 'rgba(59, 130, 246, 0.15)',
            borderWidth: 2,
            tension: 0.2,
            pointRadius: 3
          },
          {
            label: 'AI Model Predicted (kWh)',
            data: predicted,
            borderColor: '#10b981',
            borderDash: [5, 5],
            backgroundColor: 'transparent',
            borderWidth: 2.5,
            tension: 0.2,
            pointRadius: 4,
            pointHoverRadius: 6
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'top',
            labels: { color: '#9ca3af', usePointStyle: true }
          }
        },
        scales: {
          x: {
            grid: { color: 'rgba(255, 255, 255, 0.05)' },
            ticks: { color: '#9ca3af', maxTicksLimit: 10 }
          },
          y: {
            grid: { color: 'rgba(255, 255, 255, 0.05)' },
            ticks: { color: '#9ca3af' },
            title: { display: true, text: 'Energy (kWh)', color: '#6b7280' }
          }
        }
      }
    });
  }
};

document.addEventListener('DOMContentLoaded', () => {
  if (document.getElementById('energyTimeSeriesChart')) {
    ChartManager.initDashboardCharts();
  }
});
