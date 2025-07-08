// FindersKeepers v2 - WebSocket React Hook

import { useEffect, useRef, useCallback } from 'react';
import { wsService } from '@/services/websocket';
import { useAppStore } from '@/stores/appStore';

interface UseWebSocketOptions {
  autoConnect?: boolean;
  reconnectOnError?: boolean;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Error) => void;
}

export function useWebSocket(options: UseWebSocketOptions = {}) {
  const {
    reconnectOnError = true,
    onConnect,
    onDisconnect,
    onError,
  } = options;

  const setConnectionStatus = useAppStore(state => state.setConnectionStatus);
  const addRecentActivity = useAppStore(state => state.addRecentActivity);
  const addError = useAppStore(state => state.addError);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | undefined>(undefined);

  // Connection status handler
  const handleConnectionChange = useCallback((isConnected: boolean) => {
    setConnectionStatus('websocket', isConnected ? 'connected' : 'disconnected');
    
    if (isConnected) {
      onConnect?.();
    } else {
      onDisconnect?.();
      
      // Auto-reconnect logic
      if (reconnectOnError && !reconnectTimeoutRef.current) {
        reconnectTimeoutRef.current = setTimeout(() => {
          wsService.reconnect();
          reconnectTimeoutRef.current = undefined;
        }, 3000) as ReturnType<typeof setTimeout>;
      }
    }
  }, [setConnectionStatus, onConnect, onDisconnect, reconnectOnError]);

  // Error handler
  const handleError = useCallback((error: Error) => {
    setConnectionStatus('websocket', 'error');
    addError({
      code: 'WEBSOCKET_ERROR',
      message: error.message,
      timestamp: new Date().toISOString(),
      severity: 'medium',
      details: { error: error.toString() },
    });
    onError?.(error);
  }, [setConnectionStatus, addError, onError]);

  // Subscribe to specific events
  const subscribe = useCallback(<T = any>(
    event: string,
    callback: (data: T) => void,
  ) => {
    return wsService.on(event, callback);
  }, []);

  // Send data to server
  const send = useCallback((event: string, data: any) => {
    wsService.send(event, data);
  }, []);

  // Join/leave rooms
  const joinRoom = useCallback((room: string) => {
    wsService.joinRoom(room);
  }, []);

  const leaveRoom = useCallback((room: string) => {
    wsService.leaveRoom(room);
  }, []);

  // Session-specific subscriptions
  const subscribeToSession = useCallback((sessionId: string) => {
    wsService.subscribeToSession(sessionId);
  }, []);

  const unsubscribeFromSession = useCallback((sessionId: string) => {
    wsService.unsubscribeFromSession(sessionId);
  }, []);

  // Project-specific subscriptions
  const subscribeToProject = useCallback((projectName: string) => {
    wsService.subscribeToProject(projectName);
  }, []);

  const unsubscribeFromProject = useCallback((projectName: string) => {
    wsService.unsubscribeFromProject(projectName);
  }, []);

  // Connection health check
  const ping = useCallback(async (): Promise<number | null> => {
    try {
      return await wsService.ping();
    } catch (error) {
      console.error('WebSocket ping failed:', error);
      return null;
    }
  }, []);

  // Manual reconnect
  const reconnect = useCallback(() => {
    wsService.reconnect();
  }, []);

  // Setup event listeners on mount
  useEffect(() => {
    // Initialize WebSocket connection
    wsService.initialize();

    // Setup error handling
    const unsubscribeError = wsService.onError(handleError);

    // Monitor connection status
    const checkConnection = () => {
      handleConnectionChange(wsService.isConnected);
    };

    // Check initial status
    checkConnection();

    // Set up periodic connection checks
    const connectionCheckInterval = setInterval(checkConnection, 5000);

    return () => {
      unsubscribeError();
      clearInterval(connectionCheckInterval);
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [handleConnectionChange, handleError]);

  // Setup global event listeners for activity tracking
  useEffect(() => {
    const unsubscribeCallbacks: (() => void)[] = [];

    // Track session events
    unsubscribeCallbacks.push(
      wsService.on('session_start', (data) => {
        addRecentActivity({
          type: 'session_start',
          data,
          message: `New ${data.agent_type} session started`,
        });
      })
    );

    unsubscribeCallbacks.push(
      wsService.on('session_end', (data) => {
        addRecentActivity({
          type: 'session_end',
          data,
          message: `Session ${data.session_id} completed`,
        });
      })
    );

    unsubscribeCallbacks.push(
      wsService.on('action_completed', (data) => {
        addRecentActivity({
          type: 'action_completed',
          data,
          message: `Action ${data.action_type} completed`,
        });
      })
    );

    unsubscribeCallbacks.push(
      wsService.on('document_ingested', (data) => {
        addRecentActivity({
          type: 'document_ingested',
          data,
          message: `Document "${data.title}" ingested`,
        });
      })
    );

    unsubscribeCallbacks.push(
      wsService.on('system_alert', (data) => {
        addRecentActivity({
          type: 'system_alert',
          data,
          message: data.message || 'System alert',
        });
        
        // Add to errors if it's a critical alert
        if (data.severity === 'critical') {
          addError({
            code: 'SYSTEM_ALERT',
            message: data.message,
            timestamp: new Date().toISOString(),
            severity: data.severity,
            details: data,
          });
        }
      })
    );

    return () => {
      unsubscribeCallbacks.forEach(unsubscribe => unsubscribe());
    };
  }, [addRecentActivity, addError]);

  return {
    // Connection state
    isConnected: wsService.isConnected,
    connectionId: wsService.connectionId,
    
    // Event handling
    subscribe,
    send,
    
    // Room management
    joinRoom,
    leaveRoom,
    
    // Specific subscriptions
    subscribeToSession,
    unsubscribeFromSession,
    subscribeToProject,
    unsubscribeFromProject,
    
    // Connection management
    ping,
    reconnect,
  };
}

export default useWebSocket;