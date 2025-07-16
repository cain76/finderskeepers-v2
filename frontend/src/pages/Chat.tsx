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
  CircularProgress,
  Collapse,
  FormControlLabel,
  Switch,
  Slider,
  IconButton,
  Chip
} from '@mui/material';
import {
  Send as SendIcon,
  Person as PersonIcon,
  SmartToy as BotIcon,
  WifiOff as DisconnectedIcon,
  Wifi as ConnectedIcon,
  Settings as SettingsIcon,
  Speed as SpeedIcon
} from '@mui/icons-material';

interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp?: string;
  id?: string;
  type?: 'message' | 'url_suggestion' | 'scrape_status' | 'scrape_result';
  urls?: string[];
  scrapeData?: any;
}

const Chat: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: 'assistant', content: 'Hello! I am your AI assistant. How can I help you today?' }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [wsError, setWsError] = useState<string | null>(null);
  const [isThinking, setIsThinking] = useState(false);
  
  // URL scraping state
  const [detectedUrls, setDetectedUrls] = useState<string[]>([]);
  const [isScraping, setIsScraping] = useState(false);
  const [scrapeProgress, setScrapeProgress] = useState(0);
  const [scrapeStatus, setScrapeStatus] = useState<string>('');
  const [showUrlSuggestions, setShowUrlSuggestions] = useState(false);
  const [scrapeDelay, setScrapeDelay] = useState(2000); // 2 second delay between requests
  const [respectRobots, setRespectRobots] = useState(true);
  const [showThrottleSettings, setShowThrottleSettings] = useState(false);
  
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
          } else if (data.type === 'url_detected') {
            // Handle URL detection
            setDetectedUrls(data.urls?.map((u: any) => u.url) || []);
            setShowUrlSuggestions(true);
            setMessages(prev => [...prev, {
              role: 'system',
              content: data.message,
              timestamp: data.timestamp,
              id: `url_detect_${Date.now()}`,
              type: 'url_suggestion',
              urls: data.urls?.map((u: any) => u.url) || []
            }]);
          } else if (data.type === 'scrape_started') {
            // Handle scraping started
            setIsScraping(true);
            setScrapeProgress(0);
            setScrapeStatus(data.message);
            setShowUrlSuggestions(false);
            setMessages(prev => [...prev, {
              role: 'system',
              content: data.message,
              timestamp: data.timestamp,
              id: `scrape_start_${Date.now()}`,
              type: 'scrape_status'
            }]);
          } else if (data.type === 'scrape_progress') {
            // Handle scraping progress
            setScrapeProgress(data.progress || 0);
            setScrapeStatus(data.message);
            // Update the last scrape status message instead of adding new ones
            setMessages(prev => {
              const updated = [...prev];
              const lastIndex = updated.length - 1;
              if (lastIndex >= 0 && updated[lastIndex].type === 'scrape_status') {
                updated[lastIndex] = {
                  ...updated[lastIndex],
                  content: data.message,
                  timestamp: data.timestamp
                };
              } else {
                updated.push({
                  role: 'system',
                  content: data.message,
                  timestamp: data.timestamp,
                  id: `scrape_progress_${Date.now()}`,
                  type: 'scrape_status'
                });
              }
              return updated;
            });
          } else if (data.type === 'scrape_completed') {
            // Handle scraping completion
            setIsScraping(false);
            setScrapeProgress(100);
            setScrapeStatus('Scraping completed!');
            setMessages(prev => [...prev, {
              role: 'system',
              content: data.message,
              timestamp: data.timestamp,
              id: `scrape_complete_${Date.now()}`,
              type: 'scrape_result',
              scrapeData: {
                totalUrls: data.total_urls,
                successfulScrapes: data.successful_scrapes,
                failedScrapes: data.failed_scrapes,
                results: data.results
              }
            }]);
          } else if (data.type === 'scrape_error') {
            // Handle scraping errors
            setIsScraping(false);
            setScrapeStatus('Scraping failed');
            setMessages(prev => [...prev, {
              role: 'system',
              content: `❌ ${data.message}`,
              timestamp: data.timestamp,
              id: `scrape_error_${Date.now()}`,
              type: 'scrape_result'
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

  const handleUrlScraping = async (urls: string[], options: any = {}) => {
    if (!isConnected || !wsRef.current) return;
    
    try {
      const scrapeMessage = {
        type: 'url_scrape',
        urls: urls,
        project: 'finderskeepers-v2',
        tags: ['web-scraped', 'throttled'],
        scrape_options: {
          delay_between_requests: scrapeDelay,
          respect_robots_txt: respectRobots,
          user_agent: 'FindersKeepers-v2-Bot/1.0 (Respectful scraper)',
          timeout: 30000,
          max_retries: 2,
          ...options
        }
      };
      
      wsRef.current.send(JSON.stringify(scrapeMessage));
      console.log('Sent URL scraping request:', scrapeMessage);
      
    } catch (error) {
      console.error('Error sending URL scraping request:', error);
      setMessages(prev => [...prev, {
        role: 'system',
        content: `❌ Failed to start URL scraping: ${error}`,
        timestamp: new Date().toISOString(),
        id: `error_${Date.now()}`,
        type: 'scrape_result'
      }]);
    }
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
                      <Avatar sx={{ bgcolor: message.role === 'user' ? 'primary.main' : message.role === 'system' ? 'info.main' : 'secondary.main' }}>
                        {message.role === 'user' ? <PersonIcon /> : <BotIcon />}
                      </Avatar>
                      <Box sx={{ flex: 1 }}>
                        <Typography variant="caption" color="text.secondary">
                          {message.role === 'user' ? 'You' : message.role === 'system' ? 'System' : 'Assistant'} • {formatTimestamp(message.timestamp)}
                        </Typography>
                        
                        {/* Regular message content */}
                        <Typography variant="body1" sx={{ mt: 0.5, whiteSpace: 'pre-wrap' }}>
                          {message.content}
                        </Typography>
                        
                        {/* URL Suggestions */}
                        {message.type === 'url_suggestion' && message.urls && (
                          <Box sx={{ mt: 2 }}>
                            <Typography variant="subtitle2" sx={{ mb: 1 }}>
                              📎 Detected URLs:
                            </Typography>
                            {message.urls.map((url, urlIndex) => (
                              <Box key={urlIndex} sx={{ 
                                display: 'flex', 
                                alignItems: 'center', 
                                gap: 1, 
                                mb: 1,
                                p: 1,
                                border: '1px solid',
                                borderColor: 'primary.light',
                                borderRadius: 1,
                                bgcolor: 'background.paper'
                              }}>
                                <Typography variant="body2" sx={{ flex: 1, wordBreak: 'break-all' }}>
                                  {url}
                                </Typography>
                                <Button
                                  size="small"
                                  variant="contained"
                                  onClick={() => handleUrlScraping([url])}
                                  disabled={isScraping}
                                >
                                  Scrape
                                </Button>
                              </Box>
                            ))}
                            <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
                              <Button
                                variant="contained"
                                color="primary"
                                onClick={() => handleUrlScraping(message.urls || [])}
                                disabled={isScraping}
                              >
                                Scrape All URLs
                              </Button>
                              <Button
                                variant="outlined"
                                onClick={() => setShowUrlSuggestions(false)}
                              >
                                Dismiss
                              </Button>
                            </Box>
                          </Box>
                        )}
                        
                        {/* Scraping Progress */}
                        {message.type === 'scrape_status' && isScraping && (
                          <Box sx={{ mt: 2 }}>
                            <Typography variant="body2" sx={{ mb: 1 }}>
                              {scrapeStatus}
                            </Typography>
                            <Box sx={{ width: '100%', mb: 1 }}>
                              <CircularProgress 
                                variant="determinate" 
                                value={scrapeProgress} 
                                size={24}
                                sx={{ mr: 1 }}
                              />
                              <Typography variant="caption" color="text.secondary">
                                {Math.round(scrapeProgress)}%
                              </Typography>
                            </Box>
                          </Box>
                        )}
                        
                        {/* Scraping Results */}
                        {message.type === 'scrape_result' && message.scrapeData && (
                          <Box sx={{ mt: 2, p: 2, bgcolor: 'success.light', borderRadius: 1 }}>
                            <Typography variant="subtitle2" sx={{ mb: 1 }}>
                              📊 Scraping Results:
                            </Typography>
                            <Typography variant="body2">
                              • Total URLs: {message.scrapeData.totalUrls}
                            </Typography>
                            <Typography variant="body2">
                              • Successful: {message.scrapeData.successfulScrapes}
                            </Typography>
                            <Typography variant="body2">
                              • Failed: {message.scrapeData.failedScrapes}
                            </Typography>
                            {message.scrapeData.results && message.scrapeData.results.length > 0 && (
                              <Box sx={{ mt: 1 }}>
                                <Typography variant="caption" color="text.secondary">
                                  Check your knowledge base for the ingested content!
                                </Typography>
                              </Box>
                            )}
                          </Box>
                        )}
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
          <Paper sx={{ p: 2, mb: 2 }}>
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

          <Paper sx={{ p: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
              <Typography variant="h6" gutterBottom sx={{ m: 0 }}>
                URL Scraping Settings
              </Typography>
              <IconButton
                onClick={() => setShowThrottleSettings(!showThrottleSettings)}
                size="small"
              >
                <SettingsIcon />
              </IconButton>
            </Box>
            
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
              <SpeedIcon color="action" />
              <Chip 
                label={`${scrapeDelay}ms delay`} 
                size="small" 
                color={scrapeDelay >= 2000 ? 'success' : 'warning'}
              />
              <Chip 
                label={respectRobots ? 'Respects robots.txt' : 'Ignores robots.txt'} 
                size="small" 
                color={respectRobots ? 'success' : 'warning'}
              />
            </Box>

            <Collapse in={showThrottleSettings}>
              <Box sx={{ mt: 2 }}>
                <Typography variant="body2" sx={{ mb: 2, color: 'text.secondary' }}>
                  Configure scraping behavior to avoid being blocked by websites
                </Typography>
                
                <Box sx={{ mb: 3 }}>
                  <Typography variant="body2" sx={{ mb: 1 }}>
                    Delay between requests: {scrapeDelay}ms
                  </Typography>
                  <Slider
                    value={scrapeDelay}
                    onChange={(_, value) => setScrapeDelay(value as number)}
                    min={500}
                    max={10000}
                    step={500}
                    marks={[
                      { value: 500, label: '0.5s' },
                      { value: 2000, label: '2s' },
                      { value: 5000, label: '5s' },
                      { value: 10000, label: '10s' }
                    ]}
                    valueLabelDisplay="auto"
                    color={scrapeDelay >= 2000 ? 'success' : 'warning'}
                  />
                  <Typography variant="caption" color={scrapeDelay < 2000 ? 'warning.main' : 'text.secondary'}>
                    {scrapeDelay < 2000 ? 
                      '⚠️ Fast scraping may get you blocked' : 
                      '✅ Respectful scraping speed'
                    }
                  </Typography>
                </Box>

                <FormControlLabel
                  control={
                    <Switch
                      checked={respectRobots}
                      onChange={(e) => setRespectRobots(e.target.checked)}
                      color="success"
                    />
                  }
                  label="Respect robots.txt"
                />
                <Typography variant="caption" display="block" color="text.secondary">
                  Follow site crawling guidelines when available
                </Typography>
              </Box>
            </Collapse>
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
};

export default Chat;