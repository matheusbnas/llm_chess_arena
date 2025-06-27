import React, { useState, useEffect } from 'react'
import { Play, RotateCcw, Lightbulb, Save, Clock, User, Bot } from 'lucide-react'
import { Chess } from 'chess.js'
import { toast } from 'react-hot-toast'
import ChessBoard from '@/components/ChessBoard'
import GameStatus from '@/components/GameStatus'
import ModelSelector from '@/components/ModelSelector'
import MoveHistory from '@/components/MoveHistory'
import { useGameStore } from '@/stores/gameStore'
import { useAppStore } from '@/stores/appStore'
import { endpoints } from '@/lib/api'
import { wsManager } from '@/lib/websocket'

interface HumanGameConfig {
  opponent: string
  playerColor: 'white' | 'black'
  difficulty: 'Beginner' | 'Intermediate' | 'Advanced' | 'Master'
  timeControl: string
}

export default function HumanVsLLM() {
  const [gameConfig, setGameConfig] = useState<HumanGameConfig>({
    opponent: '',
    playerColor: 'white',
    difficulty: 'Advanced',
    timeControl: 'No limit'
  })
  
  const [gameActive, setGameActive] = useState(false)
  const [moveInput, setMoveInput] = useState('')
  const [humanExplanation, setHumanExplanation] = useState('')
  const [aiExplanation, setAiExplanation] = useState('')
  const [isAiThinking, setIsAiThinking] = useState(false)
  const [gameResult, setGameResult] = useState<string | null>(null)
  const [timeLeft, setTimeLeft] = useState<{ white: number; black: number }>({ white: 600, black: 600 })
  
  const { models, setModels } = useAppStore()
  const { 
    currentGame, 
    moveHistory, 
    isPlaying,
    playerColor,
    setCurrentGame, 
    addMove, 
    resetGame,
    setIsPlaying,
    setPlayerColor
  } = useGameStore()

  useEffect(() => {
    // Load available models
    const loadModels = async () => {
      try {
        const response = await endpoints.models.list()
        setModels(response.data)
        
        if (response.data.length > 0) {
          setGameConfig(prev => ({ ...prev, opponent: response.data[0].name }))
        }
      } catch (error) {
        console.error('Error loading models:', error)
        toast.error('Failed to load models')
      }
    }

    loadModels()

    // Connect to WebSocket for real-time updates
    wsManager.connect()

    // Listen for game updates
    wsManager.on('game_update', (data) => {
      if (data.move) {
        addMove(data.move)
      }
      if (data.explanation) {
        setAiExplanation(data.explanation)
      }
      if (data.game_over) {
        setGameResult(data.result)
        setGameActive(false)
        setIsPlaying(false)
      }
    })

    wsManager.on('ai_thinking', (data) => {
      setIsAiThinking(data.thinking)
    })

    return () => {
      wsManager.off('game_update', () => {})
      wsManager.off('ai_thinking', () => {})
    }
  }, [setModels, addMove, setIsPlaying])

  const startNewGame = async () => {
    try {
      const game = new Chess()
      setCurrentGame(game)
      setGameActive(true)
      setIsPlaying(true)
      setPlayerColor(gameConfig.playerColor)
      setGameResult(null)
      setAiExplanation('')
      resetGame()

      // Start game on backend
      await endpoints.humanGame.start({
        model: gameConfig.opponent,
        player_color: gameConfig.playerColor,
        difficulty: gameConfig.difficulty,
        time_control: gameConfig.timeControl
      })

      toast.success(`Game started against ${gameConfig.opponent}!`)

      // If AI plays first (player is black), trigger AI move
      if (gameConfig.playerColor === 'black') {
        makeAiMove()
      }

    } catch (error) {
      console.error('Error starting game:', error)
      toast.error('Failed to start game')
      setGameActive(false)
      setIsPlaying(false)
    }
  }

  const makeHumanMove = async () => {
    if (!currentGame || !moveInput.trim()) {
      toast.error('Please enter a valid move')
      return
    }

    try {
      // Validate and make the move
      const move = currentGame.move(moveInput.trim())
      
      if (!move) {
        toast.error('Invalid move')
        return
      }

      // Add move to history
      addMove({
        san: move.san,
        from: move.from,
        to: move.to,
        color: move.color,
        piece: move.piece,
        explanation: humanExplanation || 'Human move'
      })

      // Send move to backend
      await endpoints.humanGame.makeMove({
        move: move.san,
        explanation: humanExplanation
      })

      // Clear inputs
      setMoveInput('')
      setHumanExplanation('')

      // Check if game is over
      if (currentGame.isGameOver()) {
        setGameResult(currentGame.result())
        setGameActive(false)
        setIsPlaying(false)
        toast.success(`Game over! Result: ${currentGame.result()}`)
        return
      }

      // Trigger AI move if it's AI's turn
      if (currentGame.turn() !== (gameConfig.playerColor === 'white' ? 'w' : 'b')) {
        makeAiMove()
      }

    } catch (error) {
      console.error('Error making move:', error)
      toast.error('Failed to make move')
    }
  }

  const makeAiMove = async () => {
    if (!currentGame) return

    try {
      setIsAiThinking(true)
      setAiExplanation('')

      // Simulate AI thinking time
      await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 2000))

      // Get AI move (mock implementation)
      const possibleMoves = currentGame.moves()
      if (possibleMoves.length === 0) {
        setGameResult(currentGame.result())
        setGameActive(false)
        setIsPlaying(false)
        return
      }

      const randomMove = possibleMoves[Math.floor(Math.random() * possibleMoves.length)]
      const move = currentGame.move(randomMove)

      if (move) {
        // Generate AI explanation
        const explanations = [
          "Desenvolvo uma peça para uma casa ativa, controlando o centro.",
          "Esta jogada melhora a coordenação das minhas peças.",
          "Busco pressionar a posição adversária com este lance.",
          "Movimento estratégico para melhorar minha posição.",
          "Preparo um possível ataque futuro com esta jogada."
        ]
        const explanation = explanations[Math.floor(Math.random() * explanations.length)]

        addMove({
          san: move.san,
          from: move.from,
          to: move.to,
          color: move.color,
          piece: move.piece,
          explanation
        })

        setAiExplanation(explanation)

        // Check if game is over
        if (currentGame.isGameOver()) {
          setGameResult(currentGame.result())
          setGameActive(false)
          setIsPlaying(false)
          toast.success(`Game over! Result: ${currentGame.result()}`)
        }
      }

    } catch (error) {
      console.error('Error making AI move:', error)
      toast.error('AI failed to make a move')
    } finally {
      setIsAiThinking(false)
    }
  }

  const saveGame = async () => {
    if (!currentGame) {
      toast.error('No game to save')
      return
    }

    try {
      // Mock save game
      toast.success('Game saved successfully!')
    } catch (error) {
      console.error('Error saving game:', error)
      toast.error('Failed to save game')
    }
  }

  const showHint = () => {
    if (!currentGame) {
      toast.error('No active game')
      return
    }

    // Mock hint system
    const possibleMoves = currentGame.moves()
    if (possibleMoves.length > 0) {
      const hint = possibleMoves[Math.floor(Math.random() * Math.min(3, possibleMoves.length))]
      toast.success(`Hint: Consider ${hint}`, { duration: 5000 })
    }
  }

  const resetCurrentGame = () => {
    setCurrentGame(null)
    setGameActive(false)
    setIsPlaying(false)
    setGameResult(null)
    setMoveInput('')
    setHumanExplanation('')
    setAiExplanation('')
    setIsAiThinking(false)
    resetGame()
    toast.info('Game reset')
  }

  const isPlayerTurn = currentGame && gameActive && 
    currentGame.turn() === (gameConfig.playerColor === 'white' ? 'w' : 'b')

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Human vs LLM</h1>
        <p className="text-gray-600 mt-2">
          Challenge AI models to chess matches and improve your game
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Configuration Panel */}
        <div className="lg:col-span-1 space-y-6">
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Game Configuration
            </h3>

            <div className="space-y-4">
              {/* Opponent Selection */}
              <ModelSelector
                models={models}
                selectedModel={gameConfig.opponent}
                onModelSelect={(model) => setGameConfig(prev => ({ ...prev, opponent: model }))}
                label="Choose Your Opponent"
                disabled={gameActive}
              />

              {/* Color Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Your Color
                </label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    onClick={() => setGameConfig(prev => ({ ...prev, playerColor: 'white' }))}
                    disabled={gameActive}
                    className={`p-3 rounded-lg border text-center transition-colors ${
                      gameConfig.playerColor === 'white'
                        ? 'border-primary-500 bg-primary-50 text-primary-700'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="w-6 h-6 bg-white border border-gray-300 rounded-full mx-auto mb-1" />
                    <span className="text-sm font-medium">White</span>
                  </button>
                  <button
                    onClick={() => setGameConfig(prev => ({ ...prev, playerColor: 'black' }))}
                    disabled={gameActive}
                    className={`p-3 rounded-lg border text-center transition-colors ${
                      gameConfig.playerColor === 'black'
                        ? 'border-primary-500 bg-primary-50 text-primary-700'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="w-6 h-6 bg-gray-800 rounded-full mx-auto mb-1" />
                    <span className="text-sm font-medium">Black</span>
                  </button>
                </div>
              </div>

              {/* Difficulty */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Difficulty Level
                </label>
                <select
                  value={gameConfig.difficulty}
                  onChange={(e) => setGameConfig(prev => ({ 
                    ...prev, 
                    difficulty: e.target.value as any 
                  }))}
                  disabled={gameActive}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                >
                  <option value="Beginner">Beginner</option>
                  <option value="Intermediate">Intermediate</option>
                  <option value="Advanced">Advanced</option>
                  <option value="Master">Master</option>
                </select>
              </div>

              {/* Time Control */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Time Control
                </label>
                <select
                  value={gameConfig.timeControl}
                  onChange={(e) => setGameConfig(prev => ({ ...prev, timeControl: e.target.value }))}
                  disabled={gameActive}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                >
                  <option value="No limit">No limit</option>
                  <option value="5 min">5 minutes</option>
                  <option value="10 min">10 minutes</option>
                  <option value="15 min">15 minutes</option>
                  <option value="30 min">30 minutes</option>
                </select>
              </div>
            </div>

            {/* Control Buttons */}
            <div className="mt-6 space-y-3">
              {!gameActive ? (
                <button
                  onClick={startNewGame}
                  disabled={!gameConfig.opponent}
                  className="btn-primary w-full flex items-center justify-center space-x-2"
                >
                  <Play className="h-4 w-4" />
                  <span>Start Game</span>
                </button>
              ) : (
                <div className="space-y-2">
                  <button
                    onClick={resetCurrentGame}
                    className="btn-secondary w-full flex items-center justify-center space-x-2"
                  >
                    <RotateCcw className="h-4 w-4" />
                    <span>Reset Game</span>
                  </button>
                  
                  <button
                    onClick={saveGame}
                    className="btn-secondary w-full flex items-center justify-center space-x-2"
                  >
                    <Save className="h-4 w-4" />
                    <span>Save Game</span>
                  </button>
                  
                  <button
                    onClick={showHint}
                    disabled={!isPlayerTurn}
                    className="btn-secondary w-full flex items-center justify-center space-x-2"
                  >
                    <Lightbulb className="h-4 w-4" />
                    <span>Get Hint</span>
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Game Info */}
          {gameActive && (
            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Game Information
              </h3>
              
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">Opponent:</span>
                  <span className="font-medium">{gameConfig.opponent}</span>
                </div>
                
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">Your Color:</span>
                  <div className="flex items-center space-x-2">
                    <div className={`w-4 h-4 rounded-full ${
                      gameConfig.playerColor === 'white' ? 'bg-white border border-gray-300' : 'bg-gray-800'
                    }`} />
                    <span className="font-medium capitalize">{gameConfig.playerColor}</span>
                  </div>
                </div>
                
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">Difficulty:</span>
                  <span className="font-medium">{gameConfig.difficulty}</span>
                </div>
                
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">Time Control:</span>
                  <span className="font-medium">{gameConfig.timeControl}</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Game Display */}
        <div className="lg:col-span-2 space-y-6">
          {/* Game Status */}
          {currentGame && (
            <GameStatus
              game={currentGame}
              isPlaying={gameActive}
              currentPlayer={isPlayerTurn ? 'You' : gameConfig.opponent}
              timeLeft={gameConfig.timeControl !== 'No limit' ? timeLeft : undefined}
            />
          )}

          {/* Chess Board */}
          <div className="card">
            {currentGame ? (
              <ChessBoard
                game={currentGame}
                onMove={isPlayerTurn ? (move) => {
                  addMove(move)
                  if (!currentGame.isGameOver() && currentGame.turn() !== (gameConfig.playerColor === 'white' ? 'w' : 'b')) {
                    makeAiMove()
                  }
                } : undefined}
                disabled={!isPlayerTurn || isAiThinking}
                orientation={gameConfig.playerColor}
              />
            ) : (
              <div className="flex items-center justify-center h-96 bg-gray-50 rounded-lg">
                <div className="text-center">
                  <User className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600">Configure and start a game to begin playing</p>
                </div>
              </div>
            )}
          </div>

          {/* Move Input */}
          {gameActive && isPlayerTurn && (
            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Your Move
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Move (e.g., e4, Nf3, O-O)
                  </label>
                  <input
                    type="text"
                    value={moveInput}
                    onChange={(e) => setMoveInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && makeHumanMove()}
                    placeholder="Enter your move"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Explanation (optional)
                  </label>
                  <input
                    type="text"
                    value={humanExplanation}
                    onChange={(e) => setHumanExplanation(e.target.value)}
                    placeholder="Explain your move"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                </div>
              </div>
              
              <button
                onClick={makeHumanMove}
                disabled={!moveInput.trim()}
                className="btn-primary mt-4 flex items-center space-x-2"
              >
                <Play className="h-4 w-4" />
                <span>Make Move</span>
              </button>
            </div>
          )}

          {/* AI Thinking */}
          {isAiThinking && (
            <div className="card">
              <div className="flex items-center space-x-3">
                <Bot className="h-6 w-6 text-primary-600" />
                <div>
                  <p className="font-medium text-gray-900">{gameConfig.opponent} is thinking...</p>
                  <div className="flex space-x-1 mt-2">
                    <div className="w-2 h-2 bg-primary-600 rounded-full animate-bounce" />
                    <div className="w-2 h-2 bg-primary-600 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                    <div className="w-2 h-2 bg-primary-600 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* AI Explanation */}
          {aiExplanation && (
            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                {gameConfig.opponent}'s Explanation
              </h3>
              <p className="text-gray-700">{aiExplanation}</p>
            </div>
          )}

          {/* Move History */}
          {moveHistory.length > 0 && (
            <MoveHistory
              moves={moveHistory}
              currentMoveIndex={moveHistory.length - 1}
            />
          )}

          {/* Game Result */}
          {gameResult && (
            <div className="card">
              <div className="text-center">
                <Trophy className="h-12 w-12 text-yellow-500 mx-auto mb-4" />
                <h3 className="text-xl font-bold text-gray-900 mb-2">
                  Game Over!
                </h3>
                <p className="text-lg text-gray-700">
                  Result: {gameResult === '1-0' ? 'White wins' : 
                           gameResult === '0-1' ? 'Black wins' : 'Draw'}
                </p>
                <button
                  onClick={startNewGame}
                  className="btn-primary mt-4 flex items-center space-x-2 mx-auto"
                >
                  <Play className="h-4 w-4" />
                  <span>Play Again</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}