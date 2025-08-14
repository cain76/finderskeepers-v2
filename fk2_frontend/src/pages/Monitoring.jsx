import React, { useEffect, useState } from 'react';
import { Box, Typography, Paper, CircularProgress } from '@mui/material';

// The Monitoring page fetches real‑time processing statistics from the
// backend API. If the request fails or returns no data, the page
// gracefully falls back to a simple message. The API base URL is
// configured via the VITE_API_URL environment variable.
function Monitoring() {
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState(null);

  useEffect(() => {
    async function fetchStats() {
      try {
        const apiUrl = import.meta.env.VITE_API_URL || '';
        const res = await fetch(`${apiUrl}/api/admin/processing-stats`);
        if (res.ok) {
          const data = await res.json();
          setStats(data);
        }
      } catch (err) {
        // Silently ignore errors; they will result in stats remaining null.
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    fetchStats();
  }, []);

  return (
    <Box sx={{ p: 4 }}>
      <Typography variant="h4" gutterBottom>
        Monitoring
      </Typography>
      {loading ? (
        <CircularProgress />
      ) : (
        <Paper sx={{ p: 2, whiteSpace: 'pre-wrap', fontFamily: 'monospace' }}>
          <Typography variant="body1">
            {stats ? JSON.stringify(stats, null, 2) : 'No data available.'}
          </Typography>
        </Paper>
      )}
    </Box>
  );
}

export default Monitoring;