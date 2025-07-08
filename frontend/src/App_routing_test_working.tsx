// Test React Router without complex components
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline, Typography, Box } from '@mui/material';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: { main: '#1976d2' },
  },
});

function SimpleLayout() {
  return (
    <Box sx={{ p: 4 }}>
      <Typography variant="h3" color="primary">
        FindersKeepers v2 - Routing Test
      </Typography>
      <Typography variant="body1" sx={{ mt: 2 }}>
        React Router is working! 🎉
      </Typography>
    </Box>
  );
}

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Routes>
          <Route path="/" element={<SimpleLayout />} />
          <Route path="*" element={<SimpleLayout />} />
        </Routes>
      </Router>
    </ThemeProvider>
  );
}

export default App;