import React, { useEffect, useState } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { TrendingUp, Users, Trophy, Clock } from 'lucide-react'
import { endpoints } from '@/lib/api'
import { formatDate } from '@/lib/utils'

interface DashboardStats {
  totalGames: number
  activeModels: number
  avgGameLength: number
  tournamentsCompleted: number
}

interface RecentGame {
  id: string
  white: string
  black: string
  result: string
  moves: number
  date: string
}

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [recentGames, setRecentGames] = useState<RecentGame[]>([])
  const [chartData, setChartData] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const [statsRes, recentRes, chartRes] = await Promise.all([
          endpoints.dashboard.getStats(),
          endpoints.dashboard.getRecentGames(10),
          endpoints.dashboard.getChartData(),
        ])

        setStats(statsRes.data)
        setRecentGames(recentRes.data)
        setChartData(chartRes.data)
      } catch (error) {
        console.error('Error fetching dashboard data:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchDashboardData()
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="loading-spinner" />
      </div>
    )
  }

  const COLORS = ['#3b82f6', '#ef4444', '#f59e0b', '#10b981']

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600 mt-2">
          Overview of your LLM Chess Arena activity
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="metric-card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-white/80 text-sm">Total Games</p>
              <p className="text-3xl font-bold text-white">
                {stats?.totalGames || 0}
              </p>
            </div>
            <Trophy className="h-8 w-8 text-white/80" />
          </div>
        </div>

        <div className="metric-card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-white/80 text-sm">Active Models</p>
              <p className="text-3xl font-bold text-white">
                {stats?.activeModels || 0}
              </p>
            </div>
            <Users className="h-8 w-8 text-white/80" />
          </div>
        </div>

        <div className="metric-card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-white/80 text-sm">Avg Game Length</p>
              <p className="text-3xl font-bold text-white">
                {stats?.avgGameLength?.toFixed(1) || 0}
              </p>
            </div>
            <Clock className="h-8 w-8 text-white/80" />
          </div>
        </div>

        <div className="metric-card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-white/80 text-sm">Tournaments</p>
              <p className="text-3xl font-bold text-white">
                {stats?.tournamentsCompleted || 0}
              </p>
            </div>
            <TrendingUp className="h-8 w-8 text-white/80" />
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Results by Model */}
        {chartData?.modelResults && Array.isArray(chartData.modelResults) && chartData.modelResults.length > 0 && (
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Results by Model
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={chartData.modelResults}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="model" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="wins" fill="#3b82f6" name="Wins" />
                <Bar dataKey="draws" fill="#f59e0b" name="Draws" />
                <Bar dataKey="losses" fill="#ef4444" name="Losses" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Win Rate Distribution */}
        {chartData?.winRateData && Array.isArray(chartData.winRateData) && chartData.winRateData.length > 0 && (
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Win Rate Distribution
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={chartData.winRateData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {chartData.winRateData.map((entry: any, index: number) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Recent Games */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Recent Games
        </h3>
        
        {recentGames.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Players
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Result
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Moves
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Date
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {recentGames.map((game) => (
                  <tr key={game.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">
                        {game.white} vs {game.black}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        game.result === '1-0' ? 'bg-green-100 text-green-800' :
                        game.result === '0-1' ? 'bg-red-100 text-red-800' :
                        'bg-yellow-100 text-yellow-800'
                      }`}>
                        {game.result === '1-0' ? 'White wins' :
                         game.result === '0-1' ? 'Black wins' : 'Draw'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {game.moves}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatDate(game.date)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            <Trophy className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>No games played yet</p>
            <p className="text-sm">Start a battle in the Arena to see games here</p>
          </div>
        )}
      </div>
    </div>
  )
}