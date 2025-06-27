@@ .. @@
 import React, { useState, useEffect, useRef } from 'react';
-import io, { Socket } from 'socket.io-client';
+import { API_URL, WS_URL } from '../config/api';
 
 interface GameState {
@@ .. @@
 const HumanVsLLM: React.FC = () => {
   const [gameState, setGameState] = useState<GameState | null>(null);
   const [models, setModels] = useState<string[]>([]);
   const [selectedModel, setSelectedModel] = useState<string>('');
   const [playerColor, setPlayerColor] = useState<'white' | 'black'>('white');
   const [loading, setLoading] = useState(false);
   const [error, setError] = useState<string | null>(null);
-  const socketRef = useRef<Socket | null>(null);
+  const wsRef = useRef<WebSocket | null>(null);
 
   useEffect(() => {
     loadModels();
-    
-    // Initialize Socket.IO connection
-    socketRef.current = io('http://localhost:8000');
-    
-    socketRef.current.on('game_update', (data: GameState) => {
-      setGameState(data);
-    });
-    
-    socketRef.current.on('error', (error: string) => {
-      setError(error);
-    });
-    
-    return () => {
-      if (socketRef.current) {
-        socketRef.current.disconnect();
-      }
-    };
   }, []);
 
+  const connectWebSocket = () => {
+    if (wsRef.current) {
+      wsRef.current.close();
+    }
+
+    wsRef.current = new WebSocket(`${WS_URL}/ws`);
+    
+    wsRef.current.onopen = () => {
+      console.log('WebSocket connected');
+    };
+    
+    wsRef.current.onmessage = (event) => {
+      try {
+        const data = JSON.parse(event.data);
+        if (data.type === 'game_update') {
+          setGameState(data.data);
+        } else if (data.type === 'error') {
+          setError(data.message);
+        }
+      } catch (error) {
+        console.error('Error parsing WebSocket message:', error);
+      }
+    };
+    
+    wsRef.current.onerror = (error) => {
+      console.error('WebSocket error:', error);
+      setError('WebSocket connection error');
+    };
+    
+    wsRef.current.onclose = () => {
+      console.log('WebSocket disconnected');
+    };
+  };
+
   const loadModels = async () => {
     try {
-      const response = await fetch('http://localhost:8000/models');
+      const response = await fetch(`${API_URL}/models`);
       const data = await response.json();
       setModels(data.models);
       if (data.models.length > 0) {
@@ .. @@
   const startGame = async () => {
     try {
       setLoading(true);
-      const response = await fetch('http://localhost:8000/human-game/start', {
+      setError(null);
+      
+      // Connect WebSocket before starting game
+      connectWebSocket();
+      
+      const response = await fetch(`${API_URL}/human-game/start`, {
         method: 'POST',
         headers: {
           'Content-Type': 'application/json',
@@ .. @@
   const makeMove = async (move: string) => {
     try {
-      const response = await fetch('http://localhost:8000/human-game/move', {
+      const response = await fetch(`${API_URL}/human-game/move`, {
         method: 'POST',
         headers: {
           'Content-Type': 'application/json',
@@ .. @@
   const resetGame = async () => {
     try {
-      await fetch('http://localhost:8000/human-game/reset', {
+      await fetch(`${API_URL}/human-game/reset`, {
         method: 'POST',
       });
       setGameState(null);
+      if (wsRef.current) {
+        wsRef.current.close();
+      }
     } catch (error) {
       console.error('Error resetting game:', error);
     }
   };
+
+  // Cleanup WebSocket on unmount
+  useEffect(() => {
+    return () => {
+      if (wsRef.current) {
+        wsRef.current.close();
+      }
+    };
+  }, []);