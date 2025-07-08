// FindersKeepers v2 - Main Dashboard Page

import React from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  LinearProgress,
  Chip,
  List,
  ListItem,
  ListItemText,
  IconButton,
  Tooltip,
  Paper,
} from '@mui/material';
import {
  Psychology as SessionsIcon,
  Description as DocumentsIcon,
  MonitorHeart as HealthIcon,
  TrendingUp as TrendingIcon,
  Refresh as RefreshIcon,
  PlayArrow as PlayIcon,
  Stop as StopIcon,
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { useAppStore, useSystemHealth, useActiveSessions, useRecentActivity } from '@/stores/appStore';
import { useWebSocket } from '@/hooks/useWebSocket';
import { apiService } from '@/services/api';


interface DashboardStats {
  totalSessions: number;
  activeSessions: number;
  totalDocuments: number;
  vectorsStored: number;
  avgResponseTime: number;
  errorRate: number;
}

export default function Dashboard() {
  const [stats, setStats] = React.useState<DashboardStats>({
    totalSessions: 0,
    activeSessions: 0,
    totalDocuments: 0,
    vectorsStored: 0,
    avgResponseTime: 0,
    errorRate: 0,
  });
  const [performanceData, setPerformanceData] = React.useState<any[]>([]);
  const [loading, setLoading] = React.useState(true);

  const systemHealth = useSystemHealth();
  const activeSessions = useActiveSessions();
  const recentActivity = useRecentActivity();
  const setSystemHealth = useAppStore(state => state.setSystemHealth);
  const setActiveSessions = useAppStore(state => state.setActiveSessions);

  // WebSocket for real-time updates
  const { subscribe } = useWebSocket();

  // Load initial data
  React.useEffect(() => {
    loadDashboardData();
  }, []);

  // Subscribe to real-time updates
  React.useEffect(() => {
    const unsubscribe = subscribe('health_update', (data) => {
      setSystemHealth(data);
    });

    return unsubscribe;
  }, [subscribe, setSystemHealth]);

  const loadDashboardData = async () => {
    try {
      setLoading(true);

      // Load system health
      const healthResponse = await apiService.getSystemHealth();
      if (healthResponse && healthResponse.status) {
        setSystemHealth(healthResponse);
      }

      // Load session stats
      const sessionStatsResponse = await apiService.getSessionStats('24h');
      const documentStatsResponse = await apiService.getDocumentStats();
      const performanceResponse = await apiService.getPerformanceMetrics();

      // Load active sessions
      const sessionsResponse = await apiService.getSessions({
        status: 'active',
        limit: 10,
      });

      if (sessionsResponse.success && sessionsResponse.data) {
        setActiveSessions(sessionsResponse.data);
      }

      // Combine stats
      setStats({
        totalSessions: sessionStatsResponse.data?.total || 0,
        activeSessions: sessionsResponse.data?.length || 0,
        totalDocuments: documentStatsResponse.data?.total || 0,
        vectorsStored: documentStatsResponse.data?.vectors || 0,
        avgResponseTime: performanceResponse.data?.avg_response_time || 0,
        errorRate: performanceResponse.data?.error_rate || 0,
      });

      // Set performance chart data
      if (performanceResponse.data?.timeline) {
        setPerformanceData(performanceResponse.data.timeline);
      }

    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getServiceStatusColor = (status: string) => {
    switch (status) {
      case 'up':
        return 'success';
      case 'degraded':
        return 'warning';
      case 'down':
        return 'error';
      default:
        return 'default';
    }
  };

  const formatUptime = (percentage: number) => {
    return `${percentage.toFixed(2)}%`;
  };

  const formatResponseTime = (ms: number) => {
    return `${ms.toFixed(0)}ms`;
  };

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
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Dashboard
        </Typography>
        <Tooltip title="Refresh data">
          <IconButton onClick={loadDashboardData}>
            <RefreshIcon />
          </IconButton>
        </Tooltip>
      </Box>

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
                  <Typography variant="h4">
                    {stats.activeSessions}
                  </Typography>
                  <Typography color="textSecondary" variant="body2">
                    {stats.totalSessions} total today
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
                  <Typography variant="h4">
                    {stats.totalDocuments}
                  </Typography>
                  <Typography color="textSecondary" variant="body2">
                    {stats.vectorsStored} vectors stored
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
                  <Typography variant="h4">
                    {formatResponseTime(stats.avgResponseTime)}
                  </Typography>
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
                  <Chip
                    label={systemHealth?.status || 'Unknown'}
                    color={systemHealth?.status === 'healthy' ? 'success' : 'warning'}
                    variant="filled"
                  />
                  <Typography color="textSecondary" variant="body2">
                    Error rate: {(stats.errorRate * 100).toFixed(1)}%
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Charts and Activity */}
      <Grid container spacing={3}>
        {/* Performance Chart */}
        <Grid size={{ xs: 12, md: 8 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Performance Metrics (24h)
              </Typography>
              <Box sx={{ width: '100%', height: 300 }}>
                <ResponsiveContainer>
                  <LineChart data={performanceData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="time" />
                    <YAxis />
                    <RechartsTooltip />
                    <Legend />
                    <Line 
                      type="monotone" 
                      dataKey="response_time" 
                      stroke="#8884d8" 
                      name="Response Time (ms)"
                    />
                    <Line 
                      type="monotone" 
                      dataKey="active_sessions" 
                      stroke="#82ca9d" 
                      name="Active Sessions"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Activity */}
        <Grid size={{ xs: 12, md: 4 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recent Activity
              </Typography>
              <List dense>
                {recentActivity.slice(0, 10).map((activity, index) => (
                  <ListItem key={index} divider>
                    <ListItemText
                      primary={activity.message}
                      secondary={new Date(activity.timestamp).toLocaleTimeString()}
                    />
                  </ListItem>
                ))}
                {recentActivity.length === 0 && (
                  <ListItem>
                    <ListItemText
                      primary="No recent activity"
                      secondary="Activity will appear here as it happens"
                    />
                  </ListItem>
                )}
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* Service Status */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Service Status
              </Typography>
              <Grid container spacing={2}>
                {systemHealth?.services && Object.entries(systemHealth.services).map(([service, status]) => (
                  <Grid size={{ xs: 12, sm: 6 }} key={service}>
                    <Paper sx={{ p: 2, textAlign: 'center' }}>
                      <Typography variant="subtitle2" gutterBottom>
                        {service.toUpperCase()}
                      </Typography>
                      <Chip
                        label={typeof status === 'string' ? status : status.status || 'unknown'}
                        color={getServiceStatusColor(typeof status === 'string' ? status : status.status || 'unknown')}
                        size="small"
                        sx={{ mb: 1 }}
                      />
                      {typeof status === 'object' && status.response_time_ms && (
                        <Typography variant="body2" color="textSecondary">
                          {formatResponseTime(status.response_time_ms)}
                        </Typography>
                      )}
                      {typeof status === 'object' && status.uptime_percentage && (
                        <Typography variant="body2" color="textSecondary">
                          {formatUptime(status.uptime_percentage)} uptime
                        </Typography>
                      )}
                    </Paper>
                  </Grid>
                ))}
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Active Sessions */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Active Sessions
              </Typography>
              <List dense>
                {activeSessions.slice(0, 5).map((session) => (
                  <ListItem 
                    key={session.id}
                    divider
                    secondaryAction={
                      <IconButton edge="end" size="small">
                        {session.status === 'active' ? (
                          <PlayIcon color="success" />
                        ) : (
                          <StopIcon color="disabled" />
                        )}
                      </IconButton>
                    }
                  >
                    <ListItemText
                      primary={`${session.agent_type} - ${session.metadata.session_type}`}
                      secondary={`Started: ${new Date(session.session_start).toLocaleTimeString()}`}
                    />
                  </ListItem>
                ))}
                {activeSessions.length === 0 && (
                  <ListItem>
                    <ListItemText
                      primary="No active sessions"
                      secondary="Sessions will appear here when agents are running"
                    />
                  </ListItem>
                )}
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}