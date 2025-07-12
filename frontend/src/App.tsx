import React, { useState, useEffect } from 'react';
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

// Settings component with theme controls
function Settings({ darkMode, toggleTheme }: { darkMode: boolean; toggleTheme: () => void }) {
  return (
    <Box sx={{ maxWidth: 800, mx: 'auto', p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Settings
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Configure your FindersKeepers v2 preferences
      </Typography>

      {/* Theme Settings Card */}
      <Box 
        sx={{ 
          p: 3, 
          mb: 3, 
          border: 1, 
          borderColor: 'divider', 
          borderRadius: 2,
          backgroundColor: 'background.paper'
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            Appearance
          </Typography>
          <IconButton onClick={toggleTheme} color="primary">
            {darkMode ? <LightMode /> : <DarkMode />}
          </IconButton>
        </Box>

        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Choose how FindersKeepers looks to you.
        </Typography>

        <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
          <Box 
            onClick={() => darkMode && toggleTheme()}
            sx={{ 
              p: 2, 
              border: 1, 
              borderColor: !darkMode ? 'primary.main' : 'divider',
              borderRadius: 1,
              cursor: 'pointer',
              backgroundColor: !darkMode ? 'primary.main' : 'transparent',
              color: !darkMode ? 'primary.contrastText' : 'text.primary',
              display: 'flex',
              alignItems: 'center',
              gap: 1,
              '&:hover': { opacity: 0.8 }
            }}
          >
            <LightMode fontSize="small" />
            <Typography variant="body2">Light</Typography>
            {!darkMode && <Typography variant="caption">(Active)</Typography>}
          </Box>

          <Box 
            onClick={() => !darkMode && toggleTheme()}
            sx={{ 
              p: 2, 
              border: 1, 
              borderColor: darkMode ? 'primary.main' : 'divider',
              borderRadius: 1,
              cursor: 'pointer',
              backgroundColor: darkMode ? 'primary.main' : 'transparent',
              color: darkMode ? 'primary.contrastText' : 'text.primary',
              display: 'flex',
              alignItems: 'center',
              gap: 1,
              '&:hover': { opacity: 0.8 }
            }}
          >
            <DarkMode fontSize="small" />
            <Typography variant="body2">Dark</Typography>
            {darkMode && <Typography variant="caption">(Active)</Typography>}
          </Box>
        </Box>

        <Typography variant="caption" color="text.secondary">
          Current theme: {darkMode ? 'Dark' : 'Light'} mode
        </Typography>
      </Box>

      {/* Application Settings Card */}
      <Box 
        sx={{ 
          p: 3, 
          border: 1, 
          borderColor: 'divider', 
          borderRadius: 2,
          backgroundColor: 'background.paper'
        }}
      >
        <Typography variant="h6" gutterBottom>
          Application
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          General application preferences and behavior settings.
        </Typography>
        
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="body1">Real-time updates</Typography>
            <Box sx={{ px: 2, py: 0.5, backgroundColor: 'success.main', color: 'success.contrastText', borderRadius: 1 }}>
              <Typography variant="caption">Enabled</Typography>
            </Box>
          </Box>
          
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="body1">Vector search</Typography>
            <Box sx={{ px: 2, py: 0.5, backgroundColor: 'success.main', color: 'success.contrastText', borderRadius: 1 }}>
              <Typography variant="caption">Enabled</Typography>
            </Box>
          </Box>
          
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="body1">Knowledge graph</Typography>
            <Box sx={{ px: 2, py: 0.5, backgroundColor: 'success.main', color: 'success.contrastText', borderRadius: 1 }}>
              <Typography variant="caption">Enabled</Typography>
            </Box>
          </Box>
        </Box>
      </Box>
    </Box>
  );
}

function App() {
  // Load theme preference from localStorage or default to false
  const [darkMode, setDarkMode] = useState(() => {
    try {
      const saved = localStorage.getItem('finderskeepers-theme');
      return saved === 'dark';
    } catch {
      return false;
    }
  });

  // Save theme preference to localStorage whenever it changes
  useEffect(() => {
    try {
      localStorage.setItem('finderskeepers-theme', darkMode ? 'dark' : 'light');
    } catch (error) {
      console.warn('Failed to save theme preference:', error);
    }
  }, [darkMode]);

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
              <Route path="/settings" element={<Settings darkMode={darkMode} toggleTheme={toggleTheme} />} />
            </Routes>
          </Box>
        </Box>
      </Router>
    </ThemeProvider>
  );
}

export default App;