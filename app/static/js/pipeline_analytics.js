/**
 * Sales Pipeline Analytics JavaScript
 * Handles chart creation and data visualization for pipeline analytics
 */
document.addEventListener('DOMContentLoaded', function() {
    // Initialize charts if the elements exist
    initializeConversionRateChart();
    initializeStageTimeChart();
    initializeDealValueChart();
    initializePipelineVelocityChart();
    
    // Filter form handling
    const filterForm = document.getElementById('analyticsFilterForm');
    if (filterForm) {
        filterForm.addEventListener('submit', function(e) {
            e.preventDefault();
            refreshAnalytics();
        });
    }
    
    /**
     * Initialize the conversion rate chart
     */
    function initializeConversionRateChart() {
        const conversionRateCanvas = document.getElementById('conversionRateChart');
        if (!conversionRateCanvas) return;
        
        // Get data from the data attribute
        const stageNames = JSON.parse(conversionRateCanvas.getAttribute('data-stage-names') || '[]');
        const conversionRates = JSON.parse(conversionRateCanvas.getAttribute('data-conversion-rates') || '[]');
        
        new Chart(conversionRateCanvas.getContext('2d'), {
            type: 'bar',
            data: {
                labels: stageNames,
                datasets: [{
                    label: 'Conversion Rate (%)',
                    data: conversionRates,
                    backgroundColor: 'rgba(54, 162, 235, 0.6)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        title: {
                            display: true,
                            text: 'Conversion Rate (%)'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Pipeline Stages'
                        }
                    }
                },
                plugins: {
                    title: {
                        display: true,
                        text: 'Stage Conversion Rates'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.raw.toFixed(1) + '%';
                            }
                        }
                    }
                }
            }
        });
    }
    
    /**
     * Initialize the average time in stage chart
     */
    function initializeStageTimeChart() {
        const stageTimeCanvas = document.getElementById('stageTimeChart');
        if (!stageTimeCanvas) return;
        
        // Get data from the data attribute
        const stageNames = JSON.parse(stageTimeCanvas.getAttribute('data-stage-names') || '[]');
        const stageTimes = JSON.parse(stageTimeCanvas.getAttribute('data-stage-times') || '[]');
        
        new Chart(stageTimeCanvas.getContext('2d'), {
            type: 'bar',
            data: {
                labels: stageNames,
                datasets: [{
                    label: 'Average Time (days)',
                    data: stageTimes,
                    backgroundColor: 'rgba(75, 192, 192, 0.6)',
                    borderColor: 'rgba(75, 192, 192, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Average Time (days)'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Pipeline Stages'
                        }
                    }
                },
                plugins: {
                    title: {
                        display: true,
                        text: 'Average Time in Stage'
                    }
                }
            }
        });
    }
    
    /**
     * Initialize the deal value by stage chart
     */
    function initializeDealValueChart() {
        const dealValueCanvas = document.getElementById('dealValueChart');
        if (!dealValueCanvas) return;
        
        // Get data from the data attribute
        const stageNames = JSON.parse(dealValueCanvas.getAttribute('data-stage-names') || '[]');
        const dealValues = JSON.parse(dealValueCanvas.getAttribute('data-deal-values') || '[]');
        const dealCounts = JSON.parse(dealValueCanvas.getAttribute('data-deal-counts') || '[]');
        
        new Chart(dealValueCanvas.getContext('2d'), {
            type: 'bar',
            data: {
                labels: stageNames,
                datasets: [
                    {
                        label: 'Total Value ($)',
                        data: dealValues,
                        backgroundColor: 'rgba(255, 159, 64, 0.6)',
                        borderColor: 'rgba(255, 159, 64, 1)',
                        borderWidth: 1,
                        yAxisID: 'y'
                    },
                    {
                        label: 'Number of Deals',
                        data: dealCounts,
                        backgroundColor: 'rgba(153, 102, 255, 0.6)',
                        borderColor: 'rgba(153, 102, 255, 1)',
                        borderWidth: 1,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Total Value ($)'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        beginAtZero: true,
                        grid: {
                            drawOnChartArea: false
                        },
                        title: {
                            display: true,
                            text: 'Number of Deals'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Pipeline Stages'
                        }
                    }
                },
                plugins: {
                    title: {
                        display: true,
                        text: 'Deal Value and Count by Stage'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                if (context.dataset.label === 'Total Value ($)') {
                                    return '$' + context.raw.toLocaleString();
                                } else {
                                    return context.raw + ' deals';
                                }
                            }
                        }
                    }
                }
            }
        });
    }
    
    /**
     * Initialize the pipeline velocity chart
     */
    function initializePipelineVelocityChart() {
        const velocityCanvas = document.getElementById('velocityChart');
        if (!velocityCanvas) return;
        
        // Get data from the data attribute
        const months = JSON.parse(velocityCanvas.getAttribute('data-months') || '[]');
        const velocities = JSON.parse(velocityCanvas.getAttribute('data-velocities') || '[]');
        
        new Chart(velocityCanvas.getContext('2d'), {
            type: 'line',
            data: {
                labels: months,
                datasets: [{
                    label: 'Pipeline Velocity (days)',
                    data: velocities,
                    backgroundColor: 'rgba(255, 99, 132, 0.2)',
                    borderColor: 'rgba(255, 99, 132, 1)',
                    borderWidth: 2,
                    tension: 0.3,
                    fill: false
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Average Days to Close'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Month'
                        }
                    }
                },
                plugins: {
                    title: {
                        display: true,
                        text: 'Pipeline Velocity Over Time'
                    }
                }
            }
        });
    }
    
    /**
     * Refresh analytics data based on filter form
     */
    function refreshAnalytics() {
        const filterForm = document.getElementById('analyticsFilterForm');
        if (!filterForm) return;
        
        const formData = new FormData(filterForm);
        const params = new URLSearchParams(formData);
        
        // Show loading indicator
        const loadingIndicator = document.getElementById('loadingIndicator');
        if (loadingIndicator) {
            loadingIndicator.classList.remove('d-none');
        }
        
        // Fetch updated data
        fetch('/pipeline/analytics?' + params.toString(), {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update the charts with new data
                updateCharts(data);
                
                // Update summary statistics
                updateSummaryStats(data);
            } else {
                alert('Error: ' + data.message);
            }
            
            // Hide loading indicator
            if (loadingIndicator) {
                loadingIndicator.classList.add('d-none');
            }
        })
        .catch(error => {
            console.error('Error refreshing analytics:', error);
            alert('Error refreshing analytics. Please try again.');
            
            // Hide loading indicator
            if (loadingIndicator) {
                loadingIndicator.classList.add('d-none');
            }
        });
    }
    
    /**
     * Update charts with new data
     */
    function updateCharts(data) {
        // Get chart instances
        const charts = Chart.getChart('conversionRateChart');
        const stageTimeChart = Chart.getChart('stageTimeChart');
        const dealValueChart = Chart.getChart('dealValueChart');
        const velocityChart = Chart.getChart('velocityChart');
        
        // Update conversion rate chart
        if (charts && data.conversion_rates) {
            charts.data.labels = data.stage_names;
            charts.data.datasets[0].data = data.conversion_rates;
            charts.update();
        }
        
        // Update stage time chart
        if (stageTimeChart && data.stage_times) {
            stageTimeChart.data.labels = data.stage_names;
            stageTimeChart.data.datasets[0].data = data.stage_times;
            stageTimeChart.update();
        }
        
        // Update deal value chart
        if (dealValueChart && data.deal_values) {
            dealValueChart.data.labels = data.stage_names;
            dealValueChart.data.datasets[0].data = data.deal_values;
            dealValueChart.data.datasets[1].data = data.deal_counts;
            dealValueChart.update();
        }
        
        // Update velocity chart
        if (velocityChart && data.velocities) {
            velocityChart.data.labels = data.months;
            velocityChart.data.datasets[0].data = data.velocities;
            velocityChart.update();
        }
    }
    
    /**
     * Update summary statistics
     */
    function updateSummaryStats(data) {
        // Update summary statistics if they exist
        const elements = {
            totalDeals: document.getElementById('totalDeals'),
            totalValue: document.getElementById('totalValue'),
            avgDealSize: document.getElementById('avgDealSize'),
            winRate: document.getElementById('winRate'),
            avgDaysToClose: document.getElementById('avgDaysToClose')
        };
        
        if (elements.totalDeals && data.total_deals !== undefined) {
            elements.totalDeals.textContent = data.total_deals;
        }
        
        if (elements.totalValue && data.total_value !== undefined) {
            elements.totalValue.textContent = '$' + data.total_value.toLocaleString();
        }
        
        if (elements.avgDealSize && data.avg_deal_size !== undefined) {
            elements.avgDealSize.textContent = '$' + data.avg_deal_size.toLocaleString();
        }
        
        if (elements.winRate && data.win_rate !== undefined) {
            elements.winRate.textContent = data.win_rate.toFixed(1) + '%';
        }
        
        if (elements.avgDaysToClose && data.avg_days_to_close !== undefined) {
            elements.avgDaysToClose.textContent = data.avg_days_to_close.toFixed(1) + ' days';
        }
    }
});
