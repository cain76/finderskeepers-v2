import React from 'react';
import { Box, Typography } from '@mui/material';

// Placeholder page for bulk embedding functionality. Once integrated
// with the backend, this page will initiate mass embedding jobs and
// display progress to the user.
function BulkEmbedding() {
  return (
    <Box sx={{ p: 4 }}>
      <Typography variant="h4" gutterBottom>
        Bulk Embedding
      </Typography>
      <Typography variant="body1">
        Run bulk embedding processes here.
      </Typography>
    </Box>
  );
}

export default BulkEmbedding;