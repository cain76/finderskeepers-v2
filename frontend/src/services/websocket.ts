// FindersKeepers v2 - WebSocket Service

import { io, Socket } from 'socket.io-client';

type EventCallback = (data: any) => void;
type ErrorCallback = (error: Error) => void;

class WebSocketService {
  private socket: Socket | null = null;
  private eventCallbacks: Map<string, EventCallback[]> = new Map();
  private errorCallbacks: ErrorCallback[] = [];
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectInterval = 1000;

  constructor() {
    // Don't auto-connect to prevent startup errors
    // Connection will be established when needed
  }

  private connect(): void {
    try {
      // Connect to FastAPI WebSocket endpoint
      this.socket = io('ws://localhost:8000', {
        transports: ['websocket'],
        upgrade: false,
        rememberUpgrade: false,
        autoConnect: true,
        reconnection: true,
        reconnectionAttempts: this.maxReconnectAttempts,
        reconnectionDelay: this.reconnectInterval,
      });

      this.setupEventHandlers();
    } catch (error) {
      console.error('WebSocket connection failed:', error);
      this.handleError(error as Error);
    }
  }

  private setupEventHandlers(): void {
    if (!this.socket) return;

    this.socket.on('connect', () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
    });

    this.socket.on('disconnect', (reason: string) => {
      console.log('WebSocket disconnected:', reason);
      
      if (reason === 'io server disconnect') {
        // Manual disconnect by server, reconnect manually
        this.socket?.connect();
      }
    });

    this.socket.on('connect_error', (error: Error) => {
      console.error('WebSocket connection error:', error);
      this.reconnectAttempts++;
      
      if (this.reconnectAttempts >= this.maxReconnectAttempts) {
        console.error('Max reconnection attempts reached');
        this.handleError(new Error('WebSocket connection failed after maximum attempts'));
      }
    });

    // Listen for real-time events
    this.socket.on('agent_session_start', (data: any) => {
      this.emit('session_start', data);
    });

    this.socket.on('agent_session_end', (data: any) => {
      this.emit('session_end', data);
    });

    this.socket.on('agent_action_completed', (data: any) => {
      this.emit('action_completed', data);
    });

    this.socket.on('document_ingested', (data: any) => {
      this.emit('document_ingested', data);
    });

    this.socket.on('system_alert', (data: any) => {
      this.emit('system_alert', data);
    });

    this.socket.on('health_update', (data: any) => {
      this.emit('health_update', data);
    });

    this.socket.on('performance_metrics', (data: any) => {
      this.emit('performance_metrics', data);
    });
  }

  // Subscribe to specific events
  on(event: string, callback: EventCallback): () => void {
    if (!this.eventCallbacks.has(event)) {
      this.eventCallbacks.set(event, []);
    }
    
    this.eventCallbacks.get(event)!.push(callback);

    // Return unsubscribe function
    return () => {
      const callbacks = this.eventCallbacks.get(event);
      if (callbacks) {
        const index = callbacks.indexOf(callback);
        if (index > -1) {
          callbacks.splice(index, 1);
        }
      }
    };
  }

  // Emit events to subscribers
  private emit(event: string, data: any): void {
    const callbacks = this.eventCallbacks.get(event);
    if (callbacks) {
      callbacks.forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`Error in event callback for ${event}:`, error);
        }
      });
    }
  }

  // Subscribe to error events
  onError(callback: ErrorCallback): () => void {
    this.errorCallbacks.push(callback);

    return () => {
      const index = this.errorCallbacks.indexOf(callback);
      if (index > -1) {
        this.errorCallbacks.splice(index, 1);
      }
    };
  }

  private handleError(error: Error): void {
    this.errorCallbacks.forEach(callback => {
      try {
        callback(error);
      } catch (err) {
        console.error('Error in error callback:', err);
      }
    });
  }

  // Send data to server
  send(event: string, data: any): void {
    if (this.socket?.connected) {
      this.socket.emit(event, data);
    } else {
      console.warn('WebSocket not connected, cannot send data');
    }
  }

  // Join specific rooms for targeted updates
  joinRoom(room: string): void {
    this.send('join_room', { room });
  }

  leaveRoom(room: string): void {
    this.send('leave_room', { room });
  }

  // Subscribe to session-specific updates
  subscribeToSession(sessionId: string): void {
    this.joinRoom(`session_${sessionId}`);
  }

  unsubscribeFromSession(sessionId: string): void {
    this.leaveRoom(`session_${sessionId}`);
  }

  // Subscribe to project-specific updates
  subscribeToProject(projectName: string): void {
    this.joinRoom(`project_${projectName}`);
  }

  unsubscribeFromProject(projectName: string): void {
    this.leaveRoom(`project_${projectName}`);
  }

  // Connection status
  get isConnected(): boolean {
    return this.socket?.connected ?? false;
  }

  get connectionId(): string | undefined {
    return this.socket?.id;
  }

  // Initialize connection (can be called safely multiple times)
  initialize(): void {
    if (!this.socket) {
      this.connect();
    }
  }

  // Manually reconnect
  reconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket.connect();
    } else {
      this.connect();
    }
  }

  // Clean disconnect
  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
    this.eventCallbacks.clear();
    this.errorCallbacks.length = 0;
  }

  // Ping server for connection health check
  ping(): Promise<number> {
    return new Promise((resolve, reject) => {
      if (!this.socket?.connected) {
        reject(new Error('WebSocket not connected'));
        return;
      }

      const start = Date.now();
      
      this.socket.timeout(5000).emit('ping', (error: any) => {
        if (error) {
          reject(error);
        } else {
          resolve(Date.now() - start);
        }
      });
    });
  }
}

// Export singleton instance
export const wsService = new WebSocketService();
export default wsService;