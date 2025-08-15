import { useEffect, useRef, useCallback } from 'react';
import { useAppStore } from '@/stores/appStore';
import { createWebSocketConnection } from '@/services/api';
import type { WebSocketMessage, ChatMessage } from '@/types';

interface UseWebSocketOptions {
  clientId: string;
  onMessage?: (message: WebSocketMessage) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
  reconnectAttempts?: number;
  reconnectDelay?: number;
}

export const useWebSocket = (options: UseWebSocketOptions) => {
  const {
    clientId,
    onMessage,
    onConnect,
    onDisconnect,
    onError,
    reconnectAttempts = 5,
    reconnectDelay = 3000,
  } = options;

  const { 
    setConnectionStatus, 
    setWsConnection, 
    addChatMessage, 
    setIsTyping,
    addError 
  } = useAppStore();
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const attemptsRef = useRef(0);
  const isConnectingRef = useRef(false);

  const connect = useCallback(() => {
    if (isConnectingRef.current || (wsRef.current && wsRef.current.readyState === WebSocket.OPEN)) {
      return;
    }

    isConnectingRef.current = true;
    setConnectionStatus({ websocket: 'connecting' });

    try {
      const ws = createWebSocketConnection(clientId);
      
      ws.onopen = () => {
        console.log('WebSocket connected');
        isConnectingRef.current = false;
        attemptsRef.current = 0;
        setConnectionStatus({ websocket: 'connected' });
        setWsConnection(ws);
        onConnect?.();
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          
          // Handle different message types
          switch (message.type) {
            case 'chat_response':
              addChatMessage({
                id: `${Date.now()}-assistant`,
                type: 'assistant',
                content: message.message || '',
                timestamp: message.timestamp,
                metadata: message.data,
              });
              break;
              
            case 'knowledge_response':
              addChatMessage({
                id: `${Date.now()}-system`,
                type: 'system',
                content: message.message || 'Knowledge query processed',
                timestamp: message.timestamp,
                metadata: message.data,
              });
              break;
              
            case 'typing':
              if (message.data?.status === 'start') {
                setIsTyping(true);
              } else if (message.data?.status === 'stop') {
                setIsTyping(false);
              }
              break;
              
            default:
              console.log('Received WebSocket message:', message);
          }
          
          onMessage?.(message);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
          addError('Failed to parse WebSocket message');
        }
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        isConnectingRef.current = false;
        setConnectionStatus({ websocket: 'disconnected' });
        setWsConnection(null);
        setIsTyping(false);
        onDisconnect?.();
        
        // Attempt reconnection
        if (attemptsRef.current < reconnectAttempts) {
          attemptsRef.current++;
          console.log(`Attempting to reconnect WebSocket (${attemptsRef.current}/${reconnectAttempts})`);
          reconnectTimeoutRef.current = setTimeout(connect, reconnectDelay);
        } else {
          console.error('Max WebSocket reconnection attempts reached');
          addError('WebSocket connection failed after multiple attempts');
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        isConnectingRef.current = false;
        setConnectionStatus({ websocket: 'error' });
        addError('WebSocket connection error');
        onError?.(error);
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      isConnectingRef.current = false;
      setConnectionStatus({ websocket: 'error' });
      addError('Failed to create WebSocket connection');
    }
  }, [
    clientId,
    onMessage,
    onConnect,
    onDisconnect,
    onError,
    reconnectAttempts,
    reconnectDelay,
    setConnectionStatus,
    setWsConnection,
    addChatMessage,
    setIsTyping,
    addError,
  ]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    
    attemptsRef.current = reconnectAttempts; // Prevent reconnection
    setConnectionStatus({ websocket: 'disconnected' });
    setWsConnection(null);
    setIsTyping(false);
  }, [reconnectAttempts, setConnectionStatus, setWsConnection, setIsTyping]);

  const sendMessage = useCallback((message: Partial<WebSocketMessage>) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      const fullMessage: WebSocketMessage = {
        type: 'chat',
        timestamp: new Date().toISOString(),
        client_id: clientId,
        ...message,
      };
      
      wsRef.current.send(JSON.stringify(fullMessage));
      return true;
    } else {
      console.error('WebSocket is not connected');
      addError('Cannot send message: WebSocket not connected');
      return false;
    }
  }, [clientId, addError]);

  const sendChatMessage = useCallback((content: string) => {
    if (sendMessage({ type: 'chat', message: content })) {
      // Add user message to chat
      addChatMessage({
        id: `${Date.now()}-user`,
        type: 'user',
        content,
        timestamp: new Date().toISOString(),
      });
    }
  }, [sendMessage, addChatMessage]);

  const sendKnowledgeQuery = useCallback((query: string) => {
    return sendMessage({ type: 'knowledge_query', message: query });
  }, [sendMessage]);

  // Connect on mount
  useEffect(() => {
    connect();
    
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    isConnected: wsRef.current?.readyState === WebSocket.OPEN,
    connect,
    disconnect,
    sendMessage,
    sendChatMessage,
    sendKnowledgeQuery,
  };
};