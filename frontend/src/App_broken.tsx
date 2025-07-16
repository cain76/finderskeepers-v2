import { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import { CssBaseline, Container, Paper, Typography, Box, TextField, Button } from '@mui/material';
import { useTheme } from './stores/appStore';
import { getTheme } from './theme';
import useSystemTheme from './hooks/useSystemTheme';

// Import sophisticated page components
import Dashboard from './pages/Dashboard_working';
import AgentSessions from './pages/AgentSessions';
import Documents from './pages/Documents';
import VectorSearch from './pages/VectorSearch';
import KnowledgeGraph from './pages/KnowledgeGraph';
import SystemMonitoring from './pages/SystemMonitoring';
import Chat from './pages/Chat';
import Settings from './pages/Settings';

function App() {
  const { resolvedTheme } = useTheme();
  const theme = getTheme(resolvedTheme);
  
  // Initialize system theme detection
  useSystemTheme();

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Box 
          sx={{ 
            display: 'flex', 
            height: '100vh',
            width: '100vw',
            overflow: 'hidden'
          }}
        >
          <Box
            component="nav"
            sx={{
              width: { xs: '200px', sm: '220px', md: '240px' },
              minWidth: '180px',
              background: (theme) => theme.custom.sidebar.background,
              padding: { xs: '12px', sm: '16px', md: '20px' },
              borderRight: (theme) => `1px solid ${theme.custom.sidebar.border}`,
              overflow: 'auto',
              flexShrink: 0
            }}
          >
            <Typography 
              variant="h6" 
              sx={{ 
                margin: '0 0 20px 0', 
                color: 'primary.main',
                fontSize: { xs: '1.1rem', sm: '1.25rem' }
              }}
            >
              FindersKeepers v2
            </Typography>
            <Box component="ul" sx={{ listStyle: 'none', padding: 0, margin: 0 }}>
              <Box component="li" sx={{ marginBottom: '10px' }}>
                <Link to="/" style={{ color: theme.palette.primary.main, textDecoration: 'none', padding: '8px 0', display: 'block', fontSize: '0.9rem' }}>
                  📊 Dashboard
                </Link>
              </Box>
              <Box component="li" sx={{ marginBottom: '10px' }}>
                <Link to="/sessions" style={{ color: theme.palette.primary.main, textDecoration: 'none', padding: '8px 0', display: 'block', fontSize: '0.9rem' }}>
                  🤖 Agent Sessions
                </Link>
              </Box>
              <Box component="li" sx={{ marginBottom: '10px' }}>
                <Link to="/documents" style={{ color: theme.palette.primary.main, textDecoration: 'none', padding: '8px 0', display: 'block', fontSize: '0.9rem' }}>
                  📄 Documents
                </Link>
              </Box>
              <Box component="li" sx={{ marginBottom: '10px' }}>
                <Link to="/search" style={{ color: theme.palette.primary.main, textDecoration: 'none', padding: '8px 0', display: 'block', fontSize: '0.9rem' }}>
                  🔍 Vector Search
                </Link>
              </Box>
              <Box component="li" sx={{ marginBottom: '10px' }}>
                <Link to="/graph" style={{ color: theme.palette.primary.main, textDecoration: 'none', padding: '8px 0', display: 'block', fontSize: '0.9rem' }}>
                  🕸️ Knowledge Graph
                </Link>
              </Box>
              <Box component="li" sx={{ marginBottom: '10px' }}>
                <Link to="/chat" style={{ color: theme.palette.primary.main, textDecoration: 'none', padding: '8px 0', display: 'block', fontSize: '0.9rem' }}>
                  💬 AI Chat
                </Link>
              </Box>
              <Box component="li" sx={{ marginBottom: '10px' }}>
                <Link to="/monitoring" style={{ color: theme.palette.primary.main, textDecoration: 'none', padding: '8px 0', display: 'block', fontSize: '0.9rem' }}>
                  📈 System Monitoring
                </Link>
              </Box>
              <Box component="li" sx={{ marginBottom: '10px' }}>
                <Link to="/settings" style={{ color: theme.palette.primary.main, textDecoration: 'none', padding: '8px 0', display: 'block', fontSize: '0.9rem' }}>
                  ⚙️ Settings
                </Link>
              </Box>
            </Box>
          </Box>
          <Box
            component="main"
            sx={{
              flex: 1,
              padding: { xs: '12px', sm: '16px', md: '20px' },
              overflow: 'auto',
              height: '100vh',
              width: 0 // Forces flex item to shrink properly
            }}
          >
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