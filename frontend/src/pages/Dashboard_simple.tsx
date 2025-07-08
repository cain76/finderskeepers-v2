// Simple Dashboard without hooks for testing
import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
} from '@mui/material';
import {
  Psychology as SessionsIcon,
  Description as DocumentsIcon,
  MonitorHeart as HealthIcon,
  TrendingUp as TrendingIcon,
} from '@mui/icons-material';

export default function Dashboard() {
  return (
    <Box sx={{ flexGrow: 1 }}>
      <Typography variant="h4" component="h1" sx={{ mb: 3 }}>
        Dashboard
      </Typography>

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <SessionsIcon color="primary" sx={{ mr: 2 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="body2">
                    Active Sessions
                  </Typography>
                  <Typography variant="h4">0</Typography>
                  <Typography color="textSecondary" variant="body2">
                    0 total today
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <DocumentsIcon color="primary" sx={{ mr: 2 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="body2">
                    Documents
                  </Typography>
                  <Typography variant="h4">0</Typography>
                  <Typography color="textSecondary" variant="body2">
                    0 vectors stored
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <TrendingIcon color="primary" sx={{ mr: 2 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="body2">
                    Avg Response Time
                  </Typography>
                  <Typography variant="h4">0ms</Typography>
                  <Typography color="textSecondary" variant="body2">
                    Last 24 hours
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <HealthIcon color="primary" sx={{ mr: 2 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="body2">
                    System Health
                  </Typography>
                  <Typography variant="h4">Good</Typography>
                  <Typography color="textSecondary" variant="body2">
                    All systems operational
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Welcome to FindersKeepers v2
          </Typography>
          <Typography variant="body1">
            Your AI Knowledge Hub is running successfully! This simplified dashboard 
            confirms that the React application, TypeScript compilation, and Material-UI 
            components are all working correctly.
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
}