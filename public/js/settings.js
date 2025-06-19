class Settings {
    constructor() {
        this.currentSettings = {};
    }
    
    init() {
        this.loadSettings();
        this.setupEventListeners();
        this.loadDatabaseStats();
    }
    
    setupEventListeners() {
        // API Keys
        const saveKeysBtn = document.getElementById('save-api-keys');
        if (saveKeysBtn) {
            saveKeysBtn.addEventListener('click', () => this.saveAPIKeys());
        }
        
        // Model testing
        const testModelBtn = document.getElementById('test-model');
        if (testModelBtn) {
            testModelBtn.addEventListener('click', () => this.testSelectedModel());
        }
        
        // Lichess connection
        const connectLichessBtn = document.getElementById('connect-lichess');
        if (connectLichessBtn) {
            connectLichessBtn.addEventListener('click', () => this.connectToLichess());
        }
        
        // Stockfish testing
        const testStockfishBtn = document.getElementById('test-stockfish');
        if (testStockfishBtn) {
            testStockfishBtn.addEventListener('click', () => this.testStockfish());
        }
        
        // Data management
        const exportDataBtn = document.getElementById('export-data');
        if (exportDataBtn) {
            exportDataBtn.addEventListener('click', () => this.exportData());
        }
        
        const importDataBtn = document.getElementById('import-data');
        if (importDataBtn) {
            importDataBtn.addEventListener('click', () => this.importData());
        }
        
        const clearOldGamesBtn = document.getElementById('clear-old-games');
        if (clearOldGamesBtn) {
            clearOldGamesBtn.addEventListener('click', () => this.clearOldGames());
        }
        
        const resetDatabaseBtn = document.getElementById('reset-database');
        if (resetDatabaseBtn) {
            resetDatabaseBtn.addEventListener('click', () => this.resetDatabase());
        }
        
        // Range sliders
        this.setupRangeSliders();
    }
    
    setupRangeSliders() {
        const sliders = [
            'temperature', 'max-tokens', 'thinking-time',
            'stockfish-depth', 'analysis-depth'
        ];
        
        sliders.forEach(sliderId => {
            const slider = document.getElementById(sliderId);
            if (slider) {
                slider.addEventListener('input', (e) => {
                    const valueSpan = document.getElementById(sliderId + '-value');
                    if (valueSpan) {
                        valueSpan.textContent = e.target.value;
                    }
                });
            }
        });
    }
    
    async loadSettings() {
        try {
            const settings = await api.getSettings();
            this.currentSettings = settings;
            this.populateSettingsForm(settings);
            
            // Load available models for testing
            const models = await api.getAvailableModels();
            this.updateTestModelSelector(models);
            
        } catch (error) {
            Utils.handleError(error, 'loadSettings');
        }
    }
    
    populateSettingsForm(settings) {
        // Model parameters
        if (settings.modelParams) {
            const temperature = document.getElementById('temperature');
            if (temperature) {
                temperature.value = settings.modelParams.temperature || 0.1;
                document.getElementById('temperature-value').textContent = temperature.value;
            }
            
            const maxTokens = document.getElementById('max-tokens');
            if (maxTokens) {
                maxTokens.value = settings.modelParams.maxTokens || 1000;
                document.getElementById('max-tokens-value').textContent = maxTokens.value;
            }
            
            const thinkingTime = document.getElementById('thinking-time');
            if (thinkingTime) {
                thinkingTime.value = settings.modelParams.thinkingTime || 5;
                document.getElementById('thinking-time-value').textContent = thinkingTime.value;
            }
        }
        
        // Game settings
        if (settings.gameSettings) {
            const defaultTimeControl = document.getElementById('default-time-control');
            if (defaultTimeControl) {
                defaultTimeControl.value = settings.gameSettings.defaultTimeControl || '10';
            }
            
            const autoSaveGames = document.getElementById('auto-save-games');
            if (autoSaveGames) {
                autoSaveGames.checked = settings.gameSettings.autoSaveGames !== false;
            }
            
            const showCoordinates = document.getElementById('show-coordinates');
            if (showCoordinates) {
                showCoordinates.checked = settings.gameSettings.showCoordinates !== false;
            }
            
            const highlightLastMove = document.getElementById('highlight-last-move');
            if (highlightLastMove) {
                highlightLastMove.checked = settings.gameSettings.highlightLastMove !== false;
            }
            
            const autoAnalysis = document.getElementById('auto-analysis');
            if (autoAnalysis) {
                autoAnalysis.checked = settings.gameSettings.autoAnalysis === true;
            }
            
            const analysisDepth = document.getElementById('analysis-depth');
            if (analysisDepth) {
                analysisDepth.value = settings.gameSettings.analysisDepth || 12;
                document.getElementById('analysis-depth-value').textContent = analysisDepth.value;
            }
            
            const saveAnalysis = document.getElementById('save-analysis');
            if (saveAnalysis) {
                saveAnalysis.checked = settings.gameSettings.saveAnalysis !== false;
            }
        }
        
        // Stockfish settings
        if (settings.stockfish) {
            const stockfishPath = document.getElementById('stockfish-path');
            if (stockfishPath) {
                stockfishPath.value = settings.stockfish.path || '/usr/local/bin/stockfish';
            }
            
            const stockfishDepth = document.getElementById('stockfish-depth');
            if (stockfishDepth) {
                stockfishDepth.value = settings.stockfish.depth || 15;
                document.getElementById('stockfish-depth-value').textContent = stockfishDepth.value;
            }
        }
    }
    
    updateTestModelSelector(models) {
        const testModelSelect = document.getElementById('test-model-select');
        if (testModelSelect) {
            testModelSelect.innerHTML = '<option value="">Selecione um modelo...</option>';
            Object.entries(models).forEach(([name, available]) => {
                const option = document.createElement('option');
                option.value = name;
                option.textContent = `${available ? '🟢' : '🔴'} ${name}`;
                option.disabled = !available;
                testModelSelect.appendChild(option);
            });
        }
    }
    
    async saveAPIKeys() {
        const keys = {
            openai: document.getElementById('openai-key').value,
            google: document.getElementById('google-key').value,
            deepseek: document.getElementById('deepseek-key').value,
            groq: document.getElementById('groq-key').value
        };
        
        // Check if at least one key is provided
        const hasKeys = Object.values(keys).some(key => key.trim() !== '');
        if (!hasKeys) {
            Utils.showToast('Forneça pelo menos uma chave de API', 'warning');
            return;
        }
        
        try {
            Utils.showLoading('Salvando chaves de API...');
            
            const result = await api.saveAPIKeys(keys);
            
            Utils.hideLoading();
            
            if (result.success) {
                Utils.showToast('✅ Chaves de API salvas com sucesso!', 'success');
                Utils.showToast('🔄 Reinicie a aplicação para aplicar as mudanças', 'info', 8000);
            } else {
                Utils.showToast('❌ Erro ao salvar chaves: ' + (result.error || 'Erro desconhecido'), 'error');
            }
            
        } catch (error) {
            Utils.hideLoading();
            Utils.handleError(error, 'saveAPIKeys');
        }
    }
    
    async testSelectedModel() {
        const modelSelect = document.getElementById('test-model-select');
        if (!modelSelect || !modelSelect.value) {
            Utils.showToast('Selecione um modelo para testar', 'warning');
            return;
        }
        
        const modelName = modelSelect.value;
        
        try {
            Utils.showLoading('Testando modelo...');
            
            const result = await api.testModel(modelName);
            
            Utils.hideLoading();
            
            const testResults = document.getElementById('test-results');
            if (testResults) {
                if (result.success) {
                    testResults.innerHTML = `
                        <div class="test-success">
                            <h4>✅ Modelo ${modelName} funcionando corretamente!</h4>
                            <p>Tempo de resposta: ${result.response_time?.toFixed(2) || 0}s</p>
                            <p>Resposta: ${result.response || 'N/A'}</p>
                        </div>
                    `;
                    Utils.showToast('✅ Teste do modelo bem-sucedido!', 'success');
                } else {
                    testResults.innerHTML = `
                        <div class="test-error">
                            <h4>❌ Erro no modelo ${modelName}</h4>
                            <p>${result.error || 'Erro desconhecido'}</p>
                        </div>
                    `;
                    Utils.showToast('❌ Teste do modelo falhou', 'error');
                }
            }
            
        } catch (error) {
            Utils.hideLoading();
            Utils.handleError(error, 'testSelectedModel');
        }
    }
    
    async connectToLichess() {
        const token = document.getElementById('settings-lichess-token').value;
        
        if (!token) {
            Utils.showToast('Insira o token do Lichess', 'warning');
            return;
        }
        
        try {
            Utils.showLoading('Conectando ao Lichess...');
            
            const result = await api.testLichessConnection(token);
            
            Utils.hideLoading();
            
            if (result.success) {
                Utils.showToast('✅ Conectado ao Lichess com sucesso!', 'success');
            } else {
                Utils.showToast('❌ Erro na conexão: ' + (result.error || 'Token inválido'), 'error');
            }
            
        } catch (error) {
            Utils.hideLoading();
            Utils.handleError(error, 'connectToLichess');
        }
    }
    
    async testStockfish() {
        const path = document.getElementById('stockfish-path').value;
        
        if (!path) {
            Utils.showToast('Insira o caminho do Stockfish', 'warning');
            return;
        }
        
        try {
            Utils.showLoading('Testando Stockfish...');
            
            const result = await api.testStockfish(path);
            
            Utils.hideLoading();
            
            if (result.success) {
                Utils.showToast(`✅ Stockfish funcionando! Versão: ${result.version || 'Desconhecida'}`, 'success');
            } else {
                Utils.showToast('❌ Erro no Stockfish: ' + (result.error || 'Caminho inválido'), 'error');
            }
            
        } catch (error) {
            Utils.hideLoading();
            Utils.handleError(error, 'testStockfish');
        }
    }
    
    async loadDatabaseStats() {
        try {
            const stats = await api.getDatabaseStats();
            this.displayDatabaseStats(stats);
        } catch (error) {
            Utils.handleError(error, 'loadDatabaseStats');
        }
    }
    
    displayDatabaseStats(stats) {
        const statsContainer = document.getElementById('db-stats');
        if (statsContainer) {
            statsContainer.innerHTML = `
                <div class="metric-card">
                    <div class="metric-icon">🎮</div>
                    <div class="metric-content">
                        <h3>${stats.total_games || 0}</h3>
                        <p>Total de Partidas</p>
                    </div>
                </div>
                <div class="metric-card">
                    <div class="metric-icon">🤖</div>
                    <div class="metric-content">
                        <h3>${stats.unique_models || 0}</h3>
                        <p>Modelos Únicos</p>
                    </div>
                </div>
                <div class="metric-card">
                    <div class="metric-icon">💾</div>
                    <div class="metric-content">
                        <h3>${(stats.db_size_mb || 0).toFixed(1)} MB</h3>
                        <p>Tamanho do BD</p>
                    </div>
                </div>
            `;
        }
    }
    
    async exportData() {
        try {
            Utils.showLoading('Exportando dados...');
            
            const data = await api.exportData();
            
            Utils.hideLoading();
            
            // Create and download file
            const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
            const filename = `llm_chess_data_${timestamp}.json`;
            
            Utils.downloadFile(JSON.stringify(data, null, 2), filename, 'application/json');
            Utils.showToast('✅ Dados exportados com sucesso!', 'success');
            
        } catch (error) {
            Utils.hideLoading();
            Utils.handleError(error, 'exportData');
        }
    }
    
    async importData() {
        const fileInput = document.getElementById('import-file');
        if (!fileInput || !fileInput.files.length) {
            Utils.showToast('Selecione um arquivo para importar', 'warning');
            return;
        }
        
        const file = fileInput.files[0];
        
        try {
            Utils.showLoading('Importando dados...');
            
            const fileContent = await Utils.readFile(file);
            const data = JSON.parse(fileContent);
            
            const result = await api.importData(data);
            
            Utils.hideLoading();
            
            if (result.success) {
                Utils.showToast('✅ Dados importados com sucesso!', 'success');
                this.loadDatabaseStats(); // Refresh stats
            } else {
                Utils.showToast('❌ Erro na importação: ' + (result.error || 'Erro desconhecido'), 'error');
            }
            
        } catch (error) {
            Utils.hideLoading();
            
            if (error instanceof SyntaxError) {
                Utils.showToast('❌ Arquivo JSON inválido', 'error');
            } else {
                Utils.handleError(error, 'importData');
            }
        }
    }
    
    async clearOldGames() {
        const confirmed = document.getElementById('confirm-clear-old');
        if (!confirmed || !confirmed.checked) {
            Utils.showToast('Confirme a operação marcando a caixa de seleção', 'warning');
            return;
        }
        
        if (!confirm('Tem certeza que deseja deletar partidas antigas (>30 dias)? Esta operação é irreversível!')) {
            return;
        }
        
        try {
            Utils.showLoading('Removendo partidas antigas...');
            
            const result = await api.clearOldGames(30);
            
            Utils.hideLoading();
            
            if (result.success) {
                Utils.showToast(`✅ ${result.deleted || 0} partidas antigas removidas`, 'success');
                this.loadDatabaseStats(); // Refresh stats
            } else {
                Utils.showToast('❌ Erro ao remover partidas: ' + (result.error || 'Erro desconhecido'), 'error');
            }
            
        } catch (error) {
            Utils.hideLoading();
            Utils.handleError(error, 'clearOldGames');
        }
    }
    
    async resetDatabase() {
        const confirmInput = document.querySelector('input[placeholder="Digite \'CONFIRMAR\' para prosseguir:"]');
        if (!confirmInput || confirmInput.value !== 'CONFIRMAR') {
            Utils.showToast('Digite "CONFIRMAR" para prosseguir com o reset', 'warning');
            return;
        }
        
        if (!confirm('ATENÇÃO: Esta operação irá deletar TODOS os dados permanentemente! Tem certeza absoluta?')) {
            return;
        }
        
        try {
            Utils.showLoading('Resetando banco de dados...');
            
            const result = await api.resetDatabase();
            
            Utils.hideLoading();
            
            if (result.success) {
                Utils.showToast('✅ Banco de dados resetado com sucesso!', 'success');
                Utils.showToast('🔄 Reinicie a aplicação', 'info', 8000);
                this.loadDatabaseStats(); // Refresh stats
            } else {
                Utils.showToast('❌ Erro ao resetar: ' + (result.error || 'Erro desconhecido'), 'error');
            }
            
        } catch (error) {
            Utils.hideLoading();
            Utils.handleError(error, 'resetDatabase');
        }
    }
    
    async saveSettings() {
        const settings = {
            modelParams: {
                temperature: parseFloat(document.getElementById('temperature').value),
                maxTokens: parseInt(document.getElementById('max-tokens').value),
                thinkingTime: parseInt(document.getElementById('thinking-time').value)
            },
            gameSettings: {
                defaultTimeControl: document.getElementById('default-time-control').value,
                autoSaveGames: document.getElementById('auto-save-games').checked,
                showCoordinates: document.getElementById('show-coordinates').checked,
                highlightLastMove: document.getElementById('highlight-last-move').checked,
                autoAnalysis: document.getElementById('auto-analysis').checked,
                analysisDepth: parseInt(document.getElementById('analysis-depth').value),
                saveAnalysis: document.getElementById('save-analysis').checked
            },
            stockfish: {
                path: document.getElementById('stockfish-path').value,
                depth: parseInt(document.getElementById('stockfish-depth').value)
            }
        };
        
        try {
            Utils.showLoading('Salvando configurações...');
            
            const result = await api.updateSettings(settings);
            
            Utils.hideLoading();
            
            if (result.success) {
                this.currentSettings = settings;
                Utils.showToast('✅ Configurações salvas com sucesso!', 'success');
            } else {
                Utils.showToast('❌ Erro ao salvar: ' + (result.error || 'Erro desconhecido'), 'error');
            }
            
        } catch (error) {
            Utils.hideLoading();
            Utils.handleError(error, 'saveSettings');
        }
    }
    
    destroy() {
        // Cleanup if needed
    }
}

// Make Settings available globally
window.Settings = Settings;