const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const path = require('path');
const cors = require('cors');
require('dotenv').config();

const gameRoutes = require('./routes/games');
const modelRoutes = require('./routes/models');
const analysisRoutes = require('./routes/analysis');
const lichessRoutes = require('./routes/lichess');

const app = express();
const server = http.createServer(app);
const io = socketIo(server, {
  cors: {
    origin: "*",
    methods: ["GET", "POST"]
  }
});

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// Routes
app.use('/api/games', gameRoutes);
app.use('/api/models', modelRoutes);
app.use('/api/analysis', analysisRoutes);
app.use('/api/lichess', lichessRoutes);

// Serve main page
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Socket.IO for real-time game updates
io.on('connection', (socket) => {
  console.log('User connected:', socket.id);
  
  socket.on('join-game', (gameId) => {
    socket.join(gameId);
    console.log(`User ${socket.id} joined game ${gameId}`);
  });
  
  socket.on('move-made', (data) => {
    socket.to(data.gameId).emit('move-update', data);
  });
  
  socket.on('disconnect', () => {
    console.log('User disconnected:', socket.id);
  });
});

const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
  console.log(`🚀 LLM Chess Arena running on port ${PORT}`);
  console.log(`📱 Open http://localhost:${PORT} in your browser`);
});