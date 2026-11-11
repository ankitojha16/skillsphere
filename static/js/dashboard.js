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

    // 52-Week Study Consistency Heatmap Rendering
    const heatmapGrid = document.getElementById('studyHeatmapGrid');
    const heatmapDaysEl = document.getElementById('heatmapDaysData');
    const hoverInfoEl = document.getElementById('heatmapHoverInfo');

    if (heatmapGrid && heatmapDaysEl) {
        try {
            const days = JSON.parse(heatmapDaysEl.textContent);
            const levelColors = {
                0: 'rgba(255, 255, 255, 0.05)',
                1: 'rgba(14, 165, 233, 0.35)',
                2: 'rgba(14, 165, 233, 0.65)',
                3: '#0ea5e9',
                4: '#38bdf8'
            };

            const fragment = document.createDocumentFragment();
            days.forEach(day => {
                const cell = document.createElement('div');
                cell.className = 'heatmap-cell';
                cell.style.width = '12px';
                cell.style.height = '12px';
                cell.style.borderRadius = '2px';
                cell.style.backgroundColor = levelColors[day.level] || levelColors[0];
                cell.style.cursor = 'pointer';
                cell.style.transition = 'transform 0.15s ease, box-shadow 0.15s ease';
                if (day.level === 4) {
                    cell.style.boxShadow = '0 0 5px rgba(56, 189, 248, 0.6)';
                }

                cell.setAttribute('title', `${day.count} activity on ${day.display_date}`);

                cell.addEventListener('mouseenter', () => {
                    cell.style.transform = 'scale(1.35)';
                    cell.style.zIndex = '5';
                    if (hoverInfoEl) {
                        if (day.count > 0) {
                            hoverInfoEl.innerHTML = `<strong class="text-white">${day.display_date}</strong>: <span class="text-info fw-semibold">${day.count} study actions</span> (${day.lessons} lessons completed)`;
                        } else {
                            hoverInfoEl.innerHTML = `<strong class="text-white">${day.display_date}</strong>: <span class="text-secondary">No study records on this day</span>`;
                        }
                    }
                });

                cell.addEventListener('mouseleave', () => {
                    cell.style.transform = 'scale(1)';
                    cell.style.zIndex = '1';
                });

                fragment.appendChild(cell);
            });

            heatmapGrid.appendChild(fragment);

            heatmapGrid.addEventListener('mouseleave', () => {
                if (hoverInfoEl) {
                    hoverInfoEl.textContent = 'Hover over any day to inspect completed lessons & activity';
                }
            });
        } catch (e) {
            console.error("Error rendering study heatmap", e);
        }
    }
});
