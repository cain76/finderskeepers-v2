// Test version to isolate rendering issues
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline, Typography, Box } from '@mui/material';

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
      <Box sx={{ p: 4 }}>
        <Typography variant="h3" color="primary">
          FindersKeepers v2 - Test Mode
        </Typography>
        <Typography variant="body1" sx={{ mt: 2 }}>
          React app is loading successfully! 🎉
        </Typography>
      </Box>
    </ThemeProvider>
  );
}

export default App;