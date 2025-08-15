import React from 'react';
import { Box, Typography, Card, CardContent } from '@mui/material';

export default function VectorSearch() {
  return (
    <Box>
      <Typography variant="h4" fontWeight="bold" gutterBottom>
        Vector Search
      </Typography>
      <Typography variant="subtitle1" color="text.secondary" sx={{ mb: 4 }}>
        Semantic search across your knowledge base
      </Typography>

      <Card>
        <CardContent>
          <Typography variant="body1">
            Vector Search page implementation coming soon...
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
}