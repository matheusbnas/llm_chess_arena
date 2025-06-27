import React from 'react'
import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Arena from './pages/Arena'
import Analysis from './pages/Analysis'
import Rankings from './pages/Rankings'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/arena" element={<Arena />} />
        <Route path="/analysis" element={<Analysis />} />
        <Route path="/rankings" element={<Rankings />} />
      </Routes>
    </Layout>
  )
}

export default App