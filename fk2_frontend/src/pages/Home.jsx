import React from 'react';
import { Box, Typography, Button } from '@mui/material';
import { Link } from 'react-router-dom';

// Home page displays a welcoming hero section with a brief
// description of the FindersKeepers v2 platform and links to
// commonly used sections. The use of Material-UI components helps
// achieve a consistent look and feel across the app.
function Home() {
  return (
    <Box sx={{ p: 4, textAlign: 'center' }}>
      <Typography variant="h3" gutterBottom>
        Welcome to FindersKeepers v2
      </Typography>
      <Typography variant="body1" sx={{ mb: 4 }}>
        A modern knowledge hub for your personal AI agent, featuring an
        improved user interface and user experience.
      </Typography>
      <Button
        variant="contained"
        color="primary"
        component={Link}
        to="/monitoring"
        sx={{ mr: 2 }}
      >
        Go to Monitoring
      </Button>
      <Button
        variant="outlined"
        color="secondary"
        component={Link}
        to="/admin"
      >
        Admin Panel
      </Button>
    </Box>
  );
}

export default Home;