import React from 'react';
import { Box, Typography, Card, CardContent } from '@mui/material';

export default function Chat() {
  return (
    <Box>
      <Typography variant="h4" fontWeight="bold" gutterBottom>
        AI Chat Interface
      </Typography>
      <Typography variant="subtitle1" color="text.secondary" sx={{ mb: 4 }}>
        Real-time chat with AI agents
      </Typography>

      <Card>
        <CardContent>
          <Typography variant="body1">
            Chat interface implementation coming soon...
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
}