import React, { createContext, useContext, useEffect, useState, ReactNode, useRef } from 'react';
import { io, Socket } from 'socket.io-client';
import { WebSocketMessage } from '@/types/api';

interface WebSocketContextType {
  socket: Socket | null;
  isConnected: boolean;
  lastMessage: WebSocketMessage | null;
  sendMessage: (message: any) => void;
  subscribe: (event: string, callback: (data: any) => void) => void;
  unsubscribe: (event: string, callback?: (data: any) => void) => void;
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined);

interface WebSocketProviderProps {
  children: ReactNode;
}

export const WebSocketProvider: React.FC<WebSocketProviderProps> = ({ children }) => {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const callbacksRef = useRef<Map<string, Set<(data: any) => void>>>(new Map());

  useEffect(() => {
    // Initialize WebSocket connection
    const newSocket = io(process.env.REACT_APP_WS_URL || 'ws://localhost:8000', {
      transports: ['websocket'],
      autoConnect: true,
    });

    newSocket.on('connect', () => {
      console.log('WebSocket connected');
      setIsConnected(true);
    });

    newSocket.on('disconnect', () => {
      console.log('WebSocket disconnected');
      setIsConnected(false);
    });

    newSocket.on('connect_error', (error) => {
      console.error('WebSocket connection error:', error);
      setIsConnected(false);
    });

    // Listen for dashboard updates
    newSocket.on('metrics_update', (data) => {
      const message: WebSocketMessage = {
        type: 'metrics_update',
        data,
        timestamp: new Date().toISOString(),
      };
      setLastMessage(message);
      notifyCallbacks('metrics_update', data);
    });

    // Listen for monitoring updates
    newSocket.on('monitoring_update', (data) => {
      const message: WebSocketMessage = {
        type: 'monitoring_update',
        data,
        timestamp: new Date().toISOString(),
      };
      setLastMessage(message);
      notifyCallbacks('monitoring_update', data);
    });

    // Listen for alerts
    newSocket.on('alert', (data) => {
      const message: WebSocketMessage = {
        type: 'alert',
        data,
        timestamp: new Date().toISOString(),
      };
      setLastMessage(message);
      notifyCallbacks('alert', data);
    });

    // Listen for notifications
    newSocket.on('notification', (data) => {
      const message: WebSocketMessage = {
        type: 'notification',
        data,
        timestamp: new Date().toISOString(),
      };
      setLastMessage(message);
      notifyCallbacks('notification', data);
    });

    // Listen for errors
    newSocket.on('error', (data) => {
      const message: WebSocketMessage = {
        type: 'error',
        data,
        timestamp: new Date().toISOString(),
      };
      setLastMessage(message);
      notifyCallbacks('error', data);
    });

    setSocket(newSocket);

    return () => {
      newSocket.close();
    };
  }, []);

  const notifyCallbacks = (event: string, data: any) => {
    const callbacks = callbacksRef.current.get(event);
    if (callbacks) {
      callbacks.forEach(callback => callback(data));
    }
  };

  const sendMessage = (message: any) => {
    if (socket && isConnected) {
      socket.emit('message', message);
    }
  };

  const subscribe = (event: string, callback: (data: any) => void) => {
    if (!callbacksRef.current.has(event)) {
      callbacksRef.current.set(event, new Set());
    }
    callbacksRef.current.get(event)!.add(callback);
  };

  const unsubscribe = (event: string, callback?: (data: any) => void) => {
    const callbacks = callbacksRef.current.get(event);
    if (callbacks && callback) {
      callbacks.delete(callback);
    } else if (callbacks) {
      callbacks.clear();
    }
  };

  const value: WebSocketContextType = {
    socket,
    isConnected,
    lastMessage,
    sendMessage,
    subscribe,
    unsubscribe,
  };

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
};

export const useWebSocket = (): WebSocketContextType => {
  const context = useContext(WebSocketContext);
  if (context === undefined) {
    throw new Error('useWebSocket must be used within a WebSocketProvider');
  }
  return context;
};
