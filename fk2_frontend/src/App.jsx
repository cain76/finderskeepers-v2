import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import CssBaseline from '@mui/material/CssBaseline';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import Navigation from './components/Navigation.jsx';
import Home from './pages/Home.jsx';
import Monitoring from './pages/Monitoring.jsx';
import AdminPanel from './pages/AdminPanel.jsx';
import ProcessingStats from './pages/ProcessingStats.jsx';
import QueueMaintenance from './pages/QueueMaintenance.jsx';
import BulkEmbedding from './pages/BulkEmbedding.jsx';

// Define a light theme for the application. You can customize colors
// and typography here to better match your branding or the provided
// design document. Using a custom theme also makes it easier to
// introduce dark mode support in the future.
const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2', // A pleasant blue for headers and buttons
    },
    secondary: {
      main: '#9c27b0', // A complementary purple accent color
    },
    background: {
      default: '#f5f5f5', // Light grey background for a soft feel
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        {/*
          The Navigation component contains the app bar and side drawer
          used to navigate between the various pages. It is rendered
          outside the <Routes> so that it remains persistent while
          navigating.
        */}
        <Navigation />
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/monitoring" element={<Monitoring />} />
          <Route path="/admin" element={<AdminPanel />} />
          <Route path="/stats" element={<ProcessingStats />} />
          <Route path="/queue" element={<QueueMaintenance />} />
          <Route path="/bulk" element={<BulkEmbedding />} />
        </Routes>
      </Router>
    </ThemeProvider>
  );
}

export default App;