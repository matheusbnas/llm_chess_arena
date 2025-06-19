class Dashboard {
    constructor() {
        this.charts = {};
        this.statsUpdateInterval = null;
    }
    
    init() {
        this.loadDashboardData();
        this.setupAutoRefresh();
    }
    
    async loadDashboardData() {
        try {
            Utils.showLoading('Carregando dados do dashboard...');
            
            // Load global stats
            const stats = await api.getGlobalStats();
            this.updateMetrics(stats);
            
            // Load charts data
            const resultsData = await api.getResultsByModel();
            const winrateData = await api.getWinrateData();
            
            this.createResultsChart(resultsData);
            this.createWinrateChart(winrateData);
            
            // Load recent games
            const recentGames = await api.getRecentGames(10);
            this.updateRecentGamesTable(recentGames);
            
            Utils.hideLoading();
        } catch (error) {
            Utils.hideLoading();
            Utils.handleError(error, 'loadDashboardData');
        }
    }
    
    updateMetrics(stats) {
        const elements = {
            'total-games': stats.totalGames || 0,
            'active-models': stats.activeModels || 0,
            'avg-moves': Math.round(stats.avgGameLength || 0),
            'tournaments': stats.tournamentsCompleted || 0
        };
        
        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                this.animateCounter(element, parseInt(element.textContent) || 0, value);
            }
        });
    }
    
    animateCounter(element, start, end) {
        const duration = 1000;
        const startTime = performance.now();
        
        const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            const current = Math.round(start + (end - start) * progress);
            element.textContent = current;
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };
        
        requestAnimationFrame(animate);
    }
    
    createResultsChart(data) {
        if (!data || data.length === 0) {
            document.getElementById('results-chart').innerHTML = '<p>Nenhum dado disponível</p>';
            return;
        }
        
        const config = {
            type: 'bar',
            data: {
                labels: data.map(d => d.model),
                datasets: [
                    {
                        label: 'Vitórias',
                        data: data.map(d => d.wins),
                        backgroundColor: 'rgba(40, 167, 69, 0.8)',
                        borderColor: 'rgba(40, 167, 69, 1)',
                        borderWidth: 1
                    },
                    {
                        label: 'Empates',
                        data: data.map(d => d.draws),
                        backgroundColor: 'rgba(108, 117, 125, 0.8)',
                        borderColor: 'rgba(108, 117, 125, 1)',
                        borderWidth: 1
                    },
                    {
                        label: 'Derrotas',
                        data: data.map(d => d.losses),
                        backgroundColor: 'rgba(220, 53, 69, 0.8)',
                        borderColor: 'rgba(220, 53, 69, 1)',
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                    }
                },
                scales: {
                    x: {
                        stacked: true,
                    },
                    y: {
                        stacked: true,
                        beginAtZero: true
                    }
                }
            }
        };
        
        this.charts.results = app.createChart('results-chart', config);
    }
    
    createWinrateChart(data) {
        if (!data || data.length === 0) {
            document.getElementById('winrate-chart').innerHTML = '<p>Nenhum dado disponível</p>';
            return;
        }
        
        const config = {
            type: 'doughnut',
            data: {
                labels: data.map(d => d.result_type),
                datasets: [{
                    data: data.map(d => d.percentage),
                    backgroundColor: [
                        'rgba(40, 167, 69, 0.8)',
                        'rgba(220, 53, 69, 0.8)',
                        'rgba(108, 117, 125, 0.8)'
                    ],
                    borderColor: [
                        'rgba(40, 167, 69, 1)',
                        'rgba(220, 53, 69, 1)',
                        'rgba(108, 117, 125, 1)'
                    ],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((context.parsed / total) * 100).toFixed(1);
                                return `${context.label}: ${context.parsed} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        };
        
        this.charts.winrate = app.createChart('winrate-chart', config);
    }
    
    updateRecentGamesTable(games) {
        const tbody = document.querySelector('#recent-games-table tbody');
        if (!tbody) return;
        
        tbody.innerHTML = '';
        
        if (!games || games.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center">Nenhuma partida encontrada</td></tr>';
            return;
        }
        
        games.forEach(game => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${game.White || 'N/A'}</td>
                <td>${game.Black || 'N/A'}</td>
                <td>
                    <span class="result-badge" style="background-color: ${Utils.getResultColor(game.Result)}">
                        ${Utils.getResultText(game.Result)}
                    </span>
                </td>
                <td>${game.Moves || 0}</td>
                <td>${Utils.formatDate(game.Date)}</td>
                <td>
                    <button class="btn btn-sm" onclick="dashboard.viewGame(${game.id || 0})">
                        <i class="fas fa-eye"></i> Ver
                    </button>
                </td>
            `;
            tbody.appendChild(row);
        });
    }
    
    viewGame(gameId) {
        // Switch to analysis page and load the game
        app.showPage('analysis');
        
        // Update nav
        document.querySelectorAll('.nav-btn').forEach(btn => btn.classList.remove('active'));
        document.querySelector('[data-page="analysis"]').classList.add('active');
        
        // Load the game in analysis
        if (app.analysis) {
            app.analysis.loadGame(gameId);
        }
    }
    
    setupAutoRefresh() {
        // Refresh dashboard every 30 seconds
        this.statsUpdateInterval = setInterval(() => {
            this.loadDashboardData();
        }, 30000);
    }
    
    destroy() {
        if (this.statsUpdateInterval) {
            clearInterval(this.statsUpdateInterval);
        }
        
        // Destroy charts
        Object.values(this.charts).forEach(chart => {
            if (chart && chart.destroy) {
                chart.destroy();
            }
        });
        this.charts = {};
    }
}

// Make Dashboard available globally
window.Dashboard = Dashboard;