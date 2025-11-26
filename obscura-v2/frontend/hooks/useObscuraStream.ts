import { useEffect, useRef, useState } from 'react';

type WebSocketMessage = {
  type: 'trade_update' | 'proof_update';
  data: any;
  timestamp: number;
};

export const useObscuraStream = (userId: string) => {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!userId) return;

    // Connect to Backend WebSocket
    // Assuming backend is running on localhost:8000
    const wsUrl = `ws://localhost:8000/ws/${userId}`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('Connected to Obscura Stream');
      setIsConnected(true);
    };

    ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        setLastMessage(message);
      } catch (err) {
        console.error('Failed to parse WS message:', err);
      }
    };

    ws.onclose = () => {
      console.log('Disconnected from Obscura Stream');
      setIsConnected(false);
    };

    ws.onerror = (err) => {
      console.error('WebSocket Error:', err);
    };

    wsRef.current = ws;

    return () => {
      ws.close();
    };
  }, [userId]);

  return { isConnected, lastMessage };
};
