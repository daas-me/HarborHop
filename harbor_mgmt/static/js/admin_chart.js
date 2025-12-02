// admin_chart.js - Chart functionality for admin dashboard

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Get chart data from data attributes
    const chartElement = document.getElementById('userGrowthChart');
    
    if (!chartElement) {
        console.error('Chart element not found');
        return;
    }
    
    // Get data from data attributes
    const labels = JSON.parse(chartElement.dataset.labels || '[]');
    const monthlyData = JSON.parse(chartElement.dataset.monthly || '[]');
    const cumulativeData = JSON.parse(chartElement.dataset.cumulative || '[]');
    
    // Chart configuration
    const ctx = chartElement.getContext('2d');
    let currentChart = 'monthly';
    
    const chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'New Users',
                data: monthlyData,
                borderColor: '#ff9500',
                backgroundColor: 'rgba(255, 149, 0, 0.1)',
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointRadius: 6,
                pointHoverRadius: 8,
                pointBackgroundColor: '#ff9500',
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                pointHoverBackgroundColor: '#ff9500',
                pointHoverBorderColor: '#fff',
                pointHoverBorderWidth: 3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    align: 'end',
                    labels: {
                        font: {
                            size: 13,
                            family: "'Alan Sans', sans-serif",
                            weight: '600'
                        },
                        padding: 20,
                        usePointStyle: true,
                        pointStyle: 'circle'
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(44, 62, 80, 0.95)',
                    padding: 12,
                    titleFont: {
                        size: 14,
                        family: "'Alan Sans', sans-serif",
                        weight: '600'
                    },
                    bodyFont: {
                        size: 13,
                        family: "'Alan Sans', sans-serif"
                    },
                    cornerRadius: 8,
                    displayColors: true,
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            label += context.parsed.y + ' users';
                            return label;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0,
                        font: {
                            size: 12,
                            family: "'Alan Sans', sans-serif"
                        },
                        color: '#7f8c8d'
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)',
                        drawBorder: false
                    }
                },
                x: {
                    ticks: {
                        font: {
                            size: 12,
                            family: "'Alan Sans', sans-serif"
                        },
                        color: '#7f8c8d',
                        maxRotation: 45,
                        minRotation: 0
                    },
                    grid: {
                        display: false,
                        drawBorder: false
                    }
                }
            },
            interaction: {
                intersect: false,
                mode: 'index'
            }
        }
    });

    // Toggle chart function
    window.toggleChart = function(type) {
        const buttons = document.querySelectorAll('.chart-toggle');
        buttons.forEach(btn => btn.classList.remove('active'));
        event.target.classList.add('active');

        if (type === 'monthly') {
            chart.data.datasets[0].label = 'New Users';
            chart.data.datasets[0].data = monthlyData;
            chart.data.datasets[0].borderColor = '#ff9500';
            chart.data.datasets[0].backgroundColor = 'rgba(255, 149, 0, 0.1)';
            chart.data.datasets[0].pointBackgroundColor = '#ff9500';
        } else {
            chart.data.datasets[0].label = 'Total Users';
            chart.data.datasets[0].data = cumulativeData;
            chart.data.datasets[0].borderColor = '#3498db';
            chart.data.datasets[0].backgroundColor = 'rgba(52, 152, 219, 0.1)';
            chart.data.datasets[0].pointBackgroundColor = '#3498db';
        }
        chart.update('active');
    };
});