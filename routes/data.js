const express = require('express');
const router = express.Router();

// Get database statistics
router.get('/stats', (req, res) => {
    const stats = {
        total_games: Math.floor(Math.random() * 500) + 100,
        unique_models: 6,
        db_size_mb: Math.random() * 50 + 10
    };
    
    res.json(stats);
});

// Export all data
router.get('/export', (req, res) => {
    // Mock export data
    const exportData = {
        games: [
            {
                id: 1,
                white: "GPT-4o",
                black: "Gemini-Pro",
                result: "1-0",
                pgn: "[White \"GPT-4o\"] [Black \"Gemini-Pro\"] [Result \"1-0\"] 1. e4 e5 2. Nf3 Nc6 1-0",
                date: new Date().toISOString()
            }
        ],
        model_stats: [
            {
                model_name: "GPT-4o",
                games_played: 25,
                wins: 12,
                draws: 3,
                losses: 10,
                current_elo: 1567
            }
        ],
        export_date: new Date().toISOString()
    };
    
    res.json(exportData);
});

// Import data
router.post('/import', (req, res) => {
    const data = req.body;
    
    // Mock import process
    setTimeout(() => {
        if (data && data.games) {
            res.json({
                success: true,
                imported_games: data.games.length,
                message: 'Data imported successfully'
            });
        } else {
            res.json({
                success: false,
                error: 'Invalid data format'
            });
        }
    }, 1000);
});

// Clear old games
router.post('/clear-old', (req, res) => {
    const { days } = req.body;
    
    // Mock clearing old games
    setTimeout(() => {
        const deleted = Math.floor(Math.random() * 20) + 5;
        res.json({
            success: true,
            deleted,
            message: `Deleted ${deleted} games older than ${days} days`
        });
    }, 1000);
});

// Reset database
router.post('/reset', (req, res) => {
    // Mock database reset
    setTimeout(() => {
        res.json({
            success: true,
            message: 'Database reset successfully'
        });
    }, 2000);
});

module.exports = router;