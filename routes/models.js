const express = require('express');
const router = express.Router();

// Mock available models
const availableModels = {
    "GPT-4o": true,
    "GPT-4-Turbo": true,
    "GPT-3.5-Turbo": true,
    "Gemini-Pro": true,
    "Gemini-1.0-Pro": true,
    "Deepseek-Chat": false,
    "Deepseek-Coder": false,
    "Llama3-70B": false,
    "Mixtral-8x7B": false
};

// Get available models
router.get('/available', (req, res) => {
    res.json(availableModels);
});

// Get all models
router.get('/', (req, res) => {
    const models = Object.keys(availableModels).map(name => ({
        name,
        available: availableModels[name],
        provider: getProvider(name)
    }));
    
    res.json(models);
});

// Test model
router.post('/test', (req, res) => {
    const { modelName } = req.body;
    
    if (!availableModels[modelName]) {
        return res.json({
            success: false,
            error: 'Model not found'
        });
    }
    
    if (!availableModels[modelName]) {
        return res.json({
            success: false,
            error: 'Model not available'
        });
    }
    
    // Simulate test
    setTimeout(() => {
        res.json({
            success: true,
            response_time: Math.random() * 2 + 0.5,
            response: 'e4'
        });
    }, 1000);
});

// Get model stats
router.get('/:name/stats', (req, res) => {
    const modelName = req.params.name;
    
    // Mock stats
    const stats = {
        model: modelName,
        games_played: Math.floor(Math.random() * 100) + 10,
        wins: Math.floor(Math.random() * 40) + 5,
        draws: Math.floor(Math.random() * 20) + 2,
        losses: Math.floor(Math.random() * 40) + 3,
        avg_accuracy: Math.random() * 20 + 70,
        current_elo: Math.floor(Math.random() * 400) + 1400
    };
    
    res.json(stats);
});

// Update model config
router.put('/:name/config', (req, res) => {
    const modelName = req.params.name;
    const config = req.body;
    
    // Mock config update
    res.json({
        success: true,
        model: modelName,
        config
    });
});

function getProvider(modelName) {
    if (modelName.includes('GPT')) return 'OpenAI';
    if (modelName.includes('Gemini')) return 'Google';
    if (modelName.includes('Deepseek')) return 'DeepSeek';
    if (modelName.includes('Llama') || modelName.includes('Mixtral')) return 'Groq';
    return 'Unknown';
}

module.exports = router;