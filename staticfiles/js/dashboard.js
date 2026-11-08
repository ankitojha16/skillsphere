// SkillSphere Dashboard Charts with Chart.js

document.addEventListener('DOMContentLoaded', () => {
    const activityChartCanvas = document.getElementById('weeklyActivityChart');
    if (!activityChartCanvas) return;

    let labels = [];
    let counts = [];

    try {
        const labelsEl = document.getElementById('chartLabelsData');
        const countsEl = document.getElementById('chartCountsData');
        if (labelsEl && countsEl) {
            labels = JSON.parse(labelsEl.textContent);
            counts = JSON.parse(countsEl.textContent);
        }
    } catch (e) {
        console.error("Error parsing chart data", e);
        labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
        counts = [0, 0, 0, 0, 0, 0, 0];
    }

    const ctx = activityChartCanvas.getContext('2d');
    
    // Create gradient
    const gradient = ctx.createLinearGradient(0, 0, 0, 240);
    gradient.addColorStop(0, 'rgba(139, 92, 246, 0.9)');
    gradient.addColorStop(1, 'rgba(6, 182, 212, 0.2)');

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Completed Lessons',
                data: counts,
                backgroundColor: gradient,
                borderRadius: 8,
                borderSkipped: false,
                barThickness: 28,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: '#151F35',
                    titleColor: '#F8FAFC',
                    bodyColor: '#A78BFA',
                    borderColor: '#354663',
                    borderWidth: 1,
                    padding: 12,
                    cornerRadius: 8,
                    callbacks: {
                        label: function(context) {
                            return `${context.parsed.y} lesson${context.parsed.y === 1 ? '' : 's'} completed`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false,
                        drawBorder: false,
                    },
                    ticks: {
                        color: '#CBD5E1',
                        font: {
                            family: 'Inter',
                            size: 12,
                            weight: '500'
                        }
                    }
                },
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1,
                        color: '#A8B7CC',
                        font: {
                            family: 'Inter',
                            size: 12,
                            weight: '500'
                        }
                    },
                    grid: {
                        color: 'rgba(53, 70, 99, 0.4)',
                        drawBorder: false,
                    }
                }
            }
        }
    });
});
