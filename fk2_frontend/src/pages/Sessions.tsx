import React from 'react';
import { Box, Typography, Card, CardContent } from '@mui/material';

export default function Sessions() {
  return (
    <Box>
      <Typography variant="h4" fontWeight="bold" gutterBottom>
        Agent Sessions
      </Typography>
      <Typography variant="subtitle1" color="text.secondary" sx={{ mb: 4 }}>
        Monitor and manage AI agent sessions
      </Typography>

      <Card>
        <CardContent>
          <Typography variant="body1">
            Sessions page implementation coming soon...
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
}