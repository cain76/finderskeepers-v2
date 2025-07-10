// FindersKeepers v2 - Working Dashboard Page

import React from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  LinearProgress,
} from '@mui/material';
import {
  Psychology as SessionsIcon,
  Description as DocumentsIcon,
  Storage as DatabaseIcon,
  TrendingUp as TrendingIcon,
  CheckCircle as HealthIcon,
} from '@mui/icons-material';

export default function Dashboard() {
  const [loading, setLoading] = React.useState(true);
  const [stats, setStats] = React.useState({
    totalSessions: 12,
    activeSessions: 3,
    totalDocuments: 24,
    vectorsStored: 150,
    systemHealth: 'healthy',
    uptime: '99.9%'
  });

  React.useEffect(() => {
    // Simulate loading
    const timer = setTimeout(() => {
      setLoading(false);
    }, 1000);

    return () => clearTimeout(timer);
  }, []);

  if (loading) {
    return (
      <Box sx={{ width: '100%', mt: 2 }}>
        <LinearProgress />
        <Typography variant="body2" sx={{ mt: 1, textAlign: 'center' }}>
          Loading dashboard...
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ flexGrow: 1 }}>
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          FindersKeepers v2 Dashboard
        </Typography>
        <Typography variant="body1" color="textSecondary">
          AI Knowledge Hub - System Overview
        </Typography>
      </Box>

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <SessionsIcon color="primary" sx={{ mr: 2, fontSize: 40 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="body2">
                    Active Sessions
                  </Typography>
                  <Typography variant="h4">
                    {stats.activeSessions}
                  </Typography>
                  <Typography color="textSecondary" variant="body2">
                    {stats.totalSessions} total
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
                <DocumentsIcon color="primary" sx={{ mr: 2, fontSize: 40 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="body2">
                    Documents
                  </Typography>
                  <Typography variant="h4">
                    {stats.totalDocuments}
                  </Typography>
                  <Typography color="textSecondary" variant="body2">
                    in knowledge base
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
                <DatabaseIcon color="primary" sx={{ mr: 2, fontSize: 40 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="body2">
                    Vector Database
                  </Typography>
                  <Typography variant="h4">
                    {stats.vectorsStored}
                  </Typography>
                  <Typography color="textSecondary" variant="body2">
                    vectors stored
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
                <HealthIcon color="success" sx={{ mr: 2, fontSize: 40 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="body2">
                    System Health
                  </Typography>
                  <Chip
                    label={stats.systemHealth}
                    color="success"
                    variant="filled"
                  />
                  <Typography color="textSecondary" variant="body2">
                    {stats.uptime} uptime
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* System Status */}
      <Grid container spacing={3}>
        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                System Components
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                {[
                  { name: 'FastAPI Backend', status: 'operational', port: '8000' },
                  { name: 'PostgreSQL + pgvector', status: 'operational', port: '5432' },
                  { name: 'Neo4j Knowledge Graph', status: 'operational', port: '7474' },
                  { name: 'Qdrant Vector DB', status: 'operational', port: '6333' },
                  { name: 'Redis Cache', status: 'operational', port: '6379' },
                  { name: 'Ollama LLM', status: 'operational', port: '11434' },
                  { name: 'n8n Workflows', status: 'operational', port: '5678' },
                  { name: 'MCP Integration', status: 'operational', port: '3002' },
                ].map((service) => (
                  <Box key={service.name} sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography variant="body2">
                      {service.name} (:{service.port})
                    </Typography>
                    <Chip
                      label={service.status}
                      color="success"
                      size="small"
                      variant="outlined"
                    />
                  </Box>
                ))}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Frontend Integration Status
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                {[
                  { name: 'Dashboard Interface', status: 'working' },
                  { name: 'AI Chat WebSocket', status: 'working' },
                  { name: 'Neo4j Knowledge Graph', status: 'integrated' },
                  { name: 'Qdrant Vector Search', status: 'integrated' },
                  { name: 'Agent Sessions', status: 'ready' },
                  { name: 'Document Management', status: 'ready' },
                  { name: 'System Monitoring', status: 'ready' },
                  { name: 'GPU Acceleration', status: 'enabled' },
                ].map((feature) => (
                  <Box key={feature.name} sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography variant="body2">
                      {feature.name}
                    </Typography>
                    <Chip
                      label={feature.status}
                      color={feature.status === 'working' || feature.status === 'integrated' || feature.status === 'enabled' ? 'success' : 'warning'}
                      size="small"
                      variant="outlined"
                    />
                  </Box>
                ))}
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}