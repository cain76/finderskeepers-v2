import { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline, Container, Paper, Typography, Box, TextField, Button } from '@mui/material';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
  },
});

function Dashboard() {
  return <div style={{padding: '20px'}}><h1>Dashboard</h1><p>Welcome to FindersKeepers v2!</p></div>;
}


function Chat() {
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hello! I am your AI assistant. How can I help you today?' }
  ]);

  const sendMessage = () => {
    if (!message.trim()) return;
    
    setMessages(prev => [...prev, 
      { role: 'user', content: message },
      { role: 'assistant', content: 'This is a test response. The backend is not connected yet.' }
    ]);
    setMessage('');
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        AI Chat Assistant
      </Typography>
      
      <Paper sx={{ height: '500px', display: 'flex', flexDirection: 'column' }}>
        <Box sx={{ flex: 1, overflow: 'auto', p: 2 }}>
          {messages.map((msg, index) => (
            <Box key={index} sx={{ mb: 2, textAlign: msg.role === 'user' ? 'right' : 'left' }}>
              <Typography variant="caption" color="text.secondary">
                {msg.role === 'user' ? 'You' : 'Assistant'}
              </Typography>
              <Typography variant="body1" sx={{ 
                background: msg.role === 'user' ? '#1976d2' : '#f5f5f5',
                color: msg.role === 'user' ? 'white' : 'black',
                padding: '8px 12px', 
                borderRadius: '8px', 
                display: 'inline-block',
                maxWidth: '70%'
              }}>
                {msg.content}
              </Typography>
            </Box>
          ))}
        </Box>
        
        <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider', display: 'flex', gap: 1 }}>
          <TextField
            fullWidth
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
            placeholder="Type your message..."
          />
          <Button variant="contained" onClick={sendMessage}>
            Send
          </Button>
        </Box>
      </Paper>
    </Container>
  );
}

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <div style={{display: 'flex', minHeight: '100vh'}}>
          <nav style={{width: '200px', background: '#f0f0f0', padding: '20px'}}>
            <h3>FindersKeepers v2</h3>
            <ul style={{listStyle: 'none', padding: 0}}>
              <li><a href="/" style={{color: '#1976d2', textDecoration: 'none'}}>Dashboard</a></li>
              <li><a href="/chat" style={{color: '#1976d2', textDecoration: 'none'}}>AI Chat</a></li>
            </ul>
          </nav>
          <main style={{flex: 1, padding: '20px'}}>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/chat" element={<Chat />} />
            </Routes>
          </main>
        </div>
      </Router>
    </ThemeProvider>
  );
}

export default App;