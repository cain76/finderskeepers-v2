# React WebSocket Chat Implementation Guide
**Date**: 07-09-2025  
**Source**: https://dev.to/amarondev/building-a-real-time-chat-application-with-react-and-websocket-3138  
**Author**: Amar Gupta  
**Project**: FindersKeepers v2 - Chat Interface Implementation  

## Overview

Complete guide for building real-time chat applications with React and WebSocket. Essential for implementing the FindersKeepers v2 chat interface with real-time messaging capabilities.

## What is WebSocket?

WebSocket is a protocol that enables full-duplex communication channels over a single TCP connection. Unlike traditional HTTP requests, WebSocket allows for continuous, bidirectional communication between client and server - perfect for real-time chat applications.

## Prerequisites

- Node.js and npm
- Basic knowledge of React and Hooks
- Understanding of JavaScript ES6+ features

## Setup Instructions

### 1. Create React Application
```bash
npx create-react-app real-time-chat-app
cd real-time-chat-app
```

### 2. Install WebSocket Support
```bash
npm install websocket
```

## WebSocket Server Implementation

### Basic Node.js WebSocket Server
```javascript
// server.js
const WebSocket = require('websocket').server;
const http = require('http');

const server = http.createServer((request, response) => {
  // Handle HTTP requests here
});

const webSocketServer = new WebSocket({
  httpServer: server,
});

webSocketServer.on('request', (request) => {
  const connection = request.accept(null, request.origin);
  
  connection.on('message', (message) => {
    // Handle incoming WebSocket messages here
    console.log('Received message:', message);
    
    // Broadcast to all connected clients
    // (Implementation depends on your architecture)
  });
  
  connection.on('close', (reasonCode, description) => {
    // Handle WebSocket connection closure here
    console.log('Connection closed:', reasonCode, description);
  });
});

server.listen(3001, () => {
  console.log('WebSocket server is listening on port 3001');
});
```

## React Chat Interface Implementation

### Main App Component
```jsx
// src/App.js
import React, { useState, useEffect, useRef } from 'react';
import './App.css';

function App() {
  const [messages, setMessages] = useState([]);
  const [messageInput, setMessageInput] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const socketRef = useRef(null);

  useEffect(() => {
    // WebSocket connection setup
    const socket = new WebSocket('ws://localhost:8000/ws/user123');
    socketRef.current = socket;

    socket.onopen = () => {
      console.log('WebSocket connection established.');
      setIsConnected(true);
    };

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'chat_response') {
        setMessages(prevMessages => [...prevMessages, {
          id: Date.now(),
          text: data.message,
          sender: 'ai',
          timestamp: data.timestamp
        }]);
      }
    };

    socket.onclose = () => {
      console.log('WebSocket connection closed.');
      setIsConnected(false);
    };

    socket.onerror = (error) => {
      console.error('WebSocket error:', error);
      setIsConnected(false);
    };

    return () => {
      socket.close();
    };
  }, []);

  const sendMessage = () => {
    if (messageInput.trim() !== '' && isConnected) {
      const message = {
        type: 'chat',
        message: messageInput,
        timestamp: new Date().toISOString(),
      };

      // Add user message to UI immediately
      setMessages(prevMessages => [...prevMessages, {
        id: Date.now(),
        text: messageInput,
        sender: 'user',
        timestamp: new Date().toISOString()
      }]);

      // Send to WebSocket server
      socketRef.current.send(JSON.stringify(message));
      setMessageInput('');
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="App">
      <div className="chat-container">
        <div className="connection-status">
          <span className={`status-indicator ${isConnected ? 'connected' : 'disconnected'}`}>
            {isConnected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
        
        <div className="chat-messages">
          {messages.map((message) => (
            <div key={message.id} className={`message ${message.sender}`}>
              <div className="message-content">
                {message.text}
              </div>
              <div className="message-timestamp">
                {new Date(message.timestamp).toLocaleTimeString()}
              </div>
            </div>
          ))}
        </div>
        
        <div className="chat-input">
          <input
            type="text"
            placeholder="Type your message..."
            value={messageInput}
            onChange={(e) => setMessageInput(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={!isConnected}
          />
          <button onClick={sendMessage} disabled={!isConnected}>
            Send
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;
```

## Custom Hook for WebSocket Management

### useWebSocket Hook
```jsx
// hooks/useWebSocket.js
import { useState, useEffect, useRef, useCallback } from 'react';

export const useWebSocket = (url) => {
  const [socket, setSocket] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [messages, setMessages] = useState([]);
  const [error, setError] = useState(null);
  const socketRef = useRef(null);

  useEffect(() => {
    const connectWebSocket = () => {
      try {
        const ws = new WebSocket(url);
        socketRef.current = ws;

        ws.onopen = () => {
          setIsConnected(true);
          setError(null);
          console.log('WebSocket connected');
        };

        ws.onmessage = (event) => {
          const data = JSON.parse(event.data);
          setMessages(prev => [...prev, data]);
        };

        ws.onclose = () => {
          setIsConnected(false);
          console.log('WebSocket disconnected');
        };

        ws.onerror = (error) => {
          setError(error);
          console.error('WebSocket error:', error);
        };

        setSocket(ws);
      } catch (err) {
        setError(err);
      }
    };

    connectWebSocket();

    return () => {
      if (socketRef.current) {
        socketRef.current.close();
      }
    };
  }, [url]);

  const sendMessage = useCallback((message) => {
    if (socketRef.current && isConnected) {
      socketRef.current.send(JSON.stringify(message));
    }
  }, [isConnected]);

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  return {
    socket,
    isConnected,
    messages,
    error,
    sendMessage,
    clearMessages
  };
};
```

## Enhanced Chat Component with Hook

### Using Custom Hook
```jsx
// components/ChatInterface.js
import React, { useState } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';

const ChatInterface = () => {
  const [messageInput, setMessageInput] = useState('');
  const { isConnected, messages, sendMessage, error } = useWebSocket('ws://localhost:8000/ws/user123');

  const handleSendMessage = () => {
    if (messageInput.trim() !== '') {
      sendMessage({
        type: 'chat',
        message: messageInput,
        timestamp: new Date().toISOString()
      });
      setMessageInput('');
    }
  };

  if (error) {
    return (
      <div className="error-container">
        <h3>Connection Error</h3>
        <p>{error.message}</p>
      </div>
    );
  }

  return (
    <div className="chat-interface">
      <div className="message-list">
        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.type}`}>
            <span className="message-text">{msg.message}</span>
            <span className="message-time">
              {new Date(msg.timestamp).toLocaleTimeString()}
            </span>
          </div>
        ))}
      </div>
      
      <div className="input-container">
        <input
          type="text"
          value={messageInput}
          onChange={(e) => setMessageInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
          placeholder="Type your message..."
          disabled={!isConnected}
        />
        <button onClick={handleSendMessage} disabled={!isConnected}>
          Send
        </button>
      </div>
      
      <div className="connection-status">
        Status: {isConnected ? 'Connected' : 'Disconnected'}
      </div>
    </div>
  );
};

export default ChatInterface;
```

## FindersKeepers v2 Integration

### Message Types for Knowledge System
```javascript
// Message type definitions
const MESSAGE_TYPES = {
  CHAT: 'chat',
  KNOWLEDGE_QUERY: 'knowledge_query',
  CHAT_RESPONSE: 'chat_response',
  KNOWLEDGE_RESPONSE: 'knowledge_response',
  TYPING: 'typing',
  ONLINE_STATUS: 'online_status'
};

// Enhanced message sending
const sendKnowledgeQuery = (query) => {
  const message = {
    type: MESSAGE_TYPES.KNOWLEDGE_QUERY,
    message: query,
    timestamp: new Date().toISOString(),
    client_id: 'user123'
  };
  
  sendMessage(message);
};
```

### Advanced Features Implementation

#### 1. Typing Indicators
```jsx
const [isTyping, setIsTyping] = useState(false);
const [typingTimeout, setTypingTimeout] = useState(null);

const handleTyping = () => {
  if (!isTyping) {
    setIsTyping(true);
    sendMessage({
      type: 'typing',
      status: 'start',
      client_id: 'user123'
    });
  }

  // Clear existing timeout
  if (typingTimeout) {
    clearTimeout(typingTimeout);
  }

  // Set new timeout
  const timeout = setTimeout(() => {
    setIsTyping(false);
    sendMessage({
      type: 'typing',
      status: 'stop',
      client_id: 'user123'
    });
  }, 2000);

  setTypingTimeout(timeout);
};
```

#### 2. Connection Recovery
```jsx
const [reconnectAttempts, setReconnectAttempts] = useState(0);
const maxReconnectAttempts = 5;

const reconnectWebSocket = useCallback(() => {
  if (reconnectAttempts < maxReconnectAttempts) {
    setTimeout(() => {
      setReconnectAttempts(prev => prev + 1);
      // Reconnect logic here
    }, 1000 * Math.pow(2, reconnectAttempts)); // Exponential backoff
  }
}, [reconnectAttempts]);
```

## CSS Styling Example

```css
/* App.css */
.chat-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  max-width: 800px;
  margin: 0 auto;
  border: 1px solid #ddd;
  border-radius: 8px;
  overflow: hidden;
}

.connection-status {
  padding: 10px;
  background-color: #f5f5f5;
  border-bottom: 1px solid #ddd;
  text-align: center;
}

.status-indicator {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: bold;
}

.status-indicator.connected {
  background-color: #4CAF50;
  color: white;
}

.status-indicator.disconnected {
  background-color: #f44336;
  color: white;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background-color: #fafafa;
}

.message {
  margin-bottom: 15px;
  padding: 10px;
  border-radius: 8px;
  max-width: 70%;
}

.message.user {
  background-color: #007bff;
  color: white;
  margin-left: auto;
  text-align: right;
}

.message.ai {
  background-color: #e9ecef;
  color: #333;
  margin-right: auto;
}

.message-content {
  margin-bottom: 5px;
}

.message-timestamp {
  font-size: 12px;
  opacity: 0.7;
}

.chat-input {
  display: flex;
  padding: 20px;
  background-color: white;
  border-top: 1px solid #ddd;
}

.chat-input input {
  flex: 1;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  margin-right: 10px;
}

.chat-input button {
  padding: 10px 20px;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.chat-input button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}
```

## Best Practices

1. **Error Handling**: Always implement proper error handling for WebSocket connections
2. **Connection Management**: Handle connection drops and implement reconnection logic
3. **Message Validation**: Validate incoming messages before processing
4. **Performance**: Use React.memo and useMemo for expensive operations
5. **Security**: Implement proper authentication and message validation
6. **User Experience**: Show connection status and typing indicators

## Security Considerations

- Validate all incoming messages
- Implement authentication before establishing connections
- Use HTTPS/WSS in production
- Sanitize user input to prevent XSS attacks
- Implement rate limiting to prevent spam

## Integration with FindersKeepers v2

The existing FastAPI backend already includes WebSocket support at `/ws/{client_id}` endpoint. The React frontend needs to:

1. Connect to the WebSocket endpoint
2. Handle `chat_response` and `knowledge_response` message types
3. Integrate with the existing Material-UI chat interface
4. Connect to the knowledge graph and vector search systems

## Next Steps

1. Implement the WebSocket hook in the existing React app
2. Update the current chat interface to use real-time WebSocket communication
3. Add typing indicators and connection status
4. Integrate with the existing FastAPI WebSocket endpoint
5. Add error handling and reconnection logic