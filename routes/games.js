const express = require('express');
const router = express.Router();
const { Chess } = require('chess.js');

// Mock database - in production, use a real database
let games = [];
let gameIdCounter = 1;

// Get all games
router.get('/', (req, res) => {
    res.json(games);
});

// Get specific game
router.get('/:id', (req, res) => {
    const game = games.find(g => g.id === parseInt(req.params.id));
    if (!game) {
        return res.status(404).json({ error: 'Game not found' });
    }
    res.json(game);
});

// Create new game
router.post('/', (req, res) => {
    const { white, black, pgn, result, moves, opening } = req.body;
    
    const game = {
        id: gameIdCounter++,
        white,
        black,
        pgn,
        result,
        moves: moves || 0,
        opening: opening || '',
        date: new Date().toISOString(),
        created_at: new Date().toISOString()
    };
    
    games.push(game);
    res.json(game);
});

// Get recent games
router.get('/recent', (req, res) => {
    const limit = parseInt(req.query.limit) || 10;
    const recentGames = games
        .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
        .slice(0, limit)
        .map(game => ({
            id: game.id,
            White: game.white,
            Black: game.black,
            Result: game.result,
            Moves: game.moves,
            Opening: game.opening,
            Date: game.date
        }));
    
    res.json(recentGames);
});

// Get games between specific models
router.get('/between', (req, res) => {
    const { model1, model2 } = req.query;
    
    const filteredGames = games.filter(game => 
        (game.white === model1 && game.black === model2) ||
        (game.white === model2 && game.black === model1)
    );
    
    res.json(filteredGames);
});

// Start battle between models
router.post('/battle', async (req, res) => {
    const { whiteModel, blackModel, opening, numGames } = req.body;
    
    // Mock battle creation
    const battle = {
        id: `battle_${Date.now()}`,
        whiteModel,
        blackModel,
        opening,
        numGames,
        currentGame: 0,
        whiteWins: 0,
        blackWins: 0,
        draws: 0,
        results: [],
        status: 'active',
        created_at: new Date().toISOString()
    };
    
    // Simulate battle progress
    setTimeout(() => {
        simulateBattle(battle);
    }, 1000);
    
    res.json(battle);
});

// Start tournament
router.post('/tournament', async (req, res) => {
    const { models, gamesPerPair } = req.body;
    
    const tournament = {
        id: `tournament_${Date.now()}`,
        participants: models,
        gamesPerPair,
        totalGames: models.length * (models.length - 1) * gamesPerPair,
        completedGames: 0,
        standings: models.map(model => ({
            model,
            points: 0,
            games: 0
        })),
        status: 'active',
        created_at: new Date().toISOString()
    };
    
    res.json(tournament);
});

// Get battle status
router.get('/battle/:id/status', (req, res) => {
    // Mock battle status
    res.json({
        id: req.params.id,
        status: 'active',
        currentGame: 3,
        totalGames: 5,
        whiteWins: 1,
        blackWins: 1,
        draws: 1,
        completed: false
    });
});

// Human vs AI game routes
router.post('/human', (req, res) => {
    const { opponentModel, playerColor, difficulty, timeControl } = req.body;
    
    const game = {
        id: `human_${Date.now()}`,
        opponentModel,
        playerColor,
        difficulty,
        timeControl,
        fen: 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1',
        moveHistory: [],
        status: 'playing',
        created_at: new Date().toISOString()
    };
    
    res.json(game);
});

router.post('/human/:id/move', (req, res) => {
    const { move } = req.body;
    
    try {
        const chess = new Chess();
        // Validate move
        const moveObj = chess.move(move);
        
        if (moveObj) {
            res.json({
                success: true,
                move: moveObj.san,
                fen: chess.fen(),
                game: {
                    id: req.params.id,
                    status: chess.isGameOver() ? 'finished' : 'playing',
                    result: chess.isGameOver() ? chess.pgn() : null
                }
            });
        } else {
            res.json({
                success: false,
                error: 'Invalid move'
            });
        }
    } catch (error) {
        res.json({
            success: false,
            error: error.message
        });
    }
});

router.post('/human/:id/ai-move', (req, res) => {
    // Mock AI move
    const chess = new Chess();
    const moves = chess.moves();
    const randomMove = moves[Math.floor(Math.random() * moves.length)];
    
    const moveObj = chess.move(randomMove);
    
    res.json({
        success: true,
        move: moveObj.san,
        fen: chess.fen(),
        game: {
            id: req.params.id,
            status: chess.isGameOver() ? 'finished' : 'playing',
            result: chess.isGameOver() ? chess.pgn() : null
        }
    });
});

router.get('/human/:id/hint', (req, res) => {
    const hints = [
        "Considere desenvolver suas peças antes de atacar",
        "Proteja seu rei com o roque",
        "Controle o centro do tabuleiro",
        "Procure por táticas como garfos e cravadas",
        "Mantenha suas peças coordenadas"
    ];
    
    const randomHint = hints[Math.floor(Math.random() * hints.length)];
    
    res.json({
        success: true,
        suggestion: randomHint
    });
});

// Simulate battle progress
function simulateBattle(battle) {
    const interval = setInterval(() => {
        if (battle.currentGame >= battle.numGames) {
            clearInterval(interval);
            return;
        }
        
        battle.currentGame++;
        
        // Simulate game result
        const results = ['1-0', '0-1', '1/2-1/2'];
        const result = results[Math.floor(Math.random() * results.length)];
        
        if (result === '1-0') battle.whiteWins++;
        else if (result === '0-1') battle.blackWins++;
        else battle.draws++;
        
        battle.results.push({
            game: battle.currentGame,
            white: battle.whiteModel,
            black: battle.blackModel,
            result,
            moves: Math.floor(Math.random() * 60) + 20
        });
        
        // Create a game record
        const game = {
            id: gameIdCounter++,
            white: battle.whiteModel,
            black: battle.blackModel,
            result,
            pgn: `[White "${battle.whiteModel}"] [Black "${battle.blackModel}"] [Result "${result}"] 1. e4 e5 2. Nf3 Nc6 ${result}`,
            moves: Math.floor(Math.random() * 60) + 20,
            opening: battle.opening || '1. e4',
            date: new Date().toISOString(),
            created_at: new Date().toISOString()
        };
        
        games.push(game);
    }, 2000);
}

module.exports = router;