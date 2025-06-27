import React, { useState, useEffect } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell } from 'recharts'
import { Trophy, TrendingUp, Target, Medal, Star, Award } from 'lucide-react'
import { endpoints } from '@/lib/api'
import { formatDate, calculateWinRate } from '@/lib/utils'
import { toast } from 'react-hot-toast'

interface ModelRanking {
  model: string
  elo: number
  games_played: number
  wins: number
  draws: number
  losses: number
  win_rate: number
  avg_accuracy: number
  recent_trend: number[]
}

interface EloHistory {
  model: string
  elo: number
  date: string
}

interface OpeningStats {
  opening: string
  games_played: number
  win_rate: number
  avg_accuracy: number
  avg_game_length: number
}

export default function Rankings() {
  const [selectedTab, setSelectedTab] = useState<'general' | 'detailed' | 'openings'>('general')
  const [rankings, setRankings] = useState<ModelRanking[]>([])
  const [eloHistory, setEloHistory] = useState<EloHistory[]>([])
  const [openingStats, setOpeningStats] = useState<OpeningStats[]>([])
  const [selectedModel, setSelectedModel] = useState<string>('')
  const [modelDetails, setModelDetails] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    loadRankingsData()
  }, [])

  const loadRankingsData = async () => {
    try {
      setLoading(true)
      
      // Load rankings
      const rankingsResponse = await endpoints.rankings.get()
      const rankingsData = rankingsResponse.data.rankings || []
      setRankings(rankingsData)
      
      if (rankingsData.length > 0) {
        setSelectedModel(rankingsData[0].model)
      }
      
      // Mock ELO history data
      const mockEloHistory: EloHistory[] = []
      rankingsData.forEach((ranking: ModelRanking) => {
        for (let i = 0; i < 10; i++) {
          mockEloHistory.push({
            model: ranking.model,
            elo: ranking.elo + (Math.random() - 0.5) * 100,
            date: new Date(Date.now() - (9 - i) * 24 * 60 * 60 * 1000).toISOString()
          })
        }
      })
      setEloHistory(mockEloHistory)
      
      // Mock opening stats
      const mockOpenings: OpeningStats[] = [
        { opening: "King's Pawn (e4)", games_played: 45, win_rate: 0.62, avg_accuracy: 87.5, avg_game_length: 42.3 },
        { opening: "Queen's Pawn (d4)", games_played: 38, win_rate: 0.58, avg_accuracy: 85.2, avg_game_length: 48.7 },
        { opening: "English Opening (c4)", games_played: 22, win_rate: 0.55, avg_accuracy: 83.8, avg_game_length: 51.2 },
        { opening: "Réti Opening (Nf3)", games_played: 18, win_rate: 0.61, avg_accuracy: 86.1, avg_game_length: 45.8 },
        { opening: "Nimzo-Larsen (b3)", games_played: 12, win_rate: 0.50, avg_accuracy: 82.4, avg_game_length: 39.6 }
      ]
      setOpeningStats(mockOpenings)
      
    } catch (error) {
      console.error('Error loading rankings data:', error)
      toast.error('Failed to load rankings data')
    } finally {
      setLoading(false)
    }
  }

  const loadModelDetails = async (modelName: string) => {
    try {
      setLoading(true)
      
      // Mock detailed model stats
      const mockDetails = {
        model_name: modelName,
        total_games: Math.floor(Math.random() * 100) + 20,
        wins: Math.floor(Math.random() * 50) + 10,
        draws: Math.floor(Math.random() * 20) + 5,
        losses: Math.floor(Math.random() * 30) + 5,
        current_elo: 1500 + Math.floor(Math.random() * 300),
        peak_elo: 1600 + Math.floor(Math.random() * 200),
        avg_accuracy: 80 + Math.random() * 15,
        by_color: {
          white: {
            wins: Math.floor(Math.random() * 25) + 5,
            draws: Math.floor(Math.random() * 10) + 2,
            losses: Math.floor(Math.random() * 15) + 2
          },
          black: {
            wins: Math.floor(Math.random() * 25) + 5,
            draws: Math.floor(Math.random() * 10) + 3,
            losses: Math.floor(Math.random() * 15) + 3
          }
        },
        recent_trend: Array.from({ length: 20 }, () => 80 + Math.random() * 15)
      }
      
      setModelDetails(mockDetails)
      
    } catch (error) {
      console.error('Error loading model details:', error)
      toast.error('Failed to load model details')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (selectedModel) {
      loadModelDetails(selectedModel)
    }
  }, [selectedModel])

  const getRankIcon = (rank: number) => {
    switch (rank) {
      case 1:
        return <Trophy className="h-6 w-6 text-yellow-500" />
      case 2:
        return <Medal className="h-6 w-6 text-gray-400" />
      case 3:
        return <Award className="h-6 w-6 text-amber-600" />
      default:
        return <Star className="h-6 w-6 text-gray-300" />
    }
  }

  const COLORS = ['#3b82f6', '#ef4444', '#f59e0b', '#10b981', '#8b5cf6']

  if (loading && rankings.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="loading-spinner" />
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Rankings & Statistics</h1>
        <p className="text-gray-600 mt-2">
          Model performance rankings, ELO ratings, and detailed statistics
        </p>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'general', name: 'General Rankings', icon: Trophy },
            { id: 'detailed', name: 'Detailed Stats', icon: TrendingUp },
            { id: 'openings', name: 'Opening Performance', icon: Target }
          ].map((tab) => {
            const Icon = tab.icon
            return (
              <button
                key={tab.id}
                onClick={() => setSelectedTab(tab.id as any)}
                className={`flex items-center space-x-2 py-2 px-1 border-b-2 font-medium text-sm ${
                  selectedTab === tab.id
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <Icon className="h-4 w-4" />
                <span>{tab.name}</span>
              </button>
            )
          })}
        </nav>
      </div>

      {/* Tab Content */}
      {selectedTab === 'general' && (
        <div className="space-y-8">
          {/* Rankings Table */}
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Model Rankings
            </h3>
            
            {rankings.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Rank
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Model
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        ELO Rating
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Games
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Win Rate
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Accuracy
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {rankings.map((ranking, index) => (
                      <tr key={ranking.model} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            {getRankIcon(index + 1)}
                            <span className="ml-2 text-sm font-medium text-gray-900">
                              #{index + 1}
                            </span>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-gray-900">
                            {ranking.model}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-bold text-primary-600">
                            {ranking.elo}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {ranking.games}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            <div className="w-16 bg-gray-200 rounded-full h-2 mr-2">
                              <div
                                className="bg-green-500 h-2 rounded-full"
                                style={{ width: `${ranking.win_rate * 100}%` }}
                              />
                            </div>
                            <span className="text-sm text-gray-900">
                              {(ranking.win_rate * 100).toFixed(1)}%
                            </span>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {ranking.avg_accuracy?.toFixed(1)}%
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <Trophy className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>No ranking data available</p>
                <p className="text-sm">Play more games to see rankings</p>
              </div>
            )}
          </div>

          {/* ELO Progression Chart */}
          {eloHistory.length > 0 && (
            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                ELO Rating Progression
              </h3>
              
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={eloHistory}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="date" 
                    tickFormatter={(date) => new Date(date).toLocaleDateString()}
                  />
                  <YAxis />
                  <Tooltip 
                    labelFormatter={(date) => new Date(date).toLocaleDateString()}
                  />
                  {rankings.slice(0, 5).map((ranking, index) => (
                    <Line
                      key={ranking.model}
                      type="monotone"
                      dataKey="elo"
                      data={eloHistory.filter(h => h.model === ranking.model)}
                      stroke={COLORS[index]}
                      name={ranking.model}
                      strokeWidth={2}
                    />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      )}

      {selectedTab === 'detailed' && (
        <div className="space-y-8">
          {/* Model Selection */}
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Detailed Model Statistics
            </h3>
            
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Model
              </label>
              <select
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
                className="w-full md:w-64 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                {rankings.map(ranking => (
                  <option key={ranking.model} value={ranking.model}>
                    {ranking.model}
                  </option>
                ))}
              </select>
            </div>

            {modelDetails && (
              <div className="space-y-6">
                {/* Key Metrics */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center p-4 bg-blue-50 rounded-lg">
                    <p className="text-2xl font-bold text-blue-600">
                      {modelDetails.total_games}
                    </p>
                    <p className="text-sm text-gray-600">Total Games</p>
                  </div>
                  <div className="text-center p-4 bg-green-50 rounded-lg">
                    <p className="text-2xl font-bold text-green-600">
                      {calculateWinRate(modelDetails.wins, modelDetails.total_games).toFixed(1)}%
                    </p>
                    <p className="text-sm text-gray-600">Win Rate</p>
                  </div>
                  <div className="text-center p-4 bg-purple-50 rounded-lg">
                    <p className="text-2xl font-bold text-purple-600">
                      {modelDetails.current_elo}
                    </p>
                    <p className="text-sm text-gray-600">Current ELO</p>
                  </div>
                  <div className="text-center p-4 bg-yellow-50 rounded-lg">
                    <p className="text-2xl font-bold text-yellow-600">
                      {modelDetails.avg_accuracy.toFixed(1)}%
                    </p>
                    <p className="text-sm text-gray-600">Avg Accuracy</p>
                  </div>
                </div>

                {/* Performance by Color */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="card">
                    <h4 className="text-md font-semibold text-gray-900 mb-4">
                      Performance by Color
                    </h4>
                    
                    <div className="space-y-4">
                      <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                        <span className="font-medium">White</span>
                        <div className="text-right">
                          <p className="text-sm text-gray-600">
                            {modelDetails.by_color.white.wins}W / 
                            {modelDetails.by_color.white.draws}D / 
                            {modelDetails.by_color.white.losses}L
                          </p>
                          <p className="text-xs text-gray-500">
                            {calculateWinRate(
                              modelDetails.by_color.white.wins,
                              modelDetails.by_color.white.wins + 
                              modelDetails.by_color.white.draws + 
                              modelDetails.by_color.white.losses
                            ).toFixed(1)}% win rate
                          </p>
                        </div>
                      </div>
                      
                      <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                        <span className="font-medium">Black</span>
                        <div className="text-right">
                          <p className="text-sm text-gray-600">
                            {modelDetails.by_color.black.wins}W / 
                            {modelDetails.by_color.black.draws}D / 
                            {modelDetails.by_color.black.losses}L
                          </p>
                          <p className="text-xs text-gray-500">
                            {calculateWinRate(
                              modelDetails.by_color.black.wins,
                              modelDetails.by_color.black.wins + 
                              modelDetails.by_color.black.draws + 
                              modelDetails.by_color.black.losses
                            ).toFixed(1)}% win rate
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="card">
                    <h4 className="text-md font-semibold text-gray-900 mb-4">
                      Recent Performance Trend
                    </h4>
                    
                    <ResponsiveContainer width="100%" height={200}>
                      <LineChart data={modelDetails.recent_trend.map((acc: number, index: number) => ({
                        game: index + 1,
                        accuracy: acc
                      }))}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="game" />
                        <YAxis domain={[70, 100]} />
                        <Tooltip />
                        <Line 
                          type="monotone" 
                          dataKey="accuracy" 
                          stroke="#3b82f6" 
                          strokeWidth={2}
                          dot={{ r: 3 }}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {selectedTab === 'openings' && (
        <div className="space-y-8">
          {/* Opening Statistics Table */}
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Opening Performance
            </h3>
            
            {openingStats.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Opening
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Games
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Win Rate
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Avg Accuracy
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Avg Length
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {openingStats.map((opening) => (
                      <tr key={opening.opening} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-gray-900">
                            {opening.opening}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {opening.games_played}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            <div className="w-16 bg-gray-200 rounded-full h-2 mr-2">
                              <div
                                className="bg-green-500 h-2 rounded-full"
                                style={{ width: `${opening.win_rate * 100}%` }}
                              />
                            </div>
                            <span className="text-sm text-gray-900">
                              {(opening.win_rate * 100).toFixed(1)}%
                            </span>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {opening.avg_accuracy.toFixed(1)}%
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {opening.avg_game_length.toFixed(1)} moves
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <Target className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>No opening data available</p>
                <p className="text-sm">Play more games to see opening statistics</p>
              </div>
            )}
          </div>

          {/* Opening Popularity Chart */}
          {openingStats.length > 0 && (
            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Opening Popularity
              </h3>
              
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={openingStats}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ opening, percent }) => `${opening.split(' ')[0]} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="games_played"
                  >
                    {openingStats.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      )}
    </div>
  )
}