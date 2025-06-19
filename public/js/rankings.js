class Rankings {
    constructor() {
        this.charts = {};
    }
    
    init() {
        this.loadRankingsData();
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        // Model selector for detailed stats
        const statsModelSelect = document.getElementById('stats-model-select');
        if (statsModelSelect) {
            statsModelSelect.addEventListener('change', (e) => {
                if (e.target.value) {
                    this.loadDetailedStats(e.target.value);
                }
            });
        }
    }
    
    async loadRankingsData() {
        try {
            Utils.showLoading('Carregando rankings...');
            
            // Load ELO rankings
            const eloRankings = await api.getEloRatings();
            this.updateEloRankingsTable(eloRankings);
            
            // Load ELO progression chart
            const eloHistory = await api.getEloHistory();
            this.createEloProgressionChart(eloHistory);
            
            // Load opening statistics
            const openingStats = await api.getOpeningStats();
            this.updateOpeningsTable(openingStats);
            this.createOpeningsPopularityChart(openingStats);
            
            // Update model selectors
            await this.updateModelSelectors();
            
            Utils.hideLoading();
        } catch (error) {
            Utils.hideLoading();
            Utils.handleError(error, 'loadRankingsData');
        }
    }
    
    updateEloRankingsTable(rankings) {
        const tbody = document.querySelector('#elo-rankings-table tbody');
        if (!tbody) return;
        
        tbody.innerHTML = '';
        
        if (!rankings || rankings.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center">Nenhum ranking disponível</td></tr>';
            return;
        }
        
        // Sort by ELO rating
        const sortedRankings = rankings.sort((a, b) => (b.elo || 1500) - (a.elo || 1500));
        
        sortedRankings.forEach((ranking, index) => {
            const row = document.createElement('tr');
            
            // Add medal icons for top 3
            let positionDisplay = index + 1;
            if (index === 0) positionDisplay = '🥇 1';
            else if (index === 1) positionDisplay = '🥈 2';
            else if (index === 2) positionDisplay = '🥉 3';
            
            row.innerHTML = `
                <td>${positionDisplay}</td>
                <td>
                    <strong>${ranking.model}</strong>
                    ${ranking.elo >= 1600 ? '⭐' : ''}
                </td>
                <td>
                    <span class="elo-rating ${this.getEloClass(ranking.elo)}">
                        ${Utils.formatElo(ranking.elo)}
                    </span>
                </td>
                <td>${ranking.games_played || 0}</td>
                <td>
                    <div class="progress-bar-small">
                        <div class="progress-fill" style="width: ${(ranking.win_rate || 0) * 100}%"></div>
                    </div>
                    <span>${Utils.formatPercentage((ranking.win_rate || 0) * 100)}</span>
                </td>
                <td>${Utils.formatPercentage(ranking.avg_accuracy || 0)}</td>
            `;
            
            tbody.appendChild(row);
        });
    }
    
    getEloClass(elo) {
        if (elo >= 1800) return 'elo-master';
        if (elo >= 1600) return 'elo-expert';
        if (elo >= 1400) return 'elo-intermediate';
        return 'elo-beginner';
    }
    
    createEloProgressionChart(eloHistory) {
        if (!eloHistory || eloHistory.length === 0) {
            const chartContainer = document.getElementById('elo-progression-chart');
            if (chartContainer) {
                chartContainer.innerHTML = '<p>Nenhum histórico de ELO disponível</p>';
            }
            return;
        }
        
        // Group data by model
        const modelData = {};
        eloHistory.forEach(entry => {
            if (!modelData[entry.model]) {
                modelData[entry.model] = [];
            }
            modelData[entry.model].push({
                x: entry.date,
                y: entry.elo
            });
        });
        
        // Create datasets
        const datasets = Object.entries(modelData).map(([model, data], index) => ({
            label: model,
            data: data,
            borderColor: this.getModelColor(index),
            backgroundColor: this.getModelColor(index, 0.1),
            tension: 0.1,
            fill: false
        }));
        
        const config = {
            type: 'line',
            data: { datasets },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Evolução do Rating ELO'
                    },
                    legend: {
                        position: 'top'
                    }
                },
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            unit: 'day'
                        },
                        title: {
                            display: true,
                            text: 'Data'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Rating ELO'
                        },
                        min: 1200,
                        max: 2000
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                }
            }
        };
        
        this.charts.eloProgression = app.createChart('elo-progression-chart', config);
    }
    
    getModelColor(index, alpha = 1) {
        const colors = [
            `rgba(102, 126, 234, ${alpha})`,
            `rgba(220, 53, 69, ${alpha})`,
            `rgba(40, 167, 69, ${alpha})`,
            `rgba(255, 193, 7, ${alpha})`,
            `rgba(23, 162, 184, ${alpha})`,
            `rgba(108, 117, 125, ${alpha})`,
            `rgba(111, 66, 193, ${alpha})`,
            `rgba(253, 126, 20, ${alpha})`
        ];
        return colors[index % colors.length];
    }
    
    async updateModelSelectors() {
        try {
            const models = await api.getAvailableModels();
            const modelNames = Object.keys(models);
            
            const statsModelSelect = document.getElementById('stats-model-select');
            if (statsModelSelect) {
                statsModelSelect.innerHTML = '<option value="">Selecione um modelo...</option>';
                modelNames.forEach(name => {
                    const option = document.createElement('option');
                    option.value = name;
                    option.textContent = name;
                    statsModelSelect.appendChild(option);
                });
            }
        } catch (error) {
            Utils.handleError(error, 'updateModelSelectors');
        }
    }
    
    async loadDetailedStats(modelName) {
        try {
            Utils.showLoading('Carregando estatísticas detalhadas...');
            
            const stats = await api.getDetailedStats(modelName);
            this.displayDetailedStats(stats, modelName);
            
            Utils.hideLoading();
        } catch (error) {
            Utils.hideLoading();
            Utils.handleError(error, 'loadDetailedStats');
        }
    }
    
    displayDetailedStats(stats, modelName) {
        // Update metrics
        const metricsContainer = document.getElementById('model-metrics');
        if (metricsContainer) {
            metricsContainer.innerHTML = `
                <div class="metric-card">
                    <div class="metric-icon">🎮</div>
                    <div class="metric-content">
                        <h3>${stats.total_games || 0}</h3>
                        <p>Partidas Jogadas</p>
                    </div>
                </div>
                <div class="metric-card">
                    <div class="metric-icon">🏆</div>
                    <div class="metric-content">
                        <h3>${Utils.formatPercentage(stats.win_rate || 0)}</h3>
                        <p>Taxa de Vitória</p>
                    </div>
                </div>
                <div class="metric-card">
                    <div class="metric-icon">🎯</div>
                    <div class="metric-content">
                        <h3>${Utils.formatPercentage(stats.avg_accuracy || 0)}</h3>
                        <p>Precisão Média</p>
                    </div>
                </div>
                <div class="metric-card">
                    <div class="metric-icon">⭐</div>
                    <div class="metric-content">
                        <h3>${Utils.formatElo(stats.current_elo || 1500)}</h3>
                        <p>Rating ELO</p>
                    </div>
                </div>
            `;
        }
        
        // Performance by color
        if (stats.by_color) {
            this.createColorPerformanceChart(stats.by_color, modelName);
        }
        
        // Recent performance trend
        if (stats.recent_trend && stats.recent_trend.length > 0) {
            this.createRecentPerformanceChart(stats.recent_trend, modelName);
        }
    }
    
    createColorPerformanceChart(colorData, modelName) {
        const chartContainer = document.getElementById('color-performance');
        if (!chartContainer) return;
        
        chartContainer.innerHTML = '<canvas id="color-performance-canvas"></canvas>';
        
        const whiteData = colorData.white || {};
        const blackData = colorData.black || {};
        
        const config = {
            type: 'bar',
            data: {
                labels: ['Brancas', 'Pretas'],
                datasets: [
                    {
                        label: 'Vitórias',
                        data: [whiteData.wins || 0, blackData.wins || 0],
                        backgroundColor: 'rgba(40, 167, 69, 0.8)'
                    },
                    {
                        label: 'Empates',
                        data: [whiteData.draws || 0, blackData.draws || 0],
                        backgroundColor: 'rgba(108, 117, 125, 0.8)'
                    },
                    {
                        label: 'Derrotas',
                        data: [whiteData.losses || 0, blackData.losses || 0],
                        backgroundColor: 'rgba(220, 53, 69, 0.8)'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: `Performance por Cor - ${modelName}`
                    }
                },
                scales: {
                    x: {
                        stacked: true
                    },
                    y: {
                        stacked: true,
                        beginAtZero: true
                    }
                }
            }
        };
        
        this.charts.colorPerformance = app.createChart('color-performance-canvas', config);
    }
    
    createRecentPerformanceChart(recentTrend, modelName) {
        const chartContainer = document.getElementById('recent-performance');
        if (!chartContainer) return;
        
        chartContainer.innerHTML = '<canvas id="recent-performance-canvas"></canvas>';
        
        const config = {
            type: 'line',
            data: {
                labels: recentTrend.map((_, index) => `Partida ${index + 1}`),
                datasets: [{
                    label: 'Precisão (%)',
                    data: recentTrend,
                    borderColor: 'rgb(102, 126, 234)',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    tension: 0.1,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: `Tendência Recente - ${modelName} (Últimas ${recentTrend.length} Partidas)`
                    },
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        title: {
                            display: true,
                            text: 'Precisão (%)'
                        }
                    }
                }
            }
        };
        
        this.charts.recentPerformance = app.createChart('recent-performance-canvas', config);
    }
    
    updateOpeningsTable(openingStats) {
        const tbody = document.querySelector('#openings-table tbody');
        if (!tbody) return;
        
        tbody.innerHTML = '';
        
        if (!openingStats || openingStats.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center">Nenhuma estatística de abertura disponível</td></tr>';
            return;
        }
        
        // Sort by games played
        const sortedStats = openingStats.sort((a, b) => (b.games_played || 0) - (a.games_played || 0));
        
        sortedStats.forEach(opening => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td><strong>${opening.opening}</strong></td>
                <td>${opening.games_played || 0}</td>
                <td>
                    <div class="progress-bar-small">
                        <div class="progress-fill" style="width: ${(opening.win_rate || 0) * 100}%"></div>
                    </div>
                    <span>${Utils.formatPercentage((opening.win_rate || 0) * 100)}</span>
                </td>
                <td>${Utils.formatPercentage(opening.avg_accuracy || 0)}</td>
                <td>${(opening.avg_game_length || 0).toFixed(1)}</td>
            `;
            tbody.appendChild(row);
        });
    }
    
    createOpeningsPopularityChart(openingStats) {
        if (!openingStats || openingStats.length === 0) {
            const chartContainer = document.getElementById('openings-popularity-chart');
            if (chartContainer) {
                chartContainer.innerHTML = '<p>Nenhuma estatística de abertura disponível</p>';
            }
            return;
        }
        
        // Take top 8 most played openings
        const topOpenings = openingStats
            .sort((a, b) => (b.games_played || 0) - (a.games_played || 0))
            .slice(0, 8);
        
        const config = {
            type: 'doughnut',
            data: {
                labels: topOpenings.map(o => o.opening),
                datasets: [{
                    data: topOpenings.map(o => o.games_played || 0),
                    backgroundColor: topOpenings.map((_, index) => this.getModelColor(index, 0.8)),
                    borderColor: topOpenings.map((_, index) => this.getModelColor(index, 1)),
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Popularidade das Aberturas'
                    },
                    legend: {
                        position: 'bottom'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((context.parsed / total) * 100).toFixed(1);
                                return `${context.label}: ${context.parsed} partidas (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        };
        
        this.charts.openingsPopularity = app.createChart('openings-popularity-chart', config);
    }
    
    destroy() {
        // Destroy all charts
        Object.values(this.charts).forEach(chart => {
            if (chart && chart.destroy) {
                chart.destroy();
            }
        });
        this.charts = {};
    }
}

// Make Rankings available globally
window.Rankings = Rankings;