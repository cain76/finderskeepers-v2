import React, { useState, useRef, useEffect } from 'react';
import {
  Container,
  Paper,
  Typography,
  Box,
  TextField,
  Button,
  List,
  ListItem,
  Avatar,
  Grid,
  Alert,
  CircularProgress
} from '@mui/material';
import {
  Send as SendIcon,
  Person as PersonIcon,
  SmartToy as BotIcon,
  WifiOff as DisconnectedIcon,
  Wifi as ConnectedIcon
} from '@mui/icons-material';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
  id?: string;
}

const Chat: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: 'assistant', content: 'Hello! I am your AI assistant. How can I help you today?' }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [wsError, setWsError] = useState<string | null>(null);
  const [isThinking, setIsThinking] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // WebSocket connection
  const wsRef = useRef<WebSocket | null>(null);
  
  useEffect(() => {
    const clientId = `chat_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
    const wsUrl = `ws://localhost:8000/ws/${clientId}`;
    
    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;
      
      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setWsError(null);
      };
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('Received message:', data);
          
          if (data.type === 'chat_response' || data.type === 'knowledge_response') {
            setIsThinking(false);
            setMessages(prev => [...prev, {
              role: 'assistant',
              content: data.message,
              timestamp: data.timestamp,
              id: data.id || `msg_${Date.now()}`
            }]);
          }
        } catch (error) {
          console.error('Error parsing message:', error);
        }
      };
      
      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setWsError('WebSocket connection error');
        setIsConnected(false);
      };
      
      return () => {
        ws.close();
      };
      
    } catch (error) {
      console.error('WebSocket creation error:', error);
      setWsError('Failed to create WebSocket connection');
    }
  }, []);

  const sendMessage = () => {
    if (!inputMessage.trim() || !isConnected || !wsRef.current) return;

    const userMessage: ChatMessage = {
      role: 'user',
      content: inputMessage.trim(),
      timestamp: new Date().toISOString(),
      id: `msg_${Date.now()}`
    };

    // Add user message to display immediately
    setMessages(prev => [...prev, userMessage]);
    
    // Send message via WebSocket to backend (Ollama)
    try {
      const messageData = {
        type: 'chat',
        message: inputMessage.trim(),
        timestamp: new Date().toISOString()
      };
      
      wsRef.current.send(JSON.stringify(messageData));
      console.log('Sent message to WebSocket:', messageData);
      
      // Show thinking indicator
      setIsThinking(true);
      
    } catch (error) {
      console.error('Error sending WebSocket message:', error);
      setWsError('Failed to send message');
    }
    
    setInputMessage('');
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  };

  const formatTimestamp = (timestamp?: string) => {
    if (!timestamp) return '';
    return new Date(timestamp).toLocaleTimeString();
  };

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <BotIcon color="primary" />
        AI Chat Assistant
        {isConnected ? (
          <ConnectedIcon color="success" sx={{ ml: 1 }} />
        ) : (
          <DisconnectedIcon color="error" sx={{ ml: 1 }} />
        )}
      </Typography>

      {!isConnected && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          WebSocket disconnected. {wsError && `Error: ${wsError}`}
        </Alert>
      )}

      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Paper sx={{ display: 'flex', flexDirection: 'column', height: '70vh' }}>
            <Box sx={{ flex: 1, overflow: 'auto', p: 2 }}>
              {messages.length === 0 ? (
                <Box sx={{ textAlign: 'center', mt: 4 }}>
                  <BotIcon sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
                  <Typography variant="h6" color="text.secondary">
                    Welcome to FindersKeepers AI Assistant
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Ask me about your system, documents, or anything else!
                  </Typography>
                </Box>
              ) : (
                <List>
                  {messages.map((message, index) => (
                    <ListItem key={message.id || index} sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
                      <Avatar sx={{ bgcolor: message.role === 'user' ? 'primary.main' : 'secondary.main' }}>
                        {message.role === 'user' ? <PersonIcon /> : <BotIcon />}
                      </Avatar>
                      <Box sx={{ flex: 1 }}>
                        <Typography variant="caption" color="text.secondary">
                          {message.role === 'user' ? 'You' : 'Assistant'} • {formatTimestamp(message.timestamp)}
                        </Typography>
                        <Typography variant="body1" sx={{ mt: 0.5, whiteSpace: 'pre-wrap' }}>
                          {message.content}
                        </Typography>
                      </Box>
                    </ListItem>
                  ))}
                  {isThinking && (
                    <ListItem sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                      <Avatar sx={{ bgcolor: 'secondary.main' }}>
                        <BotIcon />
                      </Avatar>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <CircularProgress size={20} />
                        <Typography variant="body2" color="text.secondary">
                          AI is thinking...
                        </Typography>
                      </Box>
                    </ListItem>
                  )}
                </List>
              )}
              <div ref={messagesEndRef} />
            </Box>

            <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider' }}>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <TextField
                  fullWidth
                  multiline
                  maxRows={4}
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder={isConnected ? "Type your message... (Press Enter to send)" : "Connecting to chat service..."}
                  disabled={!isConnected}
                />
                <Button
                  variant="contained"
                  onClick={sendMessage}
                  disabled={!inputMessage.trim() || !isConnected}
                  sx={{ minWidth: 'auto', px: 2 }}
                >
                  <SendIcon />
                </Button>
              </Box>
            </Box>
          </Paper>
        </Grid>

        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Connection Status
            </Typography>
            <Typography variant="body2" color={isConnected ? 'success.main' : 'error.main'}>
              {isConnected ? 'Connected to WebSocket' : 'Disconnected'}
            </Typography>
            {wsError && (
              <Typography variant="body2" color="error.main" sx={{ mt: 1 }}>
                Error: {wsError}
              </Typography>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
};

export default Chat;