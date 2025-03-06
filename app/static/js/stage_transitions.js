/**
 * Stage Transitions Analytics JavaScript
 * Handles visualization and analysis of deal stage transitions
 */
document.addEventListener('DOMContentLoaded', function() {
    // Initialize stage transition charts
    initializeTransitionChart();
    initializeTimeInStageChart();
    initializeConversionFunnelChart();
    
    // Initialize date range filter if available
    const dateRangeFilter = document.getElementById('transitionDateRange');
    if (dateRangeFilter && typeof daterangepicker !== 'undefined') {
        $(dateRangeFilter).daterangepicker({
            opens: 'left',
            autoUpdateInput: false,
            ranges: {
                'Last 7 Days': [moment().subtract(6, 'days'), moment()],
                'Last 30 Days': [moment().subtract(29, 'days'), moment()],
                'This Month': [moment().startOf('month'), moment().endOf('month')],
                'Last Month': [moment().subtract(1, 'month').startOf('month'), moment().subtract(1, 'month').endOf('month')],
                'Last 3 Months': [moment().subtract(3, 'months'), moment()],
                'Last 6 Months': [moment().subtract(6, 'months'), moment()],
                'Year to Date': [moment().startOf('year'), moment()]
            },
            locale: {
                cancelLabel: 'Clear',
                format: 'YYYY-MM-DD'
            }
        });
        
        $(dateRangeFilter).on('apply.daterangepicker', function(ev, picker) {
            $(this).val(picker.startDate.format('YYYY-MM-DD') + ' to ' + picker.endDate.format('YYYY-MM-DD'));
            refreshTransitionData();
        });
        
        $(dateRangeFilter).on('cancel.daterangepicker', function() {
            $(this).val('');
            refreshTransitionData();
        });
    }
    
    // Initialize pipeline selector
    const pipelineSelector = document.getElementById('transitionPipelineSelect');
    if (pipelineSelector) {
        pipelineSelector.addEventListener('change', function() {
            refreshTransitionData();
        });
    }
    
    /**
     * Initialize the stage transition flow chart
     */
    function initializeTransitionChart() {
        const transitionCanvas = document.getElementById('stageTransitionChart');
        if (!transitionCanvas) return;
        
        // Get data from data attributes
        const labels = JSON.parse(transitionCanvas.getAttribute('data-labels') || '[]');
        const datasets = JSON.parse(transitionCanvas.getAttribute('data-datasets') || '[]');
        
        new Chart(transitionCanvas.getContext('2d'), {
            type: 'sankey',
            data: {
                datasets: [{
                    data: datasets,
                    colorFrom: (c) => getColorForStage(c.dataset.data[c.dataIndex].from),
                    colorTo: (c) => getColorForStage(c.dataset.data[c.dataIndex].to),
                    colorMode: 'gradient',
                    labels: labels
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Deal Flow Between Stages',
                        font: {
                            size: 16
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const data = context.dataset.data[context.dataIndex];
                                return `${data.from} → ${data.to}: ${data.flow} deals`;
                            }
                        }
                    },
                    legend: {
                        display: false
                    }
                }
            }
        });
    }
    
    /**
     * Initialize the average time in stage chart
     */
    function initializeTimeInStageChart() {
        const timeInStageCanvas = document.getElementById('timeInStageChart');
        if (!timeInStageCanvas) return;
        
        // Get data from data attributes
        const stages = JSON.parse(timeInStageCanvas.getAttribute('data-stages') || '[]');
        const avgTimes = JSON.parse(timeInStageCanvas.getAttribute('data-avg-times') || '[]');
        const stageColors = JSON.parse(timeInStageCanvas.getAttribute('data-colors') || '[]');
        
        new Chart(timeInStageCanvas.getContext('2d'), {
            type: 'bar',
            data: {
                labels: stages,
                datasets: [{
                    label: 'Average Days in Stage',
                    data: avgTimes,
                    backgroundColor: stageColors,
                    borderColor: stageColors.map(color => adjustColorBrightness(color, -20)),
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
                            text: 'Days'
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
                        text: 'Average Time Spent in Each Stage',
                        font: {
                            size: 16
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const value = context.raw;
                                return `${value.toFixed(1)} days`;
                            }
                        }
                    }
                }
            }
        });
    }
    
    /**
     * Initialize the conversion funnel chart
     */
    function initializeConversionFunnelChart() {
        const funnelCanvas = document.getElementById('conversionFunnelChart');
        if (!funnelCanvas) return;
        
        // Get data from data attributes
        const stages = JSON.parse(funnelCanvas.getAttribute('data-stages') || '[]');
        const counts = JSON.parse(funnelCanvas.getAttribute('data-counts') || '[]');
        const stageColors = JSON.parse(funnelCanvas.getAttribute('data-colors') || '[]');
        
        new Chart(funnelCanvas.getContext('2d'), {
            type: 'bar',
            data: {
                labels: stages,
                datasets: [{
                    label: 'Number of Deals',
                    data: counts,
                    backgroundColor: stageColors,
                    borderColor: stageColors.map(color => adjustColorBrightness(color, -20)),
                    borderWidth: 1
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                scales: {
                    x: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Number of Deals'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Pipeline Stages'
                        }
                    }
                },
                plugins: {
                    title: {
                        display: true,
                        text: 'Deal Conversion Funnel',
                        font: {
                            size: 16
                        }
                    }
                }
            }
        });
    }
    
    /**
     * Refresh transition data based on filters
     */
    function refreshTransitionData() {
        // Show loading indicator
        showLoading();
        
        // Get filter values
        const pipelineId = document.getElementById('transitionPipelineSelect')?.value || '';
        const dateRange = document.getElementById('transitionDateRange')?.value || '';
        
        // Build query parameters
        const params = new URLSearchParams();
        if (pipelineId) params.append('pipeline_id', pipelineId);
        if (dateRange) params.append('date_range', dateRange);
        
        // Fetch updated data
        fetch('/pipeline/stage_transitions?' + params.toString(), {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update charts with new data
                updateTransitionCharts(data);
                
                // Update summary statistics
                updateTransitionStats(data);
            } else {
                alert('Error: ' + data.message);
            }
            
            // Hide loading indicator
            hideLoading();
        })
        .catch(error => {
            console.error('Error refreshing transition data:', error);
            alert('Error refreshing data. Please try again.');
            
            // Hide loading indicator
            hideLoading();
        });
    }
    
    /**
     * Update transition charts with new data
     */
    function updateTransitionCharts(data) {
        // Update stage transition chart
        const transitionChart = Chart.getChart('stageTransitionChart');
        if (transitionChart && data.transition_data) {
            transitionChart.data.datasets[0].data = data.transition_data;
            transitionChart.data.datasets[0].labels = data.stage_names;
            transitionChart.update();
        }
        
        // Update time in stage chart
        const timeInStageChart = Chart.getChart('timeInStageChart');
        if (timeInStageChart && data.avg_times) {
            timeInStageChart.data.labels = data.stage_names;
            timeInStageChart.data.datasets[0].data = data.avg_times;
            timeInStageChart.data.datasets[0].backgroundColor = data.stage_colors;
            timeInStageChart.data.datasets[0].borderColor = data.stage_colors.map(color => adjustColorBrightness(color, -20));
            timeInStageChart.update();
        }
        
        // Update conversion funnel chart
        const funnelChart = Chart.getChart('conversionFunnelChart');
        if (funnelChart && data.deal_counts) {
            funnelChart.data.labels = data.stage_names;
            funnelChart.data.datasets[0].data = data.deal_counts;
            funnelChart.data.datasets[0].backgroundColor = data.stage_colors;
            funnelChart.data.datasets[0].borderColor = data.stage_colors.map(color => adjustColorBrightness(color, -20));
            funnelChart.update();
        }
    }
    
    /**
     * Update transition statistics
     */
    function updateTransitionStats(data) {
        // Update summary statistics if they exist
        const elements = {
            totalTransitions: document.getElementById('totalTransitions'),
            avgStageTime: document.getElementById('avgStageTime'),
            conversionRate: document.getElementById('overallConversionRate'),
            bottleneckStage: document.getElementById('bottleneckStage')
        };
        
        if (elements.totalTransitions && data.total_transitions !== undefined) {
            elements.totalTransitions.textContent = data.total_transitions;
        }
        
        if (elements.avgStageTime && data.avg_stage_time !== undefined) {
            elements.avgStageTime.textContent = data.avg_stage_time.toFixed(1) + ' days';
        }
        
        if (elements.conversionRate && data.overall_conversion_rate !== undefined) {
            elements.conversionRate.textContent = data.overall_conversion_rate.toFixed(1) + '%';
        }
        
        if (elements.bottleneckStage && data.bottleneck_stage !== undefined) {
            elements.bottleneckStage.textContent = data.bottleneck_stage;
        }
    }
    
    /**
     * Get color for a stage name
     */
    function getColorForStage(stageName) {
        // Try to find the stage color from the data attribute
        const stageColorsElement = document.getElementById('stageColors');
        if (stageColorsElement) {
            try {
                const stageColors = JSON.parse(stageColorsElement.getAttribute('data-stage-colors') || '{}');
                if (stageColors[stageName]) {
                    return stageColors[stageName];
                }
            } catch (e) {
                console.error('Error parsing stage colors:', e);
            }
        }
        
        // Fallback to a hash-based color
        return stringToColor(stageName);
    }
    
    /**
     * Convert a string to a color using a hash function
     */
    function stringToColor(str) {
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            hash = str.charCodeAt(i) + ((hash << 5) - hash);
        }
        
        let color = '#';
        for (let i = 0; i < 3; i++) {
            const value = (hash >> (i * 8)) & 0xFF;
            color += ('00' + value.toString(16)).substr(-2);
        }
        
        return color;
    }
    
    /**
     * Adjust color brightness
     */
    function adjustColorBrightness(hex, percent) {
        // Convert hex to RGB
        let r = parseInt(hex.substring(1, 3), 16);
        let g = parseInt(hex.substring(3, 5), 16);
        let b = parseInt(hex.substring(5, 7), 16);
        
        // Adjust brightness
        r = Math.max(0, Math.min(255, r + percent));
        g = Math.max(0, Math.min(255, g + percent));
        b = Math.max(0, Math.min(255, b + percent));
        
        // Convert back to hex
        return '#' + 
            ((1 << 24) + (r << 16) + (g << 8) + b)
            .toString(16)
            .slice(1);
    }
    
    /**
     * Show loading indicator
     */
    function showLoading() {
        const loadingIndicator = document.getElementById('loadingIndicator');
        if (loadingIndicator) {
            loadingIndicator.classList.remove('d-none');
        }
    }
    
    /**
     * Hide loading indicator
     */
    function hideLoading() {
        const loadingIndicator = document.getElementById('loadingIndicator');
        if (loadingIndicator) {
            loadingIndicator.classList.add('d-none');
        }
    }
});
