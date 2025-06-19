class ChessArenaApp {
    constructor() {
        this.currentPage = 'dashboard';
        this.socket = null;
        this.charts = {};
        
        this.init();
    }
    
    init() {
        this.setupNavigation();
        this.setupSocketConnection();
        this.loadInitialData();
        this.setupGlobalEventListeners();
        
        // Initialize page modules
        this.dashboard = new Dashboard();
        this.arena = new Arena();
        this.play = new Play();
        this.analysis = new Analysis();
        this.rankings = new Rankings();
        this.settings = new Settings();
        
        // Load the initial page
        this.showPage('dashboard');
    }
    
    setupNavigation() {
        const navButtons = document.querySelectorAll('.nav-btn');
        
        navButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                const page = btn.dataset.page;
                this.showPage(page);
                
                // Update active nav button
                navButtons.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
            });
        });
    }
    
    setupSocketConnection() {
        this.socket = io();
        
        this.socket.on('connect', () => {
            console.log('Connected to server');
        });
        
        this.socket.on('disconnect', () => {
            console.log('Disconnected from server');
            Utils.showToast('Conexão perdida com o servidor', 'warning');
        });
        
        this.socket.on('game-update', (data) => {
            this.handleGameUpdate(data);
        });
        
        this.socket.on('battle-update', (data) => {
            this.handleBattleUpdate(data);
        });
        
        this.socket.on('tournament-update', (data) => {
            this.handleTournamentUpdate(data);
        });
    }
    
    async loadInitialData() {
        try {
            Utils.showLoading('Carregando dados iniciais...');
            
            // Load available models
            const models = await api.getAvailableModels();
            this.updateModelSelectors(models);
            
            // Load global stats
            const stats = await api.getGlobalStats();
            this.updateGlobalStats(stats);
            
            Utils.hideLoading();
        } catch (error) {
            Utils.hideLoading();
            Utils.handleError(error, 'loadInitialData');
        }
    }
    
    setupGlobalEventListeners() {
        // Handle tab switching
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('tab-btn')) {
                const tabContainer = e.target.closest('.analysis-tabs, .rankings-tabs, .settings-tabs');
                if (tabContainer) {
                    this.switchTab(e.target, tabContainer);
                }
            }
        });
        
        // Handle range input updates
        document.addEventListener('input', (e) => {
            if (e.target.type === 'range') {
                const valueSpan = document.getElementById(e.target.id + '-value');
                if (valueSpan) {
                    valueSpan.textContent = e.target.value;
                }
            }
        });
        
        // Handle keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            this.handleKeyboardShortcuts(e);
        });
        
        // Handle window resize
        window.addEventListener('resize', Utils.debounce(() => {
            this.handleResize();
        }, 250));
    }
    
    showPage(pageId) {
        // Hide all pages
        document.querySelectorAll('.page').forEach(page => {
            page.classList.remove('active');
        });
        
        // Show selected page
        const page = document.getElementById(`${pageId}-page`);
        if (page) {
            page.classList.add('active');
            this.currentPage = pageId;
            
            // Initialize page-specific functionality
            this.initializePage(pageId);
        }
    }
    
    initializePage(pageId) {
        switch (pageId) {
            case 'dashboard':
                this.dashboard.init();
                break;
            case 'arena':
                this.arena.init();
                break;
            case 'play':
                this.play.init();
                break;
            case 'analysis':
                this.analysis.init();
                break;
            case 'rankings':
                this.rankings.init();
                break;
            case 'settings':
                this.settings.init();
                break;
        }
    }
    
    switchTab(tabBtn, container) {
        const tabId = tabBtn.dataset.tab;
        
        // Update tab buttons
        container.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        tabBtn.classList.add('active');
        
        // Update tab panels
        const tabContent = container.nextElementSibling;
        if (tabContent && tabContent.classList.contains('tab-content')) {
            tabContent.querySelectorAll('.tab-panel').forEach(panel => {
                panel.classList.remove('active');
            });
            
            const targetPanel = tabContent.querySelector(`#${tabId}-tab`);
            if (targetPanel) {
                targetPanel.classList.add('active');
            }
        }
    }
    
    updateModelSelectors(models) {
        const selectors = [
            'white-model', 'black-model', 'opponent-model',
            'model1-select', 'model2-select', 'stats-model-select',
            'test-model-select'
        ];
        
        selectors.forEach(selectorId => {
            const select = document.getElementById(selectorId);
            if (select) {
                select.innerHTML = '';
                
                Object.entries(models).forEach(([name, available]) => {
                    const option = document.createElement('option');
                    option.value = name;
                    option.textContent = `${available ? '🟢' : '🔴'} ${name}`;
                    option.disabled = !available;
                    select.appendChild(option);
                });
            }
        });
        
        // Update tournament model checkboxes
        const tournamentModels = document.getElementById('tournament-models');
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
    
    updateGlobalStats(stats) {
        const elements = {
            'total-games': stats.totalGames || 0,
            'active-models': stats.activeModels || 0,
            'avg-moves': Math.round(stats.avgGameLength || 0),
            'tournaments': stats.tournamentsCompleted || 0
        };
        
        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value;
            }
        });
    }
    
    handleGameUpdate(data) {
        // Handle real-time game updates
        if (this.currentPage === 'play' && this.play) {
            this.play.handleGameUpdate(data);
        }
        
        if (this.currentPage === 'arena' && this.arena) {
            this.arena.handleGameUpdate(data);
        }
    }
    
    handleBattleUpdate(data) {
        if (this.currentPage === 'arena' && this.arena) {
            this.arena.handleBattleUpdate(data);
        }
    }
    
    handleTournamentUpdate(data) {
        if (this.currentPage === 'arena' && this.arena) {
            this.arena.handleTournamentUpdate(data);
        }
    }
    
    handleKeyboardShortcuts(e) {
        // Ctrl/Cmd + number keys for page navigation
        if ((e.ctrlKey || e.metaKey) && e.key >= '1' && e.key <= '6') {
            e.preventDefault();
            const pages = ['dashboard', 'arena', 'play', 'analysis', 'rankings', 'settings'];
            const pageIndex = parseInt(e.key) - 1;
            if (pages[pageIndex]) {
                this.showPage(pages[pageIndex]);
                
                // Update nav button
                const navBtn = document.querySelector(`[data-page="${pages[pageIndex]}"]`);
                if (navBtn) {
                    document.querySelectorAll('.nav-btn').forEach(btn => btn.classList.remove('active'));
                    navBtn.classList.add('active');
                }
            }
        }
        
        // Escape key to close modals/dialogs
        if (e.key === 'Escape') {
            const dialogs = document.querySelectorAll('.promotion-dialog, .modal, .overlay');
            dialogs.forEach(dialog => {
                if (dialog.style.display !== 'none') {
                    dialog.style.display = 'none';
                }
            });
        }
    }
    
    handleResize() {
        // Resize charts
        Object.values(this.charts).forEach(chart => {
            if (chart && chart.resize) {
                chart.resize();
            }
        });
        
        // Resize chessboards
        const boards = document.querySelectorAll('.chessboard');
        boards.forEach(board => {
            const container = board.parentElement;
            const containerWidth = container.clientWidth;
            const maxSize = Math.min(containerWidth - 40, 480);
            
            if (board.chessBoard && board.chessBoard.resize) {
                board.chessBoard.resize(maxSize);
            }
        });
    }
    
    // Utility methods for other modules
    createChart(canvasId, config) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return null;
        
        const ctx = canvas.getContext('2d');
        const chart = new Chart(ctx, config);
        
        this.charts[canvasId] = chart;
        return chart;
    }
    
    destroyChart(canvasId) {
        if (this.charts[canvasId]) {
            this.charts[canvasId].destroy();
            delete this.charts[canvasId];
        }
    }
    
    updateChart(canvasId, newData) {
        const chart = this.charts[canvasId];
        if (chart) {
            chart.data = newData;
            chart.update();
        }
    }
    
    // Socket methods for other modules
    joinRoom(roomId) {
        if (this.socket) {
            this.socket.emit('join-room', roomId);
        }
    }
    
    leaveRoom(roomId) {
        if (this.socket) {
            this.socket.emit('leave-room', roomId);
        }
    }
    
    emitEvent(event, data) {
        if (this.socket) {
            this.socket.emit(event, data);
        }
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new ChessArenaApp();
});