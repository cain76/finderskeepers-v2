import { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline, Container, Paper, Typography, Box, TextField, Button } from '@mui/material';

// Import sophisticated page components
import Dashboard from './pages/Dashboard_working';
import AgentSessions from './pages/AgentSessions';
import Documents from './pages/Documents';
import VectorSearch from './pages/VectorSearch';
import KnowledgeGraph from './pages/KnowledgeGraph';
import SystemMonitoring from './pages/SystemMonitoring';
import Chat from './pages/Chat';
// Settings component will be created later
function Settings() {
  return <div style={{padding: '20px'}}><h1>Settings</h1><p>Configure your FindersKeepers preferences</p></div>;
}

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
  },
});



function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <div style={{display: 'flex', minHeight: '100vh'}}>
          <nav style={{width: '240px', background: '#f0f0f0', padding: '20px', borderRight: '1px solid #ddd'}}>
            <h3 style={{margin: '0 0 20px 0', color: '#1976d2'}}>FindersKeepers v2</h3>
            <ul style={{listStyle: 'none', padding: 0, margin: 0}}>
              <li style={{marginBottom: '10px'}}><Link to="/" style={{color: '#1976d2', textDecoration: 'none', padding: '8px 0', display: 'block'}}>📊 Dashboard</Link></li>
              <li style={{marginBottom: '10px'}}><Link to="/sessions" style={{color: '#1976d2', textDecoration: 'none', padding: '8px 0', display: 'block'}}>🤖 Agent Sessions</Link></li>
              <li style={{marginBottom: '10px'}}><Link to="/documents" style={{color: '#1976d2', textDecoration: 'none', padding: '8px 0', display: 'block'}}>📄 Documents</Link></li>
              <li style={{marginBottom: '10px'}}><Link to="/search" style={{color: '#1976d2', textDecoration: 'none', padding: '8px 0', display: 'block'}}>🔍 Vector Search</Link></li>
              <li style={{marginBottom: '10px'}}><Link to="/graph" style={{color: '#1976d2', textDecoration: 'none', padding: '8px 0', display: 'block'}}>🕸️ Knowledge Graph</Link></li>
              <li style={{marginBottom: '10px'}}><Link to="/chat" style={{color: '#1976d2', textDecoration: 'none', padding: '8px 0', display: 'block'}}>💬 AI Chat</Link></li>
              <li style={{marginBottom: '10px'}}><Link to="/monitoring" style={{color: '#1976d2', textDecoration: 'none', padding: '8px 0', display: 'block'}}>📈 System Monitoring</Link></li>
              <li style={{marginBottom: '10px'}}><Link to="/settings" style={{color: '#1976d2', textDecoration: 'none', padding: '8px 0', display: 'block'}}>⚙️ Settings</Link></li>
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