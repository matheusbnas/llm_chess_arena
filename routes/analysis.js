const express = require('express');
const router = express.Router();

// Analyze specific game
router.get('/game/:id', (req, res) => {
    const gameId = req.params.id;
    
    // Mock analysis data
    const analysis = {
        total_moves: Math.floor(Math.random() * 60) + 20,
        white_accuracy: Math.random() * 20 + 70,
        black_accuracy: Math.random() * 20 + 70,
        move_evaluations: Array.from({ length: 40 }, () => (Math.random() - 0.5) * 4),
        move_accuracies: Array.from({ length: 40 }, () => Math.random() * 0.3 + 0.7),
        blunders: Math.floor(Math.random() * 5),
        best_moves: [
            { move_number: 5, san: 'Nf3', accuracy: 0.95 },
            { move_number: 12, san: 'O-O', accuracy: 0.92 },
            { move_number: 18, san: 'Qd2', accuracy: 0.89 }
        ],
        worst_moves: [
            { move_number: 23, san: 'Bxf7+', accuracy: 0.25 },
            { move_number: 31, san: 'Qh5', accuracy: 0.18 }
        ],
        average_evaluation: Math.random() * 2 - 1
    };
    
    res.json(analysis);
});

// Compare two models
router.post('/compare', (req, res) => {
    const { model1, model2 } = req.body;
    
    // Mock comparison data
    const comparison = {
        model1_wins: Math.floor(Math.random() * 10) + 5,
        model2_wins: Math.floor(Math.random() * 10) + 5,
        draws: Math.floor(Math.random() * 5) + 1,
        model1_accuracy: Math.random() * 15 + 75,
        model2_accuracy: Math.random() * 15 + 75,
        model1_avg_moves: Math.random() * 20 + 35,
        model2_avg_moves: Math.random() * 20 + 35,
        model1_error_rate: Math.random() * 10 + 5,
        model2_error_rate: Math.random() * 10 + 5,
        model1_avg_time: Math.random() * 3 + 1,
        model2_avg_time: Math.random() * 3 + 1,
        performance_over_time: Array.from({ length: 20 }, (_, i) => [
            { game_number: i + 1, model: model1, accuracy: Math.random() * 20 + 70 },
            { game_number: i + 1, model: model2, accuracy: Math.random() * 20 + 70 }
        ]).flat()
    };
    
    res.json(comparison);
});

// Get ELO ratings
router.get('/elo', (req, res) => {
    const models = ["GPT-4o", "GPT-4-Turbo", "Gemini-Pro", "Gemini-1.0-Pro"];
    
    const rankings = models.map((model, index) => ({
        model,
        elo: Math.floor(Math.random() * 400) + 1400,
        games_played: Math.floor(Math.random() * 50) + 20,
        win_rate: Math.random() * 0.4 + 0.3,
        avg_accuracy: Math.random() * 20 + 70
    }));
    
    res.json(rankings);
});

// Get detailed stats for a model
router.get('/stats/:model', (req, res) => {
    const model = req.params.model;
    
    const stats = {
        total_games: Math.floor(Math.random() * 100) + 20,
        wins: Math.floor(Math.random() * 40) + 10,
        draws: Math.floor(Math.random() * 15) + 3,
        losses: Math.floor(Math.random() * 45) + 7,
        win_rate: Math.random() * 40 + 30,
        avg_accuracy: Math.random() * 20 + 70,
        current_elo: Math.floor(Math.random() * 400) + 1400,
        by_color: {
            white: {
                wins: Math.floor(Math.random() * 20) + 5,
                draws: Math.floor(Math.random() * 8) + 1,
                losses: Math.floor(Math.random() * 22) + 3
            },
            black: {
                wins: Math.floor(Math.random() * 20) + 5,
                draws: Math.floor(Math.random() * 7) + 2,
                losses: Math.floor(Math.random() * 23) + 4
            }
        },
        recent_trend: Array.from({ length: 20 }, () => Math.random() * 30 + 60)
    };
    
    res.json(stats);
});

// Get opening statistics
router.get('/openings', (req, res) => {
    const openings = [
        "King's Pawn Opening",
        "Queen's Pawn Opening",
        "English Opening",
        "Réti Opening",
        "King's Indian Attack",
        "Nimzo-Larsen Attack"
    ];
    
    const stats = openings.map(opening => ({
        opening,
        games_played: Math.floor(Math.random() * 30) + 5,
        win_rate: Math.random() * 0.4 + 0.3,
        avg_accuracy: Math.random() * 20 + 70,
        avg_game_length: Math.random() * 20 + 35
    }));
    
    res.json(stats);
});

// Get global statistics
router.get('/global', (req, res) => {
    const stats = {
        totalGames: Math.floor(Math.random() * 500) + 100,
        activeModels: 6,
        avgGameLength: Math.random() * 20 + 35,
        tournamentsCompleted: Math.floor(Math.random() * 10) + 2
    };
    
    res.json(stats);
});

// Get results by model
router.get('/results-by-model', (req, res) => {
    const models = ["GPT-4o", "GPT-4-Turbo", "Gemini-Pro", "Gemini-1.0-Pro"];
    
    const results = models.map(model => ({
        model,
        wins: Math.floor(Math.random() * 30) + 10,
        draws: Math.floor(Math.random() * 10) + 2,
        losses: Math.floor(Math.random() * 25) + 8
    }));
    
    res.json(results);
});

// Get winrate data
router.get('/winrate', (req, res) => {
    const data = [
        { result_type: 'White Wins', percentage: Math.floor(Math.random() * 50) + 100 },
        { result_type: 'Black Wins', percentage: Math.floor(Math.random() * 50) + 90 },
        { result_type: 'Draws', percentage: Math.floor(Math.random() * 30) + 20 }
    ];
    
    res.json(data);
});

// Get ELO history
router.get('/elo-history', (req, res) => {
    const models = ["GPT-4o", "GPT-4-Turbo", "Gemini-Pro"];
    const history = [];
    
    models.forEach(model => {
        let elo = 1500;
        for (let i = 0; i < 30; i++) {
            elo += (Math.random() - 0.5) * 50;
            elo = Math.max(1200, Math.min(1800, elo));
            
            const date = new Date();
            date.setDate(date.getDate() - (30 - i));
            
            history.push({
                model,
                elo: Math.round(elo),
                date: date.toISOString().split('T')[0]
            });
        }
    });
    
    res.json(history);
});

module.exports = router;