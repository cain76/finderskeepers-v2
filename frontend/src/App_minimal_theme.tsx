import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline, Typography, Box, IconButton } from '@mui/material';
import { LightMode, DarkMode } from '@mui/icons-material';

// Import page components
import Dashboard from './pages/Dashboard_working';
import AgentSessions from './pages/AgentSessions';
import Documents from './pages/Documents';
import VectorSearch from './pages/VectorSearch';
import KnowledgeGraph from './pages/KnowledgeGraph';
import SystemMonitoring from './pages/SystemMonitoring';
import Chat from './pages/Chat';

// Simple Settings placeholder
function Settings() {
  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4">Settings</Typography>
      <Typography variant="body1">Theme settings coming soon...</Typography>
    </Box>
  );
}

function App() {
  const [darkMode, setDarkMode] = useState(false);

  const theme = createTheme({
    palette: {
      mode: darkMode ? 'dark' : 'light',
      primary: {
        main: '#1976d2',
      },
    },
  });

  const toggleTheme = () => setDarkMode(!darkMode);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Box sx={{ display: 'flex', height: '100vh' }}>
          {/* Sidebar */}
          <Box
            component="nav"
            sx={{
              width: 240,
              backgroundColor: darkMode ? '#1e1e1e' : '#f5f5f5',
              borderRight: `1px solid ${darkMode ? '#2c2c2c' : '#e0e0e0'}`,
              p: 2,
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
              <Typography variant="h6" sx={{ flexGrow: 1 }}>
                FindersKeepers v2
              </Typography>
              <IconButton onClick={toggleTheme} color="primary">
                {darkMode ? <LightMode /> : <DarkMode />}
              </IconButton>
            </Box>
            
            <Box component="ul" sx={{ listStyle: 'none', p: 0, m: 0 }}>
              {[
                { to: '/', label: '📊 Dashboard' },
                { to: '/sessions', label: '🤖 Agent Sessions' },
                { to: '/documents', label: '📄 Documents' },
                { to: '/search', label: '🔍 Vector Search' },
                { to: '/graph', label: '🕸️ Knowledge Graph' },
                { to: '/chat', label: '💬 AI Chat' },
                { to: '/monitoring', label: '📈 System Monitoring' },
                { to: '/settings', label: '⚙️ Settings' },
              ].map((item) => (
                <Box component="li" key={item.to} sx={{ mb: 1 }}>
                  <Link
                    to={item.to}
                    style={{
                      color: theme.palette.primary.main,
                      textDecoration: 'none',
                      padding: '8px 0',
                      display: 'block',
                      fontSize: '0.9rem',
                    }}
                  >
                    {item.label}
                  </Link>
                </Box>
              ))}
            </Box>
          </Box>

          {/* Main content */}
          <Box sx={{ flex: 1, p: 3, overflow: 'auto' }}>
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
          </Box>
        </Box>
      </Router>
    </ThemeProvider>
  );
}

export default App;