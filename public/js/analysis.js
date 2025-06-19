class Analysis {
    constructor() {
        this.analysisBoard = null;
        this.currentGame = null;
        this.currentMoveIndex = 0;
        this.gameHistory = [];
    }
    
    init() {
        this.setupEventListeners();
        this.initializeBoard();
        this.loadGames();
    }
    
    setupEventListeners() {
        // Individual analysis
        const analyzeBtn = document.getElementById('analyze-game');
        if (analyzeBtn) {
            analyzeBtn.addEventListener('click', () => this.analyzeSelectedGame());
        }
        
        // Board navigation
        const firstMoveBtn = document.getElementById('first-move');
        if (firstMoveBtn) {
            firstMoveBtn.addEventListener('click', () => this.goToMove(0));
        }
        
        const prevMoveBtn = document.getElementById('prev-move');
        if (prevMoveBtn) {
            prevMoveBtn.addEventListener('click', () => this.goToMove(this.currentMoveIndex - 1));
        }
        
        const nextMoveBtn = document.getElementById('next-move');
        if (nextMoveBtn) {
            nextMoveBtn.addEventListener('click', () => this.goToMove(this.currentMoveIndex + 1));
        }
        
        const lastMoveBtn = document.getElementById('last-move');
        if (lastMoveBtn) {
            lastMoveBtn.addEventListener('click', () => this.goToMove(this.gameHistory.length));
        }
        
        // Move slider
        const moveSlider = document.getElementById('move-slider');
        if (moveSlider) {
            moveSlider.addEventListener('input', (e) => {
                this.goToMove(parseInt(e.target.value));
            });
        }
        
        // Comparative analysis
        const compareBtn = document.getElementById('compare-models');
        if (compareBtn) {
            compareBtn.addEventListener('click', () => this.compareModels());
        }
        
        // Lichess integration
        const testLichessBtn = document.getElementById('test-lichess');
        if (testLichessBtn) {
            testLichessBtn.addEventListener('click', () => this.testLichessConnection());
        }
        
        const importGamesBtn = document.getElementById('import-games');
        if (importGamesBtn) {
            importGamesBtn.addEventListener('click', () => this.importLichessGames());
        }
        
        const applyRAGBtn = document.getElementById('apply-rag');
        if (applyRAGBtn) {
            applyRAGBtn.addEventListener('click', () => this.applyRAGImprovements());
        }
        
        // Range sliders
        const maxImportGames = document.getElementById('max-import-games');
        if (maxImportGames) {
            maxImportGames.addEventListener('input', (e) => {
                document.getElementById('max-import-value').textContent = e.target.value;
            });
        }
    }
    
    initializeBoard() {
        const boardContainer = document.getElementById('analysis-chessboard');
        if (boardContainer) {
            this.analysisBoard = new ChessBoard('analysis-chessboard', {
                draggable: false,
                showCoordinates: true
            });
        }
    }
    
    async loadGames() {
        try {
            const games = await api.getGames();
            this.updateGameSelector(games);
            this.updateModelSelectors();
        } catch (error) {
            Utils.handleError(error, 'loadGames');
        }
    }
    
    updateGameSelector(games) {
        const gameSelect = document.getElementById('game-select');
        if (!gameSelect) return;
        
        gameSelect.innerHTML = '<option value="">Selecione uma partida...</option>';
        
        games.forEach(game => {
            const option = document.createElement('option');
            option.value = game.id;
            option.textContent = `${game.white} vs ${game.black} - ${Utils.getResultText(game.result)} (${Utils.formatDate(game.date)})`;
            gameSelect.appendChild(option);
        });
    }
    
    async updateModelSelectors() {
        try {
            const models = await api.getAvailableModels();
            const modelNames = Object.keys(models);
            
            const model1Select = document.getElementById('model1-select');
            const model2Select = document.getElementById('model2-select');
            
            [model1Select, model2Select].forEach(select => {
                if (select) {
                    select.innerHTML = '<option value="">Selecione um modelo...</option>';
                    modelNames.forEach(name => {
                        const option = document.createElement('option');
                        option.value = name;
                        option.textContent = name;
                        select.appendChild(option);
                    });
                }
            });
        } catch (error) {
            Utils.handleError(error, 'updateModelSelectors');
        }
    }
    
    async analyzeSelectedGame() {
        const gameSelect = document.getElementById('game-select');
        if (!gameSelect || !gameSelect.value) {
            Utils.showToast('Selecione uma partida para analisar', 'warning');
            return;
        }
        
        const gameId = gameSelect.value;
        await this.loadGame(gameId);
    }
    
    async loadGame(gameId) {
        try {
            Utils.showLoading('Carregando partida...');
            
            const game = await api.getGame(gameId);
            this.currentGame = game;
            
            // Parse game moves
            this.parseGameMoves(game.pgn);
            
            // Set initial position
            this.goToMove(0);
            
            // Analyze the game
            const analysis = await api.analyzeGame(gameId);
            this.displayAnalysisResults(analysis);
            
            Utils.hideLoading();
            Utils.showToast('Partida carregada e analisada!', 'success');
            
        } catch (error) {
            Utils.hideLoading();
            Utils.handleError(error, 'loadGame');
        }
    }
    
    parseGameMoves(pgn) {
        // This is a simplified PGN parser
        // In a real implementation, you'd use a proper chess library
        
        this.gameHistory = [];
        
        // Extract moves from PGN
        const movePattern = /\d+\.\s*([^\s]+)(?:\s+([^\s]+))?/g;
        let match;
        
        while ((match = movePattern.exec(pgn)) !== null) {
            if (match[1]) {
                this.gameHistory.push({
                    san: match[1],
                    fen: null // Would need to calculate FEN for each position
                });
            }
            if (match[2]) {
                this.gameHistory.push({
                    san: match[2],
                    fen: null
                });
            }
        }
        
        // Update move slider
        const moveSlider = document.getElementById('move-slider');
        if (moveSlider) {
            moveSlider.max = this.gameHistory.length;
            moveSlider.value = 0;
        }
    }
    
    goToMove(moveIndex) {
        if (moveIndex < 0) moveIndex = 0;
        if (moveIndex > this.gameHistory.length) moveIndex = this.gameHistory.length;
        
        this.currentMoveIndex = moveIndex;
        
        // Update move slider
        const moveSlider = document.getElementById('move-slider');
        if (moveSlider) {
            moveSlider.value = moveIndex;
        }
        
        // Update board position
        if (this.analysisBoard) {
            if (moveIndex === 0) {
                // Starting position
                this.analysisBoard.setPosition('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1');
            } else {
                // Would need to calculate FEN for the position
                // For now, just show starting position
                this.analysisBoard.setPosition('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1');
            }
        }
        
        // Show current move info
        if (moveIndex > 0 && moveIndex <= this.gameHistory.length) {
            const move = this.gameHistory[moveIndex - 1];
            const moveNumber = Math.ceil(moveIndex / 2);
            const color = moveIndex % 2 === 1 ? 'Brancas' : 'Pretas';
            
            Utils.showToast(`Lance ${moveNumber}: ${color} joga ${move.san}`, 'info', 3000);
        }
    }
    
    displayAnalysisResults(analysis) {
        if (!analysis) return;
        
        // Display metrics
        const metricsContainer = document.getElementById('analysis-metrics');
        if (metricsContainer) {
            metricsContainer.innerHTML = `
                <div class="metric-card">
                    <div class="metric-icon">⚪</div>
                    <div class="metric-content">
                        <h3>${analysis.white_accuracy?.toFixed(1) || 0}%</h3>
                        <p>Precisão das Brancas</p>
                    </div>
                </div>
                <div class="metric-card">
                    <div class="metric-icon">⚫</div>
                    <div class="metric-content">
                        <h3>${analysis.black_accuracy?.toFixed(1) || 0}%</h3>
                        <p>Precisão das Pretas</p>
                    </div>
                </div>
                <div class="metric-card">
                    <div class="metric-icon">📊</div>
                    <div class="metric-content">
                        <h3>${analysis.total_moves || 0}</h3>
                        <p>Total de Lances</p>
                    </div>
                </div>
                <div class="metric-card">
                    <div class="metric-icon">❌</div>
                    <div class="metric-content">
                        <h3>${analysis.blunders || 0}</h3>
                        <p>Erros Graves</p>
                    </div>
                </div>
            `;
        }
        
        // Display evaluation chart
        if (analysis.move_evaluations && analysis.move_evaluations.length > 0) {
            this.createEvaluationChart(analysis.move_evaluations);
        }
        
        // Display best/worst moves
        this.displayBestWorstMoves(analysis.best_moves, analysis.worst_moves);
    }
    
    createEvaluationChart(evaluations) {
        const chartContainer = document.getElementById('evaluation-chart');
        if (!chartContainer) return;
        
        // Create canvas for chart
        chartContainer.innerHTML = '<canvas id="eval-chart-canvas"></canvas>';
        
        const config = {
            type: 'line',
            data: {
                labels: evaluations.map((_, index) => index + 1),
                datasets: [{
                    label: 'Avaliação',
                    data: evaluations,
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
                        text: 'Avaliação da Posição por Lance'
                    },
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Lance'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Avaliação (peões)'
                        }
                    }
                }
            }
        };
        
        app.createChart('eval-chart-canvas', config);
    }
    
    displayBestWorstMoves(bestMoves, worstMoves) {
        const container = document.getElementById('best-worst-moves');
        if (!container) return;
        
        container.innerHTML = `
            <div class="moves-section">
                <h4>✅ Melhores Lances</h4>
                <div class="moves-list">
                    ${bestMoves?.slice(0, 3).map(move => `
                        <div class="move-item good">
                            <span class="move-number">Lance ${move.move_number}:</span>
                            <span class="move-san">${move.san}</span>
                            <span class="move-accuracy">${(move.accuracy * 100).toFixed(1)}%</span>
                        </div>
                    `).join('') || '<p>Nenhum dado disponível</p>'}
                </div>
            </div>
            <div class="moves-section">
                <h4>❌ Piores Lances</h4>
                <div class="moves-list">
                    ${worstMoves?.slice(0, 3).map(move => `
                        <div class="move-item bad">
                            <span class="move-number">Lance ${move.move_number}:</span>
                            <span class="move-san">${move.san}</span>
                            <span class="move-accuracy">${(move.accuracy * 100).toFixed(1)}%</span>
                        </div>
                    `).join('') || '<p>Nenhum dado disponível</p>'}
                </div>
            </div>
        `;
    }
    
    async compareModels() {
        const model1 = document.getElementById('model1-select').value;
        const model2 = document.getElementById('model2-select').value;
        
        if (!model1 || !model2) {
            Utils.showToast('Selecione ambos os modelos para comparar', 'warning');
            return;
        }
        
        if (model1 === model2) {
            Utils.showToast('Selecione modelos diferentes', 'warning');
            return;
        }
        
        try {
            Utils.showLoading('Comparando modelos...');
            
            const comparison = await api.compareModels(model1, model2);
            this.displayModelComparison(comparison, model1, model2);
            
            Utils.hideLoading();
            Utils.showToast('Comparação concluída!', 'success');
            
        } catch (error) {
            Utils.hideLoading();
            Utils.handleError(error, 'compareModels');
        }
    }
    
    displayModelComparison(comparison, model1, model2) {
        // Head-to-head record
        const headToHeadContainer = document.getElementById('head-to-head');
        if (headToHeadContainer) {
            headToHeadContainer.innerHTML = `
                <h4>🥊 Confronto Direto</h4>
                <div class="comparison-stats">
                    <div class="stat-item">
                        <div class="stat-value">${comparison.model1_wins || 0}</div>
                        <div class="stat-label">Vitórias ${model1}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">${comparison.draws || 0}</div>
                        <div class="stat-label">Empates</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">${comparison.model2_wins || 0}</div>
                        <div class="stat-label">Vitórias ${model2}</div>
                    </div>
                </div>
            `;
        }
        
        // Performance metrics
        const metricsContainer = document.getElementById('performance-metrics');
        if (metricsContainer) {
            metricsContainer.innerHTML = `
                <h4>📈 Métricas de Performance</h4>
                <table class="comparison-table">
                    <thead>
                        <tr>
                            <th>Métrica</th>
                            <th>${model1}</th>
                            <th>${model2}</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>Precisão Média</td>
                            <td>${(comparison.model1_accuracy || 0).toFixed(1)}%</td>
                            <td>${(comparison.model2_accuracy || 0).toFixed(1)}%</td>
                        </tr>
                        <tr>
                            <td>Lances por Partida</td>
                            <td>${(comparison.model1_avg_moves || 0).toFixed(1)}</td>
                            <td>${(comparison.model2_avg_moves || 0).toFixed(1)}</td>
                        </tr>
                        <tr>
                            <td>Taxa de Erro</td>
                            <td>${(comparison.model1_error_rate || 0).toFixed(1)}%</td>
                            <td>${(comparison.model2_error_rate || 0).toFixed(1)}%</td>
                        </tr>
                        <tr>
                            <td>Tempo Médio por Lance</td>
                            <td>${(comparison.model1_avg_time || 0).toFixed(1)}s</td>
                            <td>${(comparison.model2_avg_time || 0).toFixed(1)}s</td>
                        </tr>
                    </tbody>
                </table>
            `;
        }
        
        // Performance over time chart
        if (comparison.performance_over_time && comparison.performance_over_time.length > 0) {
            this.createPerformanceChart(comparison.performance_over_time);
        }
    }
    
    createPerformanceChart(performanceData) {
        const chartContainer = document.getElementById('performance-chart');
        if (!chartContainer) return;
        
        chartContainer.innerHTML = '<canvas id="performance-chart-canvas"></canvas>';
        
        // Group data by model
        const model1Data = performanceData.filter(d => d.model === performanceData[0].model);
        const model2Data = performanceData.filter(d => d.model !== performanceData[0].model);
        
        const config = {
            type: 'line',
            data: {
                labels: model1Data.map(d => d.game_number),
                datasets: [
                    {
                        label: model1Data[0]?.model || 'Modelo 1',
                        data: model1Data.map(d => d.accuracy),
                        borderColor: 'rgb(102, 126, 234)',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        tension: 0.1
                    },
                    {
                        label: model2Data[0]?.model || 'Modelo 2',
                        data: model2Data.map(d => d.accuracy),
                        borderColor: 'rgb(220, 53, 69)',
                        backgroundColor: 'rgba(220, 53, 69, 0.1)',
                        tension: 0.1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Evolução da Precisão ao Longo do Tempo'
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Número da Partida'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Precisão (%)'
                        }
                    }
                }
            }
        };
        
        app.createChart('performance-chart-canvas', config);
    }
    
    async testLichessConnection() {
        const token = document.getElementById('lichess-token').value;
        
        if (!token) {
            Utils.showToast('Insira o token do Lichess', 'warning');
            return;
        }
        
        try {
            Utils.showLoading('Testando conexão...');
            
            const result = await api.testLichessConnection(token);
            
            Utils.hideLoading();
            
            if (result.success) {
                Utils.showToast('✅ Conectado ao Lichess com sucesso!', 'success');
            } else {
                Utils.showToast('❌ Erro na conexão: ' + (result.error || 'Token inválido'), 'error');
            }
            
        } catch (error) {
            Utils.hideLoading();
            Utils.handleError(error, 'testLichessConnection');
        }
    }
    
    async importLichessGames() {
        const token = document.getElementById('lichess-token').value;
        const username = document.getElementById('lichess-username').value;
        const maxGames = parseInt(document.getElementById('max-import-games').value);
        
        if (!token || !username) {
            Utils.showToast('Preencha o token e nome de usuário', 'warning');
            return;
        }
        
        try {
            Utils.showLoading('Importando partidas do Lichess...');
            
            const result = await api.importLichessGames(username, maxGames, token);
            
            Utils.hideLoading();
            
            if (result.success) {
                Utils.showToast(`✅ ${result.imported} partidas importadas com sucesso!`, 'success');
                
                // Update import status
                const statusContainer = document.getElementById('import-status');
                if (statusContainer) {
                    statusContainer.innerHTML = `
                        <div class="import-success">
                            <h4>✅ Importação Concluída</h4>
                            <p>Partidas importadas: ${result.imported}</p>
                            <p>Dados de treinamento gerados: ${result.trainingData || 0} posições</p>
                        </div>
                    `;
                }
            } else {
                Utils.showToast('❌ Erro na importação: ' + (result.error || 'Erro desconhecido'), 'error');
            }
            
        } catch (error) {
            Utils.hideLoading();
            Utils.handleError(error, 'importLichessGames');
        }
    }
    
    async applyRAGImprovements() {
        try {
            Utils.showLoading('Aplicando melhoramentos RAG...');
            
            const result = await api.applyRAGImprovements();
            
            Utils.hideLoading();
            
            if (result.success) {
                Utils.showToast('✅ Melhoramentos RAG aplicados com sucesso!', 'success');
                
                // Display improvements
                const improvementsContainer = document.getElementById('rag-improvements');
                if (improvementsContainer && result.improvements) {
                    improvementsContainer.innerHTML = `
                        <div class="rag-improvements">
                            <h4>🧠 Melhoramentos Aplicados</h4>
                            ${Object.entries(result.improvements).map(([model, improvement]) => `
                                <div class="improvement-item">
                                    <h5>${model}</h5>
                                    <p>Ganho de Precisão: +${improvement.accuracy_gain?.toFixed(1) || 0}%</p>
                                    <p>Ganho de Performance: +${improvement.performance_gain?.toFixed(1) || 0}%</p>
                                </div>
                            `).join('')}
                        </div>
                    `;
                }
            } else {
                Utils.showToast('⚠️ Nenhum melhoramento significativo detectado', 'warning');
            }
            
        } catch (error) {
            Utils.hideLoading();
            Utils.handleError(error, 'applyRAGImprovements');
        }
    }
    
    destroy() {
        if (this.analysisBoard) {
            this.analysisBoard.destroy();
        }
    }
}

// Make Analysis available globally
window.Analysis = Analysis;