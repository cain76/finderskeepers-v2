# Jest WebSocket Mock Testing Guide
**Date**: 07-09-2025  
**Source**: https://github.com/romgain/jest-websocket-mock  
**Version**: 2.5.0  
**Project**: FindersKeepers v2 - WebSocket Testing Implementation  

## Overview

Jest WebSocket Mock is a comprehensive testing utility for WebSocket interactions in React applications. Essential for testing the FindersKeepers v2 real-time chat functionality with proper mocking and assertions.

## Installation

```bash
npm install --save-dev jest-websocket-mock
```

## Basic Usage

### Mock WebSocket Server Setup

```javascript
import WS from "jest-websocket-mock";

// Create a mock WebSocket server
const server = new WS("ws://localhost:8000");

// Connect a real client
const client = new WebSocket("ws://localhost:8000");
await server.connected; // Wait for connection

// Client sends message
client.send("hello");

// Server sends message to all clients
server.send("hello everyone");

// Simulate error and close
server.error();
server.close();

// Clean up between tests
WS.clean();
```

### JSON Protocol Support

```javascript
// Enable automatic JSON serialization/deserialization
const server = new WS("ws://localhost:8000", { jsonProtocol: true });

// Send JSON messages
server.send({ type: "GREETING", payload: "hello" });

// Test JSON message reception
client.send(`{ "type": "GREETING", "payload": "hello" }`);
await expect(server).toReceiveMessage({ type: "GREETING", payload: "hello" });
```

## Custom Jest Matchers

### `.toReceiveMessage()` - Async Matcher

```javascript
test("server receives messages", async () => {
  const server = new WS("ws://localhost:8000");
  const client = new WebSocket("ws://localhost:8000");
  await server.connected;
  
  client.send("hello");
  await expect(server).toReceiveMessage("hello");
});
```

### `.toHaveReceivedMessages()` - Synchronous Matcher

```javascript
test("server tracks all received messages", async () => {
  const server = new WS("ws://localhost:8000");
  const client = new WebSocket("ws://localhost:8000");
  await server.connected;
  
  client.send("message1");
  client.send("message2");
  
  await expect(server).toReceiveMessage("message1");
  await expect(server).toReceiveMessage("message2");
  
  expect(server).toHaveReceivedMessages(["message1", "message2"]);
});
```

## WS Instance Attributes

### Connection Management

```javascript
const server = new WS("ws://localhost:8000");

// Promise that resolves when new connection is established
server.connected.then((socket) => {
  console.log("Client connected:", socket);
});

// Promise that resolves when connection is closed
server.closed.then(() => {
  console.log("Connection closed");
});

// Promise that resolves when new message is received
server.nextMessage.then((message) => {
  console.log("Received message:", message);
});
```

## Advanced Features

### Connection Verification

```javascript
test("reject unauthorized connections", async () => {
  const server = new WS("ws://localhost:8000", { 
    verifyClient: () => false 
  });
  
  const errorCallback = jest.fn();
  await expect(
    new Promise((resolve, reject) => {
      errorCallback.mockImplementation(reject);
      const client = new WebSocket("ws://localhost:8000");
      client.onerror = errorCallback;
      client.onopen = resolve;
    })
  ).rejects.toEqual(expect.objectContaining({ type: "error" }));
});
```

### Protocol Selection

```javascript
test("reject wrong protocol", async () => {
  const server = new WS("ws://localhost:8000", { 
    selectProtocol: () => null 
  });
  
  const errorCallback = jest.fn();
  await expect(
    new Promise((resolve, reject) => {
      errorCallback.mockImplementationOnce(reject);
      const client = new WebSocket("ws://localhost:8000", "invalid-protocol");
      client.onerror = errorCallback;
      client.onopen = resolve;
    })
  ).rejects.toEqual(
    expect.objectContaining({
      type: "error",
      currentTarget: expect.objectContaining({ protocol: "invalid-protocol" })
    })
  );
});
```

### Error Handling

```javascript
test("server sends errors to clients", async () => {
  const server = new WS("ws://localhost:8000");
  const client = new WebSocket("ws://localhost:8000");
  await server.connected;
  
  let disconnected = false;
  let error = null;
  
  client.onclose = () => {
    disconnected = true;
  };
  
  client.onerror = (e) => {
    error = e;
  };
  
  server.error();
  
  expect(disconnected).toBe(true);
  expect(error.origin).toBe("ws://localhost:8000/");
  expect(error.type).toBe("error");
});
```

### Custom Event Listeners

```javascript
test("server can refuse connections", async () => {
  const server = new WS("ws://localhost:8000");
  
  server.on("connection", (socket) => {
    socket.close({ wasClean: false, code: 1003, reason: "NOPE" });
  });
  
  const client = new WebSocket("ws://localhost:8000");
  
  client.onclose = (event) => {
    expect(event.code).toBe(1003);
    expect(event.wasClean).toBe(false);
    expect(event.reason).toBe("NOPE");
  };
  
  expect(client.readyState).toBe(WebSocket.CONNECTING);
  await server.connected;
  expect(client.readyState).toBe(WebSocket.CLOSING);
  await server.closed;
  expect(client.readyState).toBe(WebSocket.CLOSED);
});
```

## React Testing Integration

### Automatic React Testing Library Integration

```javascript
// jest-websocket-mock automatically wraps calls in act() if @testing-library/react is available
import { render, screen } from '@testing-library/react';
import WS from 'jest-websocket-mock';
import ChatComponent from './ChatComponent';

test('chat component handles WebSocket messages', async () => {
  const server = new WS("ws://localhost:8000");
  
  render(<ChatComponent />);
  
  // No need to manually wrap in act() - jest-websocket-mock handles it
  server.send({ type: 'chat_response', message: 'Hello from server' });
  
  expect(screen.getByText('Hello from server')).toBeInTheDocument();
});
```

## Test Setup and Teardown

### Setup Between Tests

```javascript
describe('WebSocket Chat Tests', () => {
  let server;
  let client;

  beforeEach(async () => {
    server = new WS("ws://localhost:8000");
    client = new WebSocket("ws://localhost:8000");
    await server.connected;
  });

  afterEach(() => {
    WS.clean(); // Clean up all connections
  });

  test('sends and receives messages', async () => {
    client.send("test message");
    await expect(server).toReceiveMessage("test message");
    
    server.send("server response");
    // Assert client received the message
  });
});
```

## FindersKeepers v2 Testing Examples

### Testing Chat Component

```javascript
import { render, screen, fireEvent } from '@testing-library/react';
import WS from 'jest-websocket-mock';
import ChatInterface from '../components/ChatInterface';

describe('ChatInterface', () => {
  let server;

  beforeEach(async () => {
    server = new WS("ws://localhost:8000/ws/user123", { jsonProtocol: true });
  });

  afterEach(() => {
    WS.clean();
  });

  test('sends chat message and receives AI response', async () => {
    render(<ChatInterface />);
    
    // Wait for connection
    await server.connected;
    
    // User types and sends message
    const input = screen.getByPlaceholderText('Type your message...');
    const sendButton = screen.getByText('Send');
    
    fireEvent.change(input, { target: { value: 'Hello AI' } });
    fireEvent.click(sendButton);
    
    // Verify message was sent to server
    await expect(server).toReceiveMessage({
      type: 'chat',
      message: 'Hello AI',
      timestamp: expect.any(String)
    });
    
    // Simulate AI response
    server.send({
      type: 'chat_response',
      message: 'Hello! How can I help you?',
      timestamp: new Date().toISOString()
    });
    
    // Verify AI response appears in UI
    expect(screen.getByText('Hello! How can I help you?')).toBeInTheDocument();
  });

  test('handles knowledge queries', async () => {
    render(<ChatInterface />);
    await server.connected;
    
    // Send knowledge query
    const input = screen.getByPlaceholderText('Type your message...');
    fireEvent.change(input, { target: { value: 'What is Docker?' } });
    fireEvent.click(screen.getByText('Send'));
    
    // Verify knowledge query was sent
    await expect(server).toReceiveMessage({
      type: 'knowledge_query',
      message: 'What is Docker?',
      timestamp: expect.any(String)
    });
    
    // Simulate knowledge response
    server.send({
      type: 'knowledge_response',
      message: 'Docker is a containerization platform...',
      timestamp: new Date().toISOString(),
      embeddings_count: 384
    });
    
    expect(screen.getByText(/Docker is a containerization platform/)).toBeInTheDocument();
  });

  test('handles connection errors', async () => {
    render(<ChatInterface />);
    await server.connected;
    
    // Simulate connection error
    server.error();
    
    // Verify error state is shown
    expect(screen.getByText('Disconnected')).toBeInTheDocument();
  });
});
```

### Testing WebSocket Hook

```javascript
import { renderHook, act } from '@testing-library/react';
import WS from 'jest-websocket-mock';
import { useWebSocket } from '../hooks/useWebSocket';

describe('useWebSocket Hook', () => {
  let server;

  beforeEach(() => {
    server = new WS("ws://localhost:8000/ws/user123", { jsonProtocol: true });
  });

  afterEach(() => {
    WS.clean();
  });

  test('connects and sends messages', async () => {
    const { result } = renderHook(() => 
      useWebSocket('ws://localhost:8000/ws/user123')
    );
    
    // Wait for connection
    await server.connected;
    
    // Check connection status
    expect(result.current.isConnected).toBe(true);
    
    // Send message using hook
    act(() => {
      result.current.sendMessage({
        type: 'chat',
        message: 'Test message'
      });
    });
    
    // Verify message was sent
    await expect(server).toReceiveMessage({
      type: 'chat',
      message: 'Test message'
    });
  });

  test('handles incoming messages', async () => {
    const { result } = renderHook(() => 
      useWebSocket('ws://localhost:8000/ws/user123')
    );
    
    await server.connected;
    
    // Send message from server
    act(() => {
      server.send({
        type: 'chat_response',
        message: 'Server message'
      });
    });
    
    // Verify message was received
    expect(result.current.messages).toContainEqual({
      type: 'chat_response',
      message: 'Server message'
    });
  });
});
```

## Best Practices

### 1. Always Clean Up

```javascript
afterEach(() => {
  WS.clean(); // Prevents test interference
});
```

### 2. Use JSON Protocol for Structured Data

```javascript
const server = new WS("ws://localhost:8000", { jsonProtocol: true });
```

### 3. Test Both Happy and Error Paths

```javascript
test('handles connection errors gracefully', async () => {
  const server = new WS("ws://localhost:8000");
  const client = new WebSocket("ws://localhost:8000");
  await server.connected;
  
  const errorHandler = jest.fn();
  client.onerror = errorHandler;
  
  server.error();
  
  expect(errorHandler).toHaveBeenCalled();
});
```

### 4. Mock Non-Global WebSocket Libraries

```javascript
// __mocks__/ws.js
export { WebSocket as default } from "mock-socket";
```

## Known Issues

1. **Fake Timers**: Don't use `jest.useFakeTimers()` with WebSocket tests
2. **setImmediate**: Add `require('setimmediate')` to setupTests.js if needed
3. **Node.js Libraries**: Use manual mocks for libraries like `ws`

## Required Dependencies

```json
{
  "devDependencies": {
    "jest-websocket-mock": "^2.5.0",
    "@testing-library/react": "^13.0.0",
    "@testing-library/jest-dom": "^5.16.0"
  }
}
```

## Integration with FindersKeepers v2

The FindersKeepers v2 project should use jest-websocket-mock for:

1. **Chat Interface Testing**: Mock the `/ws/{client_id}` endpoint
2. **Knowledge Query Testing**: Test knowledge_query and knowledge_response messages
3. **Connection Management**: Test reconnection and error handling
4. **Real-time Features**: Test typing indicators and online status

## Next Steps

1. Add jest-websocket-mock to devDependencies
2. Create test utilities for common WebSocket scenarios
3. Write comprehensive tests for chat functionality
4. Test integration with Ollama AI responses
5. Add tests for knowledge graph queries