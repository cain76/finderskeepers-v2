# Building a Real-time Chat Application with React and WebSocket

Source: https://dev.to/amarondev/building-a-real-time-chat-application-with-react-and-websocket-3138

## Introduction

In today's digital age, real-time communication is at the forefront of web development. Whether you're creating a social networking platform, a customer support system, or just want to add some chat functionality to your website, building a real-time chat application is a valuable skill for any React developer. In this tutorial, we will take you through the process of building a real-time chat application using React and WebSocket, allowing you to engage with users instantly.

### What is WebSocket?

Before we dive into the development process, let's briefly understand what WebSocket is. WebSocket is a protocol that enables full-duplex communication channels over a single TCP connection. Unlike traditional HTTP requests, which are stateless and require a new connection for each request, WebSocket allows for continuous, bidirectional communication between the client and server. This makes it perfect for building real-time applications like chat systems.

## Prerequisites

Before we start coding, ensure you have the following tools and technologies installed:

1. Node.js and npm (Node Package Manager)
2. Create React App (CRA) - You can install it globally by running `npm install -g create-react-app`.

## Setting Up the React Application

Let's start by creating a new React application using Create React App. Open your terminal and run the following command:

```bash
npx create-react-app real-time-chat-app
```

This command will set up a new React project named "real-time-chat-app." Once the setup is complete, navigate to the project directory using:

```bash
cd real-time-chat-app
```

## Adding WebSocket Support

Now, we need to add WebSocket support to our React application. We'll use the popular "WebSocket" package for this purpose. Install it by running:

```bash
npm install websocket
```

## Creating a WebSocket Server

To establish WebSocket communication, we need a server that can handle WebSocket connections. For simplicity, we'll create a WebSocket server using Node.js. Create a new file named "server.js" in your project directory and add the following code:

```javascript
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
 });
 
 connection.on('close', (reasonCode, description) => {
  // Handle WebSocket connection closure here
 });
});

server.listen(3001, () => {
 console.log('WebSocket server is listening on port 3001');
});
```

This code sets up an HTTP server and a WebSocket server on port 3001. You can customize the port as needed.

## Creating the React Chat Interface

Now that we have the WebSocket server in place, let's create the chat interface in our React application. Replace the contents of "src/App.js" with the following code:

```javascript
import React, { useState } from 'react';
import './App.css';

function App() {
 const [messages, setMessages] = useState([]);
 const [messageInput, setMessageInput] = useState('');
 
 // WebSocket connection setup goes here
 
 const sendMessage = () => {
  // Implement sending messages via WebSocket here
 };
 
 return (
  <div className="App">
   <div className="chat-container">
    <div className="chat-messages">
     {messages.map((message, index) => (
      <div key={index} className="message">
       {message}
      </div>
     ))}
    </div>
    <div className="chat-input">
     <input
      type="text"
      placeholder="Type your message..."
      value={messageInput}
      onChange={(e) => setMessageInput(e.target.value)}
     />
     <button onClick={sendMessage}>Send</button>
    </div>
   </div>
  </div>
 );
}

export default App;
```

This code sets up a basic chat interface with an input field and a send button. We're using React state to manage the messages and the message input field.

## Connecting React to the WebSocket Server

To establish a connection between our React app and the WebSocket server, add the following code inside the "App" component:

```javascript
import { useEffect } from 'react';

// ...

useEffect(() => {
 const socket = new WebSocket('ws://localhost:3001');
 
 socket.onopen = () => {
  console.log('WebSocket connection established.');
 };
 
 socket.onmessage = (event) => {
  const receivedMessage = JSON.parse(event.data);
  setMessages([...messages, receivedMessage]);
 };
 
 return () => {
  socket.close();
 };
}, [messages]);
```

This code initializes a WebSocket connection to the server and handles incoming messages. When a message is received, it's parsed and added to the list of messages using the `setMessages` function.

## Sending Messages

Now, let's implement the `sendMessage` function to send messages to the WebSocket server:

```javascript
const sendMessage = () => {
 if (messageInput.trim() !== '') {
  const message = {
   text: messageInput,
   timestamp: new Date().toISOString(),
  };
  socket.send(JSON.stringify(message));
  setMessageInput('');
 }
};
```

This code checks if the message input is not empty, creates a message object with the text and a timestamp, and sends it to the server as a JSON string.

## Styling the Chat Interface

Feel free to add CSS styles to make your chat interface visually appealing. You can create a CSS file or use a CSS framework like Bootstrap to style your components.

## Conclusion

Congratulations! You've just built a real-time chat application using React and WebSocket. This tutorial covers the fundamental steps to create a basic chat interface and establish a WebSocket connection. There's plenty of room for customization and enhancements, such as user authentication, message persistence, and user presence indicators.

Real-time chat applications are essential in today's interconnected world, and the skills you've gained from this tutorial will serve as a strong foundation for building more sophisticated real-time applications. Happy coding!

## Key Takeaways for FindersKeepers v2:

1. **WebSocket Connection Management**: Use useEffect to establish WebSocket connections
2. **Message Handling**: Parse JSON messages and update state accordingly
3. **Connection Cleanup**: Always close WebSocket connections in useEffect cleanup
4. **Message Sending**: Structure messages with metadata like timestamps
5. **State Management**: Use React state to manage messages and UI state