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

function AgentSessions() {
  return <div style={{padding: '20px'}}><h1>Agent Sessions</h1><p>Track AI agent interactions and sessions</p></div>;
}

function Documents() {
  return <div style={{padding: '20px'}}><h1>Documents</h1><p>Manage and search your document library</p></div>;
}

function VectorSearch() {
  return <div style={{padding: '20px'}}><h1>Vector Search</h1><p>Semantic search across your knowledge base</p></div>;
}

function KnowledgeGraph() {
  return <div style={{padding: '20px'}}><h1>Knowledge Graph</h1><p>Visualize entity relationships and connections</p></div>;
}

function SystemMonitoring() {
  return <div style={{padding: '20px'}}><h1>System Monitoring</h1><p>Monitor Docker containers and system performance</p></div>;
}

function Settings() {
  return <div style={{padding: '20px'}}><h1>Settings</h1><p>Configure your FindersKeepers preferences</p></div>;
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
          <nav style={{width: '240px', background: '#f0f0f0', padding: '20px', borderRight: '1px solid #ddd'}}>
            <h3 style={{margin: '0 0 20px 0', color: '#1976d2'}}>FindersKeepers v2</h3>
            <ul style={{listStyle: 'none', padding: 0, margin: 0}}>
              <li style={{marginBottom: '10px'}}><a href="/" style={{color: '#1976d2', textDecoration: 'none', padding: '8px 0', display: 'block'}}>📊 Dashboard</a></li>
              <li style={{marginBottom: '10px'}}><a href="/sessions" style={{color: '#1976d2', textDecoration: 'none', padding: '8px 0', display: 'block'}}>🤖 Agent Sessions</a></li>
              <li style={{marginBottom: '10px'}}><a href="/documents" style={{color: '#1976d2', textDecoration: 'none', padding: '8px 0', display: 'block'}}>📄 Documents</a></li>
              <li style={{marginBottom: '10px'}}><a href="/search" style={{color: '#1976d2', textDecoration: 'none', padding: '8px 0', display: 'block'}}>🔍 Vector Search</a></li>
              <li style={{marginBottom: '10px'}}><a href="/graph" style={{color: '#1976d2', textDecoration: 'none', padding: '8px 0', display: 'block'}}>🕸️ Knowledge Graph</a></li>
              <li style={{marginBottom: '10px'}}><a href="/chat" style={{color: '#1976d2', textDecoration: 'none', padding: '8px 0', display: 'block'}}>💬 AI Chat</a></li>
              <li style={{marginBottom: '10px'}}><a href="/monitoring" style={{color: '#1976d2', textDecoration: 'none', padding: '8px 0', display: 'block'}}>📈 System Monitoring</a></li>
              <li style={{marginBottom: '10px'}}><a href="/settings" style={{color: '#1976d2', textDecoration: 'none', padding: '8px 0', display: 'block'}}>⚙️ Settings</a></li>
            </ul>
          </nav>
          <main style={{flex: 1, padding: '20px'}}>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/sessions" element={<AgentSessions />} />
              <Route path="/documents" element={<Documents />} />
              <Route path="/search" element={<VectorSearch />} />
              <Route path="/graph" element={<KnowledgeGraph />} />
              <Route path="/chat" element={<Chat />} />
              <Route path="/monitoring" element={<SystemMonitoring />} />
              <Route path="/settings" element={<Settings />} />
            </Routes>
          </main>
        </div>
      </Router>
    </ThemeProvider>
  );
}

export default App;