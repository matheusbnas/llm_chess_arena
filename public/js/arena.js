class Arena {
    constructor() {
        this.currentBattle = null;
        this.currentTournament = null;
        this.battleBoard = null;
        this.battleUpdateInterval = null;
    }
    
    init() {
        this.setupEventListeners();
        this.initializeBoard();
        this.loadAvailableModels();
    }
    
    setupEventListeners() {
        // Tournament mode toggle
        const tournamentMode = document.getElementById('tournament-mode');
        if (tournamentMode) {
            tournamentMode.addEventListener('change', (e) => {
                this.toggleTournamentMode(e.target.checked);
            });
        }
        
        // Range sliders
        const numGames = document.getElementById('num-games');
        if (numGames) {
            numGames.addEventListener('input', (e) => {
                document.getElementById('num-games-value').textContent = e.target.value;
            });
        }
        
        const gamesPerPair = document.getElementById('games-per-pair');
        if (gamesPerPair) {
            gamesPerPair.addEventListener('input', (e) => {
                document.getElementById('games-per-pair-value').textContent = e.target.value;
            });
        }
        
        // Battle buttons
        const startBattle = document.getElementById('start-battle');
        if (startBattle) {
            startBattle.addEventListener('click', () => this.startIndividualBattle());
        }
        
        const startTournament = document.getElementById('start-tournament');
        if (startTournament) {
            startTournament.addEventListener('click', () => this.startTournament());
        }
    }
    
    initializeBoard() {
        const boardContainer = document.getElementById('arena-chessboard');
        if (boardContainer) {
            this.battleBoard = new ChessBoard('arena-chessboard', {
                draggable: false,
                showCoordinates: true
            });
        }
    }
    
    async loadAvailableModels() {
        try {
            const models = await api.getAvailableModels();
            this.updateModelSelectors(models);
        } catch (error) {
            Utils.handleError(error, 'loadAvailableModels');
        }
    }
    
    updateModelSelectors(models) {
        const whiteSelect = document.getElementById('white-model');
        const blackSelect = document.getElementById('black-model');
        const tournamentModels = document.getElementById('tournament-models');
        
        if (whiteSelect) {
            whiteSelect.innerHTML = '';
            Object.entries(models).forEach(([name, available]) => {
                const option = document.createElement('option');
                option.value = name;
                option.textContent = `${available ? '🟢' : '🔴'} ${name}`;
                option.disabled = !available;
                whiteSelect.appendChild(option);
            });
        }
        
        if (blackSelect) {
            blackSelect.innerHTML = '';
            Object.entries(models).forEach(([name, available]) => {
                const option = document.createElement('option');
                option.value = name;
                option.textContent = `${available ? '🟢' : '🔴'} ${name}`;
                option.disabled = !available;
                blackSelect.appendChild(option);
            });
        }
        
        if (tournamentModels) {
            tournamentModels.innerHTML = '';
            Object.entries(models).forEach(([name, available]) => {
                if (available) {
                    const label = document.createElement('label');
                    label.innerHTML = `
                        <input type="checkbox" value="${name}"> ${name}
                    `;
                    tournamentModels.appendChild(label);
                }
            });
        }
    }
    
    toggleTournamentMode(enabled) {
        const individualBattle = document.getElementById('individual-battle');
        const tournamentConfig = document.getElementById('tournament-config');
        
        if (individualBattle && tournamentConfig) {
            if (enabled) {
                individualBattle.style.display = 'none';
                tournamentConfig.style.display = 'block';
            } else {
                individualBattle.style.display = 'block';
                tournamentConfig.style.display = 'none';
            }
        }
    }
    
    async startIndividualBattle() {
        const whiteModel = document.getElementById('white-model').value;
        const blackModel = document.getElementById('black-model').value;
        const opening = document.getElementById('opening').value;
        const numGames = parseInt(document.getElementById('num-games').value);
        
        if (!whiteModel || !blackModel) {
            Utils.showToast('Selecione ambos os modelos', 'warning');
            return;
        }
        
        if (whiteModel === blackModel) {
            Utils.showToast('Selecione modelos diferentes', 'warning');
            return;
        }
        
        try {
            Utils.showLoading('Iniciando batalha...');
            
            const battleConfig = {
                whiteModel,
                blackModel,
                opening,
                numGames
            };
            
            const battle = await api.startBattle(battleConfig);
            this.currentBattle = battle;
            
            this.updateBattleStatus(battle);
            this.startBattleMonitoring();
            
            Utils.hideLoading();
            Utils.showToast('Batalha iniciada com sucesso!', 'success');
            
        } catch (error) {
            Utils.hideLoading();
            Utils.handleError(error, 'startIndividualBattle');
        }
    }
    
    async startTournament() {
        const selectedModels = Array.from(document.querySelectorAll('#tournament-models input:checked'))
            .map(input => input.value);
        const gamesPerPair = parseInt(document.getElementById('games-per-pair').value);
        
        if (selectedModels.length < 2) {
            Utils.showToast('Selecione pelo menos 2 modelos', 'warning');
            return;
        }
        
        try {
            Utils.showLoading('Iniciando torneio...');
            
            const tournamentConfig = {
                models: selectedModels,
                gamesPerPair
            };
            
            const tournament = await api.startTournament(tournamentConfig);
            this.currentTournament = tournament;
            
            this.updateTournamentStatus(tournament);
            this.startTournamentMonitoring();
            
            Utils.hideLoading();
            Utils.showToast('Torneio iniciado com sucesso!', 'success');
            
        } catch (error) {
            Utils.hideLoading();
            Utils.handleError(error, 'startTournament');
        }
    }
    
    updateBattleStatus(battle) {
        const battleInfo = document.getElementById('battle-info');
        if (!battleInfo) return;
        
        battleInfo.innerHTML = `
            <div class="battle-header">
                <h4>⚔️ ${battle.whiteModel} vs ${battle.blackModel}</h4>
                <p>Partida ${battle.currentGame}/${battle.totalGames}</p>
            </div>
            <div class="battle-progress">
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${(battle.currentGame / battle.totalGames) * 100}%"></div>
                </div>
            </div>
            <div class="battle-stats">
                <div class="stat">
                    <span class="label">Vitórias ${battle.whiteModel}:</span>
                    <span class="value">${battle.whiteWins || 0}</span>
                </div>
                <div class="stat">
                    <span class="label">Empates:</span>
                    <span class="value">${battle.draws || 0}</span>
                </div>
                <div class="stat">
                    <span class="label">Vitórias ${battle.blackModel}:</span>
                    <span class="value">${battle.blackWins || 0}</span>
                </div>
            </div>
        `;
        
        // Update board if current game is available
        if (battle.currentBoard && this.battleBoard) {
            this.battleBoard.setPosition(battle.currentBoard);
        }
        
        // Update progress bar
        const progressFill = document.getElementById('battle-progress-fill');
        if (progressFill) {
            progressFill.style.width = `${(battle.currentGame / battle.totalGames) * 100}%`;
        }
        
        // Update results table
        this.updateBattleResults(battle.results || []);
    }
    
    updateTournamentStatus(tournament) {
        const battleInfo = document.getElementById('battle-info');
        if (!battleInfo) return;
        
        battleInfo.innerHTML = `
            <div class="tournament-header">
                <h4>🏆 Torneio em Andamento</h4>
                <p>${tournament.participants.length} participantes</p>
            </div>
            <div class="tournament-progress">
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${(tournament.completedGames / tournament.totalGames) * 100}%"></div>
                </div>
                <p>Partidas: ${tournament.completedGames}/${tournament.totalGames}</p>
            </div>
            <div class="tournament-standings">
                <h5>Classificação Atual:</h5>
                ${this.renderTournamentStandings(tournament.standings || [])}
            </div>
        `;
    }
    
    renderTournamentStandings(standings) {
        if (!standings.length) return '<p>Aguardando resultados...</p>';
        
        return `
            <table class="standings-table">
                <thead>
                    <tr>
                        <th>Pos</th>
                        <th>Modelo</th>
                        <th>Pontos</th>
                        <th>Partidas</th>
                    </tr>
                </thead>
                <tbody>
                    ${standings.map((standing, index) => `
                        <tr>
                            <td>${index + 1}</td>
                            <td>${standing.model}</td>
                            <td>${standing.points}</td>
                            <td>${standing.games}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    }
    
    updateBattleResults(results) {
        const resultsContainer = document.getElementById('battle-results');
        if (!resultsContainer) return;
        
        if (!results.length) {
            resultsContainer.innerHTML = '<p>Nenhum resultado ainda...</p>';
            return;
        }
        
        resultsContainer.innerHTML = `
            <h5>Resultados:</h5>
            <table class="results-table">
                <thead>
                    <tr>
                        <th>Partida</th>
                        <th>Brancas</th>
                        <th>Pretas</th>
                        <th>Resultado</th>
                        <th>Lances</th>
                    </tr>
                </thead>
                <tbody>
                    ${results.map((result, index) => `
                        <tr>
                            <td>${index + 1}</td>
                            <td>${result.white}</td>
                            <td>${result.black}</td>
                            <td>
                                <span class="result-badge" style="background-color: ${Utils.getResultColor(result.result)}">
                                    ${Utils.getResultText(result.result)}
                                </span>
                            </td>
                            <td>${result.moves || 0}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    }
    
    startBattleMonitoring() {
        if (this.battleUpdateInterval) {
            clearInterval(this.battleUpdateInterval);
        }
        
        this.battleUpdateInterval = setInterval(async () => {
            if (!this.currentBattle) return;
            
            try {
                const status = await api.getBattleStatus(this.currentBattle.id);
                this.updateBattleStatus(status);
                
                if (status.completed) {
                    this.stopBattleMonitoring();
                    Utils.showToast('Batalha concluída!', 'success');
                }
            } catch (error) {
                console.error('Error updating battle status:', error);
            }
        }, 2000);
    }
    
    startTournamentMonitoring() {
        if (this.battleUpdateInterval) {
            clearInterval(this.battleUpdateInterval);
        }
        
        this.battleUpdateInterval = setInterval(async () => {
            if (!this.currentTournament) return;
            
            try {
                const status = await api.getTournamentStatus(this.currentTournament.id);
                this.updateTournamentStatus(status);
                
                if (status.completed) {
                    this.stopBattleMonitoring();
                    Utils.showToast('Torneio concluído!', 'success');
                }
            } catch (error) {
                console.error('Error updating tournament status:', error);
            }
        }, 3000);
    }
    
    stopBattleMonitoring() {
        if (this.battleUpdateInterval) {
            clearInterval(this.battleUpdateInterval);
            this.battleUpdateInterval = null;
        }
    }
    
    handleGameUpdate(data) {
        if (this.currentBattle && data.battleId === this.currentBattle.id) {
            this.updateBattleStatus(data);
        }
    }
    
    handleBattleUpdate(data) {
        if (this.currentBattle && data.id === this.currentBattle.id) {
            this.currentBattle = data;
            this.updateBattleStatus(data);
        }
    }
    
    handleTournamentUpdate(data) {
        if (this.currentTournament && data.id === this.currentTournament.id) {
            this.currentTournament = data;
            this.updateTournamentStatus(data);
        }
    }
    
    destroy() {
        this.stopBattleMonitoring();
        
        if (this.battleBoard) {
            this.battleBoard.destroy();
        }
    }
}

// Make Arena available globally
window.Arena = Arena;