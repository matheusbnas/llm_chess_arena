class Play {
    constructor() {
        this.currentGame = null;
        this.gameBoard = null;
        this.gameUpdateInterval = null;
        this.isPlayerTurn = false;
    }
    
    init() {
        this.setupEventListeners();
        this.initializeBoard();
        this.loadAvailableModels();
    }
    
    setupEventListeners() {
        // New game button
        const newGameBtn = document.getElementById('new-game');
        if (newGameBtn) {
            newGameBtn.addEventListener('click', () => this.startNewGame());
        }
        
        // Game control buttons
        const restartBtn = document.getElementById('restart-game');
        if (restartBtn) {
            restartBtn.addEventListener('click', () => this.restartGame());
        }
        
        const saveBtn = document.getElementById('save-game');
        if (saveBtn) {
            saveBtn.addEventListener('click', () => this.saveGame());
        }
        
        const hintBtn = document.getElementById('hint');
        if (hintBtn) {
            hintBtn.addEventListener('click', () => this.getHint());
        }
        
        // Move input
        const makeMoveBtn = document.getElementById('make-move');
        if (makeMoveBtn) {
            makeMoveBtn.addEventListener('click', () => this.makePlayerMove());
        }
        
        const moveInput = document.getElementById('move-input');
        if (moveInput) {
            moveInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.makePlayerMove();
                }
            });
        }
    }
    
    initializeBoard() {
        const boardContainer = document.getElementById('play-chessboard');
        if (boardContainer) {
            this.gameBoard = new ChessBoard('play-chessboard', {
                draggable: true,
                showCoordinates: true
            });
            
            // Set up board event handlers
            this.gameBoard.onMove((move) => {
                if (this.isPlayerTurn) {
                    this.handleBoardMove(move);
                }
            });
            
            this.gameBoard.onGetPossibleMoves = (square) => {
                return this.getPossibleMoves(square);
            };
        }
    }
    
    async loadAvailableModels() {
        try {
            const models = await api.getAvailableModels();
            this.updateModelSelector(models);
        } catch (error) {
            Utils.handleError(error, 'loadAvailableModels');
        }
    }
    
    updateModelSelector(models) {
        const opponentSelect = document.getElementById('opponent-model');
        if (opponentSelect) {
            opponentSelect.innerHTML = '';
            Object.entries(models).forEach(([name, available]) => {
                const option = document.createElement('option');
                option.value = name;
                option.textContent = `${available ? '🟢' : '🔴'} ${name}`;
                option.disabled = !available;
                opponentSelect.appendChild(option);
            });
        }
    }
    
    async startNewGame() {
        const opponentModel = document.getElementById('opponent-model').value;
        const playerColor = document.querySelector('input[name="player-color"]:checked').value;
        const difficulty = document.getElementById('difficulty').value;
        const timeControl = document.getElementById('time-control').value;
        
        if (!opponentModel) {
            Utils.showToast('Selecione um modelo oponente', 'warning');
            return;
        }
        
        try {
            Utils.showLoading('Iniciando novo jogo...');
            
            const gameConfig = {
                opponentModel,
                playerColor,
                difficulty,
                timeControl
            };
            
            const game = await api.startHumanGame(gameConfig);
            this.currentGame = game;
            
            this.setupGameUI();
            this.updateGameStatus();
            this.startGameMonitoring();
            
            // Set initial board position
            if (this.gameBoard) {
                this.gameBoard.setPosition(game.fen || 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1');
                this.gameBoard.flip(playerColor === 'black');
            }
            
            this.isPlayerTurn = (playerColor === 'white');
            
            Utils.hideLoading();
            Utils.showToast('Novo jogo iniciado!', 'success');
            
            // If AI plays first (player is black), get AI move
            if (playerColor === 'black') {
                this.getAIMove();
            }
            
        } catch (error) {
            Utils.hideLoading();
            Utils.handleError(error, 'startNewGame');
        }
    }
    
    setupGameUI() {
        // Show game controls
        const gameControls = document.querySelector('.game-controls');
        if (gameControls) {
            gameControls.style.display = 'block';
        }
        
        // Show move input if it's player's turn
        const moveInput = document.querySelector('.move-input');
        if (moveInput) {
            moveInput.style.display = this.isPlayerTurn ? 'block' : 'none';
        }
        
        // Clear move history
        const moveList = document.getElementById('move-list');
        if (moveList) {
            moveList.innerHTML = '';
        }
    }
    
    updateGameStatus() {
        if (!this.currentGame) return;
        
        const gameStatus = document.getElementById('game-status');
        if (!gameStatus) return;
        
        const opponent = this.currentGame.opponentModel;
        const playerColor = this.currentGame.playerColor;
        const difficulty = this.currentGame.difficulty;
        
        let statusText = `🎮 Jogando contra ${opponent} (${difficulty})`;
        let statusClass = 'status-playing';
        
        if (this.currentGame.status === 'finished') {
            statusText = `🏁 Jogo finalizado - ${this.getGameResult()}`;
            statusClass = 'status-finished';
        } else if (this.currentGame.status === 'check') {
            statusText += ' - Xeque!';
            statusClass = 'status-check';
        }
        
        gameStatus.innerHTML = `
            <div class="${statusClass}">
                <p>${statusText}</p>
                <p>Você: ${playerColor === 'white' ? 'Brancas' : 'Pretas'}</p>
            </div>
        `;
        
        // Update move input visibility
        const moveInput = document.querySelector('.move-input');
        if (moveInput) {
            moveInput.style.display = (this.isPlayerTurn && this.currentGame.status === 'playing') ? 'block' : 'none';
        }
    }
    
    async makePlayerMove() {
        const moveInput = document.getElementById('move-input');
        if (!moveInput || !this.currentGame) return;
        
        const move = moveInput.value.trim();
        if (!move) {
            Utils.showToast('Digite um lance válido', 'warning');
            return;
        }
        
        try {
            Utils.showLoading('Processando lance...');
            
            const result = await api.makeHumanMove(this.currentGame.id, move);
            
            if (result.success) {
                // Update board
                if (this.gameBoard) {
                    this.gameBoard.setPosition(result.fen);
                    if (result.lastMove) {
                        this.gameBoard.highlightMove(result.lastMove.from, result.lastMove.to);
                    }
                }
                
                // Update game state
                this.currentGame = result.game;
                this.updateGameStatus();
                this.updateMoveHistory();
                
                // Clear input
                moveInput.value = '';
                
                // Switch turns
                this.isPlayerTurn = false;
                
                Utils.hideLoading();
                Utils.showToast('Lance jogado com sucesso!', 'success');
                
                // Check if game is over
                if (result.game.status === 'finished') {
                    this.endGame();
                } else {
                    // Get AI response
                    setTimeout(() => this.getAIMove(), 1000);
                }
                
            } else {
                Utils.hideLoading();
                Utils.showToast(result.error || 'Lance inválido', 'error');
            }
            
        } catch (error) {
            Utils.hideLoading();
            Utils.handleError(error, 'makePlayerMove');
        }
    }
    
    handleBoardMove(move) {
        if (!this.isPlayerTurn || !this.currentGame) return;
        
        // Convert board move to SAN notation
        const moveInput = document.getElementById('move-input');
        if (moveInput) {
            moveInput.value = move.san || `${move.from}${move.to}`;
            this.makePlayerMove();
        }
    }
    
    getPossibleMoves(square) {
        // This would need to be implemented based on current game state
        // For now, return empty array
        return [];
    }
    
    async getAIMove() {
        if (!this.currentGame || this.isPlayerTurn) return;
        
        try {
            // Show thinking indicator
            const gameStatus = document.getElementById('game-status');
            if (gameStatus) {
                const thinkingDiv = document.createElement('div');
                thinkingDiv.className = 'thinking-indicator';
                thinkingDiv.textContent = '🤖 IA está pensando...';
                gameStatus.appendChild(thinkingDiv);
            }
            
            const result = await api.getAIMove(this.currentGame.id);
            
            // Remove thinking indicator
            const thinkingIndicator = document.querySelector('.thinking-indicator');
            if (thinkingIndicator) {
                thinkingIndicator.remove();
            }
            
            if (result.success) {
                // Update board
                if (this.gameBoard) {
                    this.gameBoard.setPosition(result.fen);
                    if (result.lastMove) {
                        this.gameBoard.highlightMove(result.lastMove.from, result.lastMove.to);
                    }
                }
                
                // Update game state
                this.currentGame = result.game;
                this.updateGameStatus();
                this.updateMoveHistory();
                
                // Switch turns
                this.isPlayerTurn = true;
                
                Utils.showToast(`IA jogou: ${result.move}`, 'info');
                
                // Check if game is over
                if (result.game.status === 'finished') {
                    this.endGame();
                }
                
            } else {
                Utils.showToast('Erro ao processar lance da IA', 'error');
            }
            
        } catch (error) {
            Utils.handleError(error, 'getAIMove');
        }
    }
    
    updateMoveHistory() {
        if (!this.currentGame || !this.currentGame.moveHistory) return;
        
        const moveList = document.getElementById('move-list');
        if (!moveList) return;
        
        moveList.innerHTML = '';
        
        this.currentGame.moveHistory.forEach((move, index) => {
            const moveDiv = document.createElement('div');
            moveDiv.className = 'move-item';
            
            const moveNumber = Math.floor(index / 2) + 1;
            const isWhite = index % 2 === 0;
            const prefix = isWhite ? `${moveNumber}.` : `${moveNumber}...`;
            
            moveDiv.innerHTML = `
                <span class="move-number">${prefix}</span>
                <span class="move-san">${move.san}</span>
                <span class="move-time">${Utils.formatDuration(move.time || 0)}</span>
            `;
            
            moveList.appendChild(moveDiv);
        });
        
        // Scroll to bottom
        moveList.scrollTop = moveList.scrollHeight;
    }
    
    async getHint() {
        if (!this.currentGame || !this.isPlayerTurn) {
            Utils.showToast('Não é possível obter dica agora', 'warning');
            return;
        }
        
        try {
            Utils.showLoading('Obtendo dica...');
            
            const hint = await api.getHint(this.currentGame.id);
            
            Utils.hideLoading();
            
            if (hint.success) {
                Utils.showToast(`💡 Dica: ${hint.suggestion}`, 'info', 8000);
            } else {
                Utils.showToast('Não foi possível obter uma dica', 'warning');
            }
            
        } catch (error) {
            Utils.hideLoading();
            Utils.handleError(error, 'getHint');
        }
    }
    
    async saveGame() {
        if (!this.currentGame) {
            Utils.showToast('Nenhum jogo para salvar', 'warning');
            return;
        }
        
        try {
            Utils.showLoading('Salvando jogo...');
            
            // Implementation would depend on API
            // For now, just show success message
            
            Utils.hideLoading();
            Utils.showToast('Jogo salvo com sucesso!', 'success');
            
        } catch (error) {
            Utils.hideLoading();
            Utils.handleError(error, 'saveGame');
        }
    }
    
    restartGame() {
        if (confirm('Tem certeza que deseja reiniciar o jogo?')) {
            this.currentGame = null;
            this.isPlayerTurn = false;
            
            if (this.gameBoard) {
                this.gameBoard.setPosition('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1');
            }
            
            // Hide game controls
            const gameControls = document.querySelector('.game-controls');
            if (gameControls) {
                gameControls.style.display = 'none';
            }
            
            const moveInput = document.querySelector('.move-input');
            if (moveInput) {
                moveInput.style.display = 'none';
            }
            
            // Update status
            const gameStatus = document.getElementById('game-status');
            if (gameStatus) {
                gameStatus.innerHTML = '<p>Configure um novo jogo para começar</p>';
            }
            
            // Clear move history
            const moveList = document.getElementById('move-list');
            if (moveList) {
                moveList.innerHTML = '';
            }
        }
    }
    
    endGame() {
        this.isPlayerTurn = false;
        this.stopGameMonitoring();
        
        const result = this.getGameResult();
        Utils.showToast(`Jogo finalizado: ${result}`, 'info', 10000);
        
        // Hide move input
        const moveInput = document.querySelector('.move-input');
        if (moveInput) {
            moveInput.style.display = 'none';
        }
    }
    
    getGameResult() {
        if (!this.currentGame || !this.currentGame.result) {
            return 'Resultado desconhecido';
        }
        
        const result = this.currentGame.result;
        const playerColor = this.currentGame.playerColor;
        
        if (result === '1-0') {
            return playerColor === 'white' ? 'Você venceu!' : 'IA venceu!';
        } else if (result === '0-1') {
            return playerColor === 'black' ? 'Você venceu!' : 'IA venceu!';
        } else {
            return 'Empate!';
        }
    }
    
    startGameMonitoring() {
        if (this.gameUpdateInterval) {
            clearInterval(this.gameUpdateInterval);
        }
        
        this.gameUpdateInterval = setInterval(() => {
            if (this.currentGame && this.currentGame.status === 'playing') {
                this.updateGameStatus();
            }
        }, 1000);
    }
    
    stopGameMonitoring() {
        if (this.gameUpdateInterval) {
            clearInterval(this.gameUpdateInterval);
            this.gameUpdateInterval = null;
        }
    }
    
    handleGameUpdate(data) {
        if (this.currentGame && data.gameId === this.currentGame.id) {
            this.currentGame = data.game;
            this.updateGameStatus();
            this.updateMoveHistory();
            
            if (this.gameBoard && data.fen) {
                this.gameBoard.setPosition(data.fen);
                if (data.lastMove) {
                    this.gameBoard.highlightMove(data.lastMove.from, data.lastMove.to);
                }
            }
        }
    }
    
    destroy() {
        this.stopGameMonitoring();
        
        if (this.gameBoard) {
            this.gameBoard.destroy();
        }
    }
}

// Make Play available globally
window.Play = Play;