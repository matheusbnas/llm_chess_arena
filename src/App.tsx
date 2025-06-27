import React from 'react'
import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Arena from './pages/Arena'
import Analysis from './pages/Analysis'
import Rankings from './pages/Rankings'
import Settings from './pages/Settings'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/arena" element={<Arena />} />
        <Route path="/analysis" element={<Analysis />} />
        <Route path="/rankings" element={<Rankings />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </Layout>
  )
}

export default App