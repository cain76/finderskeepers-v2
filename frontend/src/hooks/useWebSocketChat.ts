import { useState, useEffect, useRef, useCallback } from 'react';

export interface ChatMessage {
  type: 'chat' | 'knowledge_query' | 'chat_response' | 'knowledge_response';
  message: string;
  timestamp: string;
  client_id?: string;
  embeddings_count?: number;
  sender?: 'user' | 'ai';
  id?: string;
}

export interface UseWebSocketChatOptions {
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  debug?: boolean;
}

export interface UseWebSocketChatReturn {
  socket: WebSocket | null;
  isConnected: boolean;
  messages: ChatMessage[];
  error: string | null;
  sendChatMessage: (message: string) => void;
  sendKnowledgeQuery: (query: string) => void;
  clearMessages: () => void;
  reconnect: () => void;
}

export const useWebSocketChat = (
  clientId: string,
  options: UseWebSocketChatOptions = {}
): UseWebSocketChatReturn => {
  const {
    reconnectInterval = 3000,
    maxReconnectAttempts = 5,
    debug = false
  } = options;

  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);

  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const log = useCallback((message: string) => {
    if (debug) {
      console.log(`[WebSocket] ${message}`);
    }
  }, [debug]);

  // Get WebSocket URL from environment or use default
  const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';
  const url = `${wsUrl}/ws/${clientId}`;

  const connect = useCallback(() => {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      log('Already connected');
      return;
    }

    try {
      log(`Connecting to ${url}`);
      const ws = new WebSocket(url);
      socketRef.current = ws;

      ws.onopen = () => {
        log('Connected');
        setIsConnected(true);
        setError(null);
        setReconnectAttempts(0);
        setSocket(ws);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as ChatMessage;
          log(`Received: ${data.type} - ${data.message.substring(0, 50)}...`);
          
          // Add AI sender flag for responses
          if (data.type === 'chat_response' || data.type === 'knowledge_response') {
            data.sender = 'ai';
          }
          
          // Add unique ID if not present
          if (!data.id) {
            data.id = `msg_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
          }

          setMessages(prev => [...prev, data]);
        } catch (err) {
          log(`Failed to parse message: ${err}`);
          setError('Failed to parse incoming message');
        }
      };

      ws.onclose = (event) => {
        log(`Disconnected: ${event.code} ${event.reason}`);
        setIsConnected(false);
        setSocket(null);
        socketRef.current = null;

        // Attempt to reconnect if not a normal closure
        if (event.code !== 1000 && reconnectAttempts < maxReconnectAttempts) {
          const timeout = setTimeout(() => {
            log(`Reconnecting... (${reconnectAttempts + 1}/${maxReconnectAttempts})`);
            setReconnectAttempts(prev => prev + 1);
            connect();
          }, reconnectInterval);
          reconnectTimeoutRef.current = timeout;
        }
      };

      ws.onerror = (event) => {
        log(`Error: ${event}`);
        setError('WebSocket connection error');
        setIsConnected(false);
      };

    } catch (err) {
      log(`Connection failed: ${err}`);
      setError(`Failed to connect: ${err}`);
    }
  }, [url, reconnectAttempts, maxReconnectAttempts, reconnectInterval, log]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (socketRef.current) {
      log('Disconnecting');
      socketRef.current.close(1000, 'Manual disconnect');
      socketRef.current = null;
    }

    setSocket(null);
    setIsConnected(false);
    setReconnectAttempts(0);
  }, [log]);

  const sendMessage = useCallback((message: ChatMessage) => {
    if (!socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
      log('Cannot send message - not connected');
      setError('Cannot send message - not connected');
      return;
    }

    try {
      const messageString = JSON.stringify(message);
      socketRef.current.send(messageString);
      log(`Sent: ${message.type} - ${message.message.substring(0, 50)}...`);
      
      // Add user message to local state immediately
      const userMessage: ChatMessage = {
        ...message,
        sender: 'user',
        id: `msg_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`
      };
      setMessages(prev => [...prev, userMessage]);
    } catch (err) {
      log(`Failed to send message: ${err}`);
      setError(`Failed to send message: ${err}`);
    }
  }, [log]);

  const sendChatMessage = useCallback((message: string) => {
    const chatMessage: ChatMessage = {
      type: 'chat',
      message,
      timestamp: new Date().toISOString(),
      client_id: clientId
    };
    sendMessage(chatMessage);
  }, [sendMessage, clientId]);

  const sendKnowledgeQuery = useCallback((query: string) => {
    const knowledgeMessage: ChatMessage = {
      type: 'knowledge_query',
      message: query,
      timestamp: new Date().toISOString(),
      client_id: clientId
    };
    sendMessage(knowledgeMessage);
  }, [sendMessage, clientId]);

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  const reconnect = useCallback(() => {
    disconnect();
    setReconnectAttempts(0);
    setTimeout(connect, 100);
  }, [disconnect, connect]);

  useEffect(() => {
    connect();
    return disconnect;
  }, [connect, disconnect]);

  return {
    socket,
    isConnected,
    messages,
    error,
    sendChatMessage,
    sendKnowledgeQuery,
    clearMessages,
    reconnect
  };
};