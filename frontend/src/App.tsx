// Working version with simplified components
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline } from '@mui/material';
import AppLayout from '@/components/layout/AppLayout_simple';
import Dashboard from '@/pages/Dashboard';
import Documents from '@/pages/Documents';
import VectorSearch from '@/pages/VectorSearch';
import KnowledgeGraph from '@/pages/KnowledgeGraph';
import AgentSessions from '@/pages/AgentSessions';
import SystemMonitoring from '@/pages/SystemMonitoring';
import Chat from '@/pages/Chat';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
    background: {
      default: '#f5f5f5',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h4: {
      fontWeight: 600,
    },
    h6: {
      fontWeight: 600,
    },
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          borderRadius: 8,
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 6,
        },
      },
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Routes>
          <Route path="/" element={<AppLayout />}>
            <Route index element={<Dashboard />} />
            <Route path="sessions" element={<AgentSessions />} />
            <Route path="documents" element={<Documents />} />
            <Route path="search" element={<VectorSearch />} />
            <Route path="graph" element={<KnowledgeGraph />} />
            <Route path="monitoring" element={<SystemMonitoring />} />
            <Route path="chat" element={<Chat />} />
            <Route path="settings" element={<div>Settings Page</div>} />
          </Route>
        </Routes>
      </Router>
    </ThemeProvider>
  );
}

export default App;