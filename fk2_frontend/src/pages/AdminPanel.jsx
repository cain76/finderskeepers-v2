import React from 'react';
import { Box, Typography } from '@mui/material';

// The AdminPanel page will eventually host controls for bulk
// processing, queue maintenance and other administrative tasks.
// Currently it contains placeholder text describing the intended use.
function AdminPanel() {
  return (
    <Box sx={{ p: 4 }}>
      <Typography variant="h4" gutterBottom>
        Admin Panel
      </Typography>
      <Typography variant="body1">
        Use this panel to manage bulk processing, queue maintenance and
        other administrative tasks.
      </Typography>
    </Box>
  );
}

export default AdminPanel;