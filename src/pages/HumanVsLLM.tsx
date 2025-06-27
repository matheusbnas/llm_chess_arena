import React, { useState, useEffect, useRef } from 'react';
import { API_URL, WS_URL } from '../config/api';

interface GameState {
}

const HumanVsLLM: React.FC = () => {
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [models, setModels] = useState<string[]>([]);
  const [selectedModel, setSelectedModel] = useState<string>('');
  const [playerColor, setPlayerColor] = useState<'white' | 'black'>('white');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    loadModels();
  }, []);

  const connectWebSocket = () => {
    if (wsRef.current) {
      wsRef.current.close();
    }

    wsRef.current = new WebSocket(`${WS_URL}/ws`);
    
    wsRef.current.onopen = () => {
      console.log('WebSocket connected');
    };
    
    wsRef.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'game_update') {
          setGameState(data.data);
        } else if (data.type === 'error') {
          setError(data.message);
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };
    
    wsRef.current.onerror = (error) => {
      console.error('WebSocket error:', error);
      setError('WebSocket connection error');
    };
    
    wsRef.current.onclose = () => {
      console.log('WebSocket disconnected');
    };
  };

  const loadModels = async () => {
    try {
      const response = await fetch(`${API_URL}/models`);
      const data = await response.json();
      setModels(data.models);
      if (data.models.length > 0) {
        setSelectedModel(data.models[0]);
      }
    } catch (error) {
      console.error('Error loading models:', error);
      setError('Failed to load models');
    }
  };

  const startGame = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Connect WebSocket before starting game
      connectWebSocket();
      
      const response = await fetch(`${API_URL}/human-game/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model: selectedModel,
          player_color: playerColor,
        }),
      });
      const data = await response.json();
      setGameState(data);
    } catch (error) {
      console.error('Error starting game:', error);
      setError('Failed to start game');
    } finally {
      setLoading(false);
    }
  };

  const makeMove = async (move: string) => {
    try {
      const response = await fetch(`${API_URL}/human-game/move`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          move: move,
        }),
      });
      const data = await response.json();
      setGameState(data);
    } catch (error) {
      console.error('Error making move:', error);
      setError('Failed to make move');
    }
  };

  const resetGame = async () => {
    try {
      await fetch(`${API_URL}/human-game/reset`, {
        method: 'POST',
      });
      setGameState(null);
      if (wsRef.current) {
        wsRef.current.close();
      }
    } catch (error) {
      console.error('Error resetting game:', error);
    }
  };

  // Cleanup WebSocket on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);
}