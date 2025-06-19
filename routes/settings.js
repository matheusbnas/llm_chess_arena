const express = require('express');
const router = express.Router();

// Mock settings storage
let currentSettings = {
    modelParams: {
        temperature: 0.1,
        maxTokens: 1000,
        thinkingTime: 5
    },
    gameSettings: {
        defaultTimeControl: '10',
        auto SaveGames: true,
        showCoordinates: true,
        highlightLastMove: true,
        autoAnalysis: false,
        analysisDepth: 12,
        saveAnalysis: true
    },
    stockfish: {
        path: '/usr/local/bin/stockfish',
        depth: 15
    }
};

// Get current settings
router.get('/', (req, res) => {
    res.json(currentSettings);
});

// Update settings
router.put('/', (req, res) => {
    currentSettings = { ...currentSettings, ...req.body };
    res.json({
        success: true,
        settings: currentSettings
    });
});

// Save API keys
router.post('/api-keys', (req, res) => {
    const { openai, google, deepseek, groq } = req.body;
    
    // Mock saving API keys
    setTimeout(() => {
        res.json({
            success: true,
            message: 'API keys saved successfully'
        });
    }, 1000);
});

// Test Stockfish
router.post('/test-stockfish', (req, res) => {
    const { path } = req.body;
    
    // Mock Stockfish test
    setTimeout(() => {
        if (path && path.includes('stockfish')) {
            res.json({
                success: true,
                version: 'Stockfish 15.1'
            });
        } else {
            res.json({
                success: false,
                error: 'Stockfish not found at specified path'
            });
        }
    }, 1000);
});

module.exports = router;