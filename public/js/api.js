class API {
    constructor() {
        this.baseURL = '/api';
    }
    
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };
        
        if (config.body && typeof config.body === 'object') {
            config.body = JSON.stringify(config.body);
        }
        
        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            } else {
                return await response.text();
            }
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }
    
    // Games API
    async getGames() {
        return this.request('/games');
    }
    
    async getGame(id) {
        return this.request(`/games/${id}`);
    }
    
    async createGame(gameData) {
        return this.request('/games', {
            method: 'POST',
            body: gameData
        });
    }
    
    async updateGame(id, gameData) {
        return this.request(`/games/${id}`, {
            method: 'PUT',
            body: gameData
        });
    }
    
    async deleteGame(id) {
        return this.request(`/games/${id}`, {
            method: 'DELETE'
        });
    }
    
    async getRecentGames(limit = 10) {
        return this.request(`/games/recent?limit=${limit}`);
    }
    
    async getGamesBetweenModels(model1, model2) {
        return this.request(`/games/between?model1=${encodeURIComponent(model1)}&model2=${encodeURIComponent(model2)}`);
    }
    
    // Models API
    async getModels() {
        return this.request('/models');
    }
    
    async getAvailableModels() {
        return this.request('/models/available');
    }
    
    async testModel(modelName) {
        return this.request('/models/test', {
            method: 'POST',
            body: { modelName }
        });
    }
    
    async getModelStats(modelName) {
        return this.request(`/models/${encodeURIComponent(modelName)}/stats`);
    }
    
    async updateModelConfig(modelName, config) {
        return this.request(`/models/${encodeURIComponent(modelName)}/config`, {
            method: 'PUT',
            body: config
        });
    }
    
    // Battle API
    async startBattle(battleConfig) {
        return this.request('/games/battle', {
            method: 'POST',
            body: battleConfig
        });
    }
    
    async startTournament(tournamentConfig) {
        return this.request('/games/tournament', {
            method: 'POST',
            body: tournamentConfig
        });
    }
    
    async getBattleStatus(battleId) {
        return this.request(`/games/battle/${battleId}/status`);
    }
    
    async getTournamentStatus(tournamentId) {
        return this.request(`/games/tournament/${tournamentId}/status`);
    }
    
    // Human vs AI API
    async startHumanGame(gameConfig) {
        return this.request('/games/human', {
            method: 'POST',
            body: gameConfig
        });
    }
    
    async makeHumanMove(gameId, move) {
        return this.request(`/games/human/${gameId}/move`, {
            method: 'POST',
            body: { move }
        });
    }
    
    async getAIMove(gameId) {
        return this.request(`/games/human/${gameId}/ai-move`, {
            method: 'POST'
        });
    }
    
    async getHint(gameId) {
        return this.request(`/games/human/${gameId}/hint`);
    }
    
    // Analysis API
    async analyzeGame(gameId) {
        return this.request(`/analysis/game/${gameId}`);
    }
    
    async compareModels(model1, model2) {
        return this.request('/analysis/compare', {
            method: 'POST',
            body: { model1, model2 }
        });
    }
    
    async getEloRatings() {
        return this.request('/analysis/elo');
    }
    
    async getDetailedStats(modelName) {
        return this.request(`/analysis/stats/${encodeURIComponent(modelName)}`);
    }
    
    async getOpeningStats() {
        return this.request('/analysis/openings');
    }
    
    async getGlobalStats() {
        return this.request('/analysis/global');
    }
    
    // Lichess API
    async testLichessConnection(token) {
        return this.request('/lichess/test', {
            method: 'POST',
            body: { token }
        });
    }
    
    async importLichessGames(username, maxGames, token) {
        return this.request('/lichess/import', {
            method: 'POST',
            body: { username, maxGames, token }
        });
    }
    
    async applyRAGImprovements() {
        return this.request('/lichess/rag', {
            method: 'POST'
        });
    }
    
    async getLichessUserInfo(username, token) {
        return this.request(`/lichess/user/${username}`, {
            method: 'POST',
            body: { token }
        });
    }
    
    // Settings API
    async saveAPIKeys(keys) {
        return this.request('/settings/api-keys', {
            method: 'POST',
            body: keys
        });
    }
    
    async getSettings() {
        return this.request('/settings');
    }
    
    async updateSettings(settings) {
        return this.request('/settings', {
            method: 'PUT',
            body: settings
        });
    }
    
    async testStockfish(path) {
        return this.request('/settings/test-stockfish', {
            method: 'POST',
            body: { path }
        });
    }
    
    // Data Management API
    async exportData() {
        return this.request('/data/export');
    }
    
    async importData(data) {
        return this.request('/data/import', {
            method: 'POST',
            body: data
        });
    }
    
    async getDatabaseStats() {
        return this.request('/data/stats');
    }
    
    async clearOldGames(days) {
        return this.request('/data/clear-old', {
            method: 'POST',
            body: { days }
        });
    }
    
    async resetDatabase() {
        return this.request('/data/reset', {
            method: 'POST'
        });
    }
}

// Create global API instance
window.api = new API();