import React, { useEffect, useState } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  LinearProgress,
  Chip,
  Button,
  Alert,
  CircularProgress,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Avatar,
  Divider,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Psychology as SessionsIcon,
  Description as DocumentsIcon,
  Timeline as VectorIcon,
  TrendingUp as TrendingUpIcon,
  Speed as SpeedIcon,
  Storage as StorageIcon,
  CloudQueue as QueueIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { useAppStore, useStats, useProcessingStats } from '@/stores/appStore';
import { apiService } from '@/services/api';
import type { SystemStats, ProcessingStats, AgentSession } from '@/types';

// Sample data for charts - in production this would come from the API
const sessionActivityData = [
  { time: '00:00', sessions: 4, actions: 12 },
  { time: '04:00', sessions: 2, actions: 8 },
  { time: '08:00', sessions: 8, actions: 24 },
  { time: '12:00', sessions: 12, actions: 36 },
  { time: '16:00', sessions: 10, actions: 28 },
  { time: '20:00', sessions: 6, actions: 18 },
];

const processingData = [
  { type: 'Processed', count: 1250 },
  { type: 'Pending', count: 125 },
  { type: 'Failed', count: 15 },
];

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ReactNode;
  color: 'primary' | 'secondary' | 'success' | 'warning' | 'error';
  loading?: boolean;
  trend?: number;
}

const MetricCard: React.FC<MetricCardProps> = ({ title, value, subtitle, icon, color, loading, trend }) => (
  <Card sx={{ height: '100%' }}>
    <CardContent>
      <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
        <Avatar sx={{ bgcolor: `${color}.main`, width: 48, height: 48 }}>
          {icon}
        </Avatar>
        {trend && (
          <Chip
            icon={<TrendingUpIcon />}
            label={`${trend > 0 ? '+' : ''}${trend}%`}
            size="small"
            color={trend > 0 ? 'success' : 'error'}
          />
        )}
      </Box>
      
      {loading ? (
        <CircularProgress size={24} />
      ) : (
        <>
          <Typography variant="h4" fontWeight="bold" color="text.primary">
            {value}
          </Typography>
          <Typography variant="body1" color="text.primary" sx={{ mt: 0.5 }}>
            {title}
          </Typography>
          {subtitle && (
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              {subtitle}
            </Typography>
          )}
        </>
      )}
    </CardContent>
  </Card>
);

export default function Dashboard() {
  const { 
    sessions, 
    documents, 
    setStats, 
    setProcessingStats, 
    setSessions, 
    setDocuments,
    setLoading,
    addError 
  } = useAppStore();
  
  const stats = useStats();
  const processingStats = useProcessingStats();
  const [recentSessions, setRecentSessions] = useState<AgentSession[]>([]);

  useEffect(() => {
    const fetchDashboardData = async () => {
      setLoading('stats', true);
      
      try {
        // Fetch system statistics
        const [statsResponse, processingResponse, sessionsResponse, documentsResponse] = await Promise.allSettled([
          apiService.admin.stats(),
          apiService.admin.stats(), // Placeholder for processing stats
          apiService.mcp.sessions.recent(),
          apiService.documents.list(),
        ]);

        // Handle stats
        if (statsResponse.status === 'fulfilled') {
          const mockStats: SystemStats = {
            total_sessions: sessions.length,
            active_sessions: sessions.filter(s => s.status === 'active').length,
            total_documents: documents.length,
            unprocessed_documents: documents.filter(d => d.status === 'pending').length,
            total_actions: 0,
            embedding_queue_size: 50,
            processing_status: 'active',
          };
          setStats(mockStats);
        }

        // Handle processing stats
        if (processingResponse.status === 'fulfilled') {
          const mockProcessingStats: ProcessingStats = {
            documents_processed: 1250,
            documents_pending: 125,
            documents_failed: 15,
            embeddings_created: 15000,
            processing_rate: 85.5,
            last_processing_time: new Date().toISOString(),
          };
          setProcessingStats(mockProcessingStats);
        }

        // Handle sessions
        if (sessionsResponse.status === 'fulfilled') {
          const mockSessions: AgentSession[] = [
            {
              id: '1',
              client_id: 'claude-session-1',
              session_start: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
              status: 'active',
              total_actions: 15,
              context_summary: 'Working on frontend development',
            },
            {
              id: '2',
              client_id: 'claude-session-2',
              session_start: new Date(Date.now() - 1000 * 60 * 60).toISOString(),
              session_end: new Date(Date.now() - 1000 * 60 * 10).toISOString(),
              status: 'ended',
              total_actions: 42,
              context_summary: 'Database optimization and query improvements',
            },
          ];
          setSessions(mockSessions);
          setRecentSessions(mockSessions.slice(0, 5));
        }

      } catch (error) {
        console.error('Failed to fetch dashboard data:', error);
        addError('Failed to load dashboard data');
      } finally {
        setLoading('stats', false);
      }
    };

    fetchDashboardData();
    
    // Refresh data every 30 seconds
    const interval = setInterval(fetchDashboardData, 30000);
    return () => clearInterval(interval);
  }, [setStats, setProcessingStats, setSessions, setDocuments, setLoading, addError, sessions.length, documents.length]);

  const handleRefreshStats = async () => {
    setLoading('stats', true);
    try {
      const response = await apiService.admin.stats();
      console.log('Stats refreshed:', response.data);
    } catch (error) {
      addError('Failed to refresh statistics');
    } finally {
      setLoading('stats', false);
    }
  };

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
        <Box>
          <Typography variant="h4" fontWeight="bold" gutterBottom>
            Welcome to FindersKeepers v2
          </Typography>
          <Typography variant="subtitle1" color="text.secondary">
            Your AI-powered knowledge management hub
          </Typography>
        </Box>
        <Button variant="outlined" onClick={handleRefreshStats} startIcon={<DashboardIcon />}>
          Refresh
        </Button>
      </Box>

      {/* System Status Alert */}
      <Alert severity="success" sx={{ mb: 3 }}>
        <Typography variant="body2">
          All systems operational. Processing {processingStats?.processing_rate || 85}% of documents successfully.
        </Typography>
      </Alert>

      {/* Metrics Grid */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Active Sessions"
            value={stats?.active_sessions || 0}
            subtitle={`${stats?.total_sessions || 0} total sessions`}
            icon={<SessionsIcon />}
            color="primary"
            trend={12}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Documents Processed"
            value={processingStats?.documents_processed || 0}
            subtitle={`${processingStats?.documents_pending || 0} pending`}
            icon={<DocumentsIcon />}
            color="success"
            trend={8}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Vector Embeddings"
            value={`${((processingStats?.embeddings_created || 0) / 1000).toFixed(1)}K`}
            subtitle="Knowledge vectors created"
            icon={<VectorIcon />}
            color="secondary"
            trend={25}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Processing Rate"
            value={`${processingStats?.processing_rate || 85}%`}
            subtitle="Success rate"
            icon={<SpeedIcon />}
            color="warning"
            trend={-2}
          />
        </Grid>
      </Grid>

      {/* Charts and Activity */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} lg={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight="bold" gutterBottom>
                Session Activity (24h)
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={sessionActivityData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis />
                  <Tooltip />
                  <Line 
                    type="monotone" 
                    dataKey="sessions" 
                    stroke="#1976d2" 
                    strokeWidth={2}
                    name="Sessions"
                  />
                  <Line 
                    type="monotone" 
                    dataKey="actions" 
                    stroke="#dc004e" 
                    strokeWidth={2}
                    name="Actions"
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} lg={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight="bold" gutterBottom>
                Processing Status
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={processingData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="type" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="count" fill="#1976d2" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Recent Activity and System Info */}
      <Grid container spacing={3}>
        <Grid item xs={12} lg={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight="bold" gutterBottom>
                Recent Sessions
              </Typography>
              <List>
                {recentSessions.map((session, index) => (
                  <React.Fragment key={session.id}>
                    <ListItem>
                      <ListItemIcon>
                        <Avatar sx={{ 
                          bgcolor: session.status === 'active' ? 'success.main' : 'text.secondary',
                          width: 32, 
                          height: 32 
                        }}>
                          {session.status === 'active' ? <CheckCircleIcon /> : <SessionsIcon />}
                        </Avatar>
                      </ListItemIcon>
                      <ListItemText
                        primary={
                          <Box display="flex" alignItems="center" gap={1}>
                            <Typography variant="body2">
                              Session {session.client_id}
                            </Typography>
                            <Chip 
                              label={session.status} 
                              size="small" 
                              color={session.status === 'active' ? 'success' : 'default'}
                            />
                          </Box>
                        }
                        secondary={
                          <Box>
                            <Typography variant="body2" color="text.secondary">
                              {session.context_summary}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {session.total_actions} actions • {new Date(session.session_start).toLocaleTimeString()}
                            </Typography>
                          </Box>
                        }
                      />
                    </ListItem>
                    {index < recentSessions.length - 1 && <Divider />}
                  </React.Fragment>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} lg={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight="bold" gutterBottom>
                System Health
              </Typography>
              <Box gap={2}>
                <Box display="flex" justifyContent="space-between" alignItems="center" py={1}>
                  <Typography variant="body2">API Service</Typography>
                  <Chip icon={<CheckCircleIcon />} label="Healthy" color="success" size="small" />
                </Box>
                <Box display="flex" justifyContent="space-between" alignItems="center" py={1}>
                  <Typography variant="body2">WebSocket Connection</Typography>
                  <Chip icon={<CheckCircleIcon />} label="Connected" color="success" size="small" />
                </Box>
                <Box display="flex" justifyContent="space-between" alignItems="center" py={1}>
                  <Typography variant="body2">Database</Typography>
                  <Chip icon={<CheckCircleIcon />} label="Operational" color="success" size="small" />
                </Box>
                <Box display="flex" justifyContent="space-between" alignItems="center" py={1}>
                  <Typography variant="body2">Vector Search</Typography>
                  <Chip icon={<WarningIcon />} label="Limited" color="warning" size="small" />
                </Box>
                <Box display="flex" justifyContent="space-between" alignItems="center" py={1}>
                  <Typography variant="body2">Processing Queue</Typography>
                  <Box display="flex" alignItems="center" gap={1}>
                    <LinearProgress 
                      variant="determinate" 
                      value={75} 
                      sx={{ width: 60 }}
                    />
                    <Typography variant="caption">75%</Typography>
                  </Box>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}
