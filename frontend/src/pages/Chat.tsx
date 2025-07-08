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
  Chip,
  CircularProgress,
  Card,
  CardContent,
  Grid,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  FormControlLabel,
  Switch,
  Select,
  MenuItem,
  FormControl,
  InputLabel
} from '@mui/material';
import {
  Send as SendIcon,
  Person as PersonIcon,
  SmartToy as BotIcon,
  ExpandMore as ExpandMoreIcon,
  History as HistoryIcon,
  Psychology as PsychologyIcon,
  VectorSpace as VectorIcon
} from '@mui/icons-material';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
}

interface ChatSource {
  type: string;
  title: string;
  relevance: number;
  content?: string;
}

interface ChatResponse {
  message: string;
  conversation_id: string;
  sources: ChatSource[];
  model_used: string;
  response_time_ms: number;
  tokens_used: number;
}

interface Conversation {
  conversation_id: string;
  last_message: string;
  last_updated: string;
  message_count: number;
}

const Chat: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [lastResponse, setLastResponse] = useState<ChatResponse | null>(null);
  const [useKnowledgeGraph, setUseKnowledgeGraph] = useState(true);
  const [useVectorSearch, setUseVectorSearch] = useState(true);
  const [selectedModel, setSelectedModel] = useState('llama3.2:3b');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    loadConversations();
  }, []);

  const loadConversations = async () => {
    try {
      const response = await fetch('/api/chat/conversations');
      if (response.ok) {
        const data = await response.json();
        setConversations(data.conversations || []);
      }
    } catch (error) {
      console.error('Failed to load conversations:', error);
    }
  };

  const loadConversation = async (convId: string) => {
    try {
      const response = await fetch(`/api/chat/conversations/${convId}`);
      if (response.ok) {
        const data = await response.json();
        setMessages(data.messages || []);
        setConversationId(convId);
      }
    } catch (error) {
      console.error('Failed to load conversation:', error);
    }
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      role: 'user',
      content: inputMessage.trim(),
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMessage.content,
          conversation_id: conversationId,
          use_knowledge_graph: useKnowledgeGraph,
          use_vector_search: useVectorSearch,
          model: selectedModel,
          max_tokens: 1000
        }),
      });

      if (response.ok) {
        const chatResponse: ChatResponse = await response.json();
        
        const assistantMessage: ChatMessage = {
          role: 'assistant',
          content: chatResponse.message,
          timestamp: new Date().toISOString()
        };

        setMessages(prev => [...prev, assistantMessage]);
        setConversationId(chatResponse.conversation_id);
        setLastResponse(chatResponse);
        
        // Reload conversations list
        loadConversations();
      } else {
        const errorData = await response.json();
        const errorMessage: ChatMessage = {
          role: 'assistant',
          content: `Error: ${errorData.detail || 'Failed to get response'}`,
          timestamp: new Date().toISOString()
        };
        setMessages(prev => [...prev, errorMessage]);
      }
    } catch (error) {
      const errorMessage: ChatMessage = {
        role: 'assistant',
        content: 'Error: Unable to connect to the chat service.',
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  };

  const startNewConversation = () => {
    setMessages([]);
    setConversationId(null);
    setLastResponse(null);
  };

  const formatTimestamp = (timestamp?: string) => {
    if (!timestamp) return '';
    return new Date(timestamp).toLocaleTimeString();
  };

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <PsychologyIcon color="primary" />
        AI Chat Assistant
      </Typography>

      <Grid container spacing={3}>
        {/* Conversation History Sidebar */}
        <Grid item xs={12} md={3}>
          <Paper sx={{ p: 2, height: '70vh', overflow: 'auto' }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <HistoryIcon />
                Conversations
              </Typography>
              <Button size="small" onClick={startNewConversation}>
                New Chat
              </Button>
            </Box>
            
            <List dense>
              {conversations.map((conv) => (
                <ListItem
                  key={conv.conversation_id}
                  button
                  onClick={() => loadConversation(conv.conversation_id)}
                  selected={conversationId === conv.conversation_id}
                >
                  <Box>
                    <Typography variant="body2" noWrap>
                      {conv.last_message}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {conv.message_count} messages • {formatTimestamp(conv.last_updated)}
                    </Typography>
                  </Box>
                </ListItem>
              ))}
            </List>
          </Paper>
        </Grid>

        {/* Main Chat Area */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ display: 'flex', flexDirection: 'column', height: '70vh' }}>
            {/* Messages */}
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
                    <ListItem key={index} sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
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
                  {isLoading && (
                    <ListItem sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                      <Avatar sx={{ bgcolor: 'secondary.main' }}>
                        <BotIcon />
                      </Avatar>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <CircularProgress size={20} />
                        <Typography variant="body2" color="text.secondary">
                          Assistant is thinking...
                        </Typography>
                      </Box>
                    </ListItem>
                  )}
                </List>
              )}
              <div ref={messagesEndRef} />
            </Box>

            {/* Input Area */}
            <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider' }}>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <TextField
                  fullWidth
                  multiline
                  maxRows={4}
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Type your message... (Press Enter to send, Shift+Enter for new line)"
                  disabled={isLoading}
                />
                <Button
                  variant="contained"
                  onClick={sendMessage}
                  disabled={!inputMessage.trim() || isLoading}
                  sx={{ minWidth: 'auto', px: 2 }}
                >
                  <SendIcon />
                </Button>
              </Box>
            </Box>
          </Paper>
        </Grid>

        {/* Settings and Response Info */}
        <Grid item xs={12} md={3}>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {/* Chat Settings */}
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Chat Settings
              </Typography>
              
              <FormControl fullWidth size="small" sx={{ mb: 2 }}>
                <InputLabel>Model</InputLabel>
                <Select
                  value={selectedModel}
                  label="Model"
                  onChange={(e) => setSelectedModel(e.target.value)}
                >
                  <MenuItem value="llama3.2:3b">Llama 3.2 3B</MenuItem>
                  <MenuItem value="codestral">Codestral 7B</MenuItem>
                  <MenuItem value="qwen2.5:0.5b">Qwen 2.5 0.5B</MenuItem>
                </Select>
              </FormControl>

              <FormControlLabel
                control={
                  <Switch
                    checked={useKnowledgeGraph}
                    onChange={(e) => setUseKnowledgeGraph(e.target.checked)}
                  />
                }
                label="Use Knowledge Graph"
              />
              
              <FormControlLabel
                control={
                  <Switch
                    checked={useVectorSearch}
                    onChange={(e) => setUseVectorSearch(e.target.checked)}
                  />
                }
                label="Use Vector Search"
              />
            </Paper>

            {/* Response Information */}
            {lastResponse && (
              <Paper sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>
                  Response Info
                </Typography>
                
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary">
                    Model: {lastResponse.model_used}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Response time: {Math.round(lastResponse.response_time_ms)}ms
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Tokens: {lastResponse.tokens_used}
                  </Typography>
                </Box>

                {lastResponse.sources.length > 0 && (
                  <Accordion>
                    <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                      <Typography variant="subtitle2">
                        Sources ({lastResponse.sources.length})
                      </Typography>
                    </AccordionSummary>
                    <AccordionDetails>
                      {lastResponse.sources.map((source, index) => (
                        <Card key={index} sx={{ mb: 1 }}>
                          <CardContent sx={{ p: 1, '&:last-child': { pb: 1 } }}>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                              <Chip
                                size="small"
                                label={source.type}
                                color={source.type === 'knowledge' ? 'primary' : 'secondary'}
                              />
                              <Typography variant="caption">
                                {Math.round(source.relevance * 100)}% relevant
                              </Typography>
                            </Box>
                            <Typography variant="subtitle2" gutterBottom>
                              {source.title}
                            </Typography>
                            {source.content && (
                              <Typography variant="caption" color="text.secondary">
                                {source.content}
                              </Typography>
                            )}
                          </CardContent>
                        </Card>
                      ))}
                    </AccordionDetails>
                  </Accordion>
                )}
              </Paper>
            )}
          </Box>
        </Grid>
      </Grid>
    </Container>
  );
};

export default Chat;