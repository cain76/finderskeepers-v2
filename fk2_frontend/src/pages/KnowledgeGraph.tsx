import React from 'react';
import { Box, Typography, Card, CardContent } from '@mui/material';

export default function KnowledgeGraph() {
  return (
    <Box>
      <Typography variant="h4" fontWeight="bold" gutterBottom>
        Knowledge Graph
      </Typography>
      <Typography variant="subtitle1" color="text.secondary" sx={{ mb: 4 }}>
        Visualize relationships in your knowledge base
      </Typography>

      <Card>
        <CardContent>
          <Typography variant="body1">
            Knowledge Graph page implementation coming soon...
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
}