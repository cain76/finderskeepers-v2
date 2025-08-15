import React from 'react';
import { Box, Typography, Card, CardContent } from '@mui/material';

export default function Documents() {
  return (
    <Box>
      <Typography variant="h4" fontWeight="bold" gutterBottom>
        Document Management
      </Typography>
      <Typography variant="subtitle1" color="text.secondary" sx={{ mb: 4 }}>
        Upload, manage, and search through your knowledge base
      </Typography>

      <Card>
        <CardContent>
          <Typography variant="body1">
            Documents page implementation coming soon...
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
}