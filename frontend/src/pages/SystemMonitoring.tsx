// FindersKeepers v2 - System Monitoring Page

import React from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  LinearProgress,
  Chip,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Alert,
  CircularProgress,
  Fade,
} from '@mui/material';
import {
  CheckCircle as HealthyIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Refresh as RefreshIcon,
  MonitorHeart as MonitorIcon,
  Psychology as OllamaIcon,
  Sync as SyncIcon,
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
  AreaChart,
  Area,
} from 'recharts';
import { useWebSocket } from '@/hooks/useWebSocket';
import { apiService } from '@/services/api';
import type { SystemHealth } from '@/types';

interface ServiceStatus {
  name: string;
  status: 'up' | 'down' | 'degraded' | 'checking';
  uptime_percentage?: number;
  response_time_ms?: number;
  last_check?: string;
  details?: Record<string, any>;
}

interface PerformanceMetrics {
  timestamp: string;
  cpu_usage: number;
  memory_usage: number;
  response_time: number;
  active_connections: number;
}

interface LoadingStates {
  initial: boolean;
  health: boolean;
  services: boolean;
  performance: boolean;
  manual: boolean;
}

export default function SystemMonitoring() {
  const [systemHealth, setSystemHealth] = React.useState<SystemHealth | null>(null);
  const [services, setServices] = React.useState<ServiceStatus[]>([]);
  const [performanceData, setPerformanceData] = React.useState<PerformanceMetrics[]>([]);
  const [loading, setLoading] = React.useState<LoadingStates>({
    initial: true,
    health: false,
    services: false,
    performance: false,
    manual: false,
  });
  const [lastUpdate, setLastUpdate] = React.useState<string>('');
  const [isRefreshing, setIsRefreshing] = React.useState(false);

  const { subscribe } = useWebSocket();

  // Real-time health updates
  React.useEffect(() => {
    const unsubscribe = subscribe('health_update', (data: SystemHealth) => {
      setSystemHealth(data);
      setLastUpdate(new Date().toLocaleTimeString());
    });

    return unsubscribe;
  }, [subscribe]);

  // Update specific loading state
  const updateLoading = (key: keyof LoadingStates, value: boolean) => {
    setLoading(prev => ({ ...prev, [key]: value }));
  };

  // Load system health with caching and timeout
  const loadSystemHealth = async (isManual = false) => {
    try {
      if (isManual) {
        setIsRefreshing(true);
        updateLoading('manual', true);
      } else {
        updateLoading('health', true);
      }
      
      // Set a timeout for the API call
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout
      
      try {
        const healthResponse = await Promise.race([
          apiService.getSystemHealth(),
          new Promise((_, reject) => 
            setTimeout(() => reject(new Error('Health check timeout')), 10000)
          )
        ]) as any;
        
        clearTimeout(timeoutId);
        
        if (healthResponse.success && healthResponse.data) {
          setSystemHealth(healthResponse.data);
          
          // Transform services data asynchronously  
          setTimeout(() => {
            const servicesData: ServiceStatus[] = [];
            if (healthResponse.data.services) {
              Object.entries(healthResponse.data.services).forEach(([name, serviceInfo]: [string, any]) => {
                servicesData.push({
                  name: name.toUpperCase(),
                  status: serviceInfo.status || serviceInfo || 'unknown',
                  uptime_percentage: serviceInfo.uptime_percentage,
                  response_time_ms: serviceInfo.response_time_ms,
                  last_check: serviceInfo.last_check,
                  details: serviceInfo.details,
                });
              });
            }
            setServices(servicesData);
          }, 0);
        }
        
        setLastUpdate(new Date().toLocaleTimeString());
      } catch (timeoutError) {
        clearTimeout(timeoutId);
        console.error('Health check timeout or failed:', timeoutError);
        // Set basic fallback data
        setSystemHealth({
          status: 'unknown',
          services: {},
          last_check: new Date().toISOString()
        } as SystemHealth);
      }
    } catch (error) {
      console.error('Failed to load system health:', error);
    } finally {
      updateLoading('health', false);
      if (isManual) {
        updateLoading('manual', false);
        setIsRefreshing(false);
      }
    }
  };

  // Load performance data separately
  const loadPerformanceData = async () => {
    try {
      updateLoading('performance', true);
      
      // Generate sample performance data
      const now = new Date();
      const sampleData = Array.from({ length: 24 }, (_, i) => ({
        timestamp: new Date(now.getTime() - (23 - i) * 60 * 60 * 1000).toLocaleTimeString(),
        cpu_usage: Math.random() * 100,
        memory_usage: Math.random() * 100,
        response_time: 100 + Math.random() * 200,
        active_connections: Math.floor(Math.random() * 50),
      }));
      setPerformanceData(sampleData);
    } catch (error) {
      console.error('Failed to load performance data:', error);
    } finally {
      updateLoading('performance', false);
    }
  };

  // Initial load with progressive enhancement
  React.useEffect(() => {
    const initialize = async () => {
      updateLoading('initial', true);
      
      // Load health data first (faster)
      await loadSystemHealth();
      updateLoading('initial', false);
      
      // Load performance data in background
      loadPerformanceData();
    };
    
    initialize();
  }, []);

  // Auto-refresh system health (background updates)
  React.useEffect(() => {
    const interval = setInterval(() => {
      // Only refresh health data, not the entire UI
      loadSystemHealth(false);
    }, 30000);
    
    return () => clearInterval(interval);
  }, []);

  // Refresh performance data less frequently
  React.useEffect(() => {
    const interval = setInterval(() => {
      loadPerformanceData();
    }, 60000); // Every minute
    
    return () => clearInterval(interval);
  }, []);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'up':
      case 'healthy':
        return <HealthyIcon color="success" />;
      case 'degraded':
      case 'warning':
        return <WarningIcon color="warning" />;
      case 'down':
      case 'error':
        return <ErrorIcon color="error" />;
      default:
        return <MonitorIcon color="action" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'up':
      case 'healthy':
        return 'success';
      case 'degraded':
      case 'warning':
        return 'warning';
      case 'down':
      case 'error':
        return 'error';
      default:
        return 'default';
    }
  };

  const formatUptime = (percentage?: number) => {
    return percentage ? `${percentage.toFixed(2)}%` : 'N/A';
  };

  const formatResponseTime = (ms?: number) => {
    return ms ? `${ms.toFixed(0)}ms` : 'N/A';
  };

  const getOverallHealthStatus = () => {
    if (!systemHealth) {
      return { status: 'unknown', color: 'default' };
    }
    
    if (systemHealth.status === 'healthy') {
      return { status: 'All Systems Operational', color: 'success' };
    } else {
      return { status: 'Some Issues Detected', color: 'warning' };
    }
  };

  const handleManualRefresh = () => {
    Promise.all([
      loadSystemHealth(true),
      loadPerformanceData()
    ]);
  };

  // Show initial loading only on first load
  if (loading.initial) {
    return (
      <Box sx={{ width: '100%', mt: 2 }}>
        <LinearProgress />
        <Typography variant="body2" sx={{ mt: 1, textAlign: 'center' }}>
          Loading system health data...
        </Typography>
      </Box>
    );
  }

  const overallHealth = getOverallHealthStatus();

  return (
    <Box sx={{ flexGrow: 1 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          System Monitoring
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Fade in={loading.health}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <SyncIcon fontSize="small" color="action" />
              <Typography variant="body2" color="textSecondary">
                Updating...
              </Typography>
            </Box>
          </Fade>
          <Typography variant="body2" color="textSecondary">
            Last updated: {lastUpdate}
          </Typography>
          <Button
            variant="outlined"
            startIcon={isRefreshing ? <CircularProgress size={16} /> : <RefreshIcon />}
            onClick={handleManualRefresh}
            disabled={loading.manual}
          >
            {isRefreshing ? 'Refreshing...' : 'Refresh'}
          </Button>
        </Box>
      </Box>

      {/* Overall Status */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              {getStatusIcon(systemHealth?.status || 'unknown')}
              <Typography variant="h5">
                {overallHealth.status}
              </Typography>
              <Chip
                label={systemHealth?.status || 'unknown'}
                color={overallHealth.color as any}
                variant="filled"
              />
            </Box>
          </Box>
        </CardContent>
      </Card>

      {/* Service Status Grid */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        {services.map((service) => (
          <Grid size={{ xs: 12, sm: 6, md: 4 }} key={service.name}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  {getStatusIcon(service.status)}
                  <Typography variant="h6" sx={{ ml: 1 }}>
                    {service.name}
                  </Typography>
                </Box>
                
                <Chip
                  label={service.status}
                  color={getStatusColor(service.status) as any}
                  size="small"
                  sx={{ mb: 2 }}
                />
                
                <Box sx={{ mt: 2 }}>
                  {service.uptime_percentage !== undefined && (
                    <Typography variant="body2" color="textSecondary">
                      Uptime: {formatUptime(service.uptime_percentage)}
                    </Typography>
                  )}
                  {service.response_time_ms !== undefined && (
                    <Typography variant="body2" color="textSecondary">
                      Response: {formatResponseTime(service.response_time_ms)}
                    </Typography>
                  )}
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
        
        {/* Loading state for services */}
        {loading.services && (
          <Grid size={{ xs: 12 }}>
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 2 }}>
              <CircularProgress size={24} />
            </Box>
          </Grid>
        )}
      </Grid>

      {/* Performance Charts */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6">
                  System Resource Usage (24h)
                </Typography>
                {loading.performance && (
                  <CircularProgress size={20} />
                )}
              </Box>
              <Box sx={{ width: '100%', height: 300 }}>
                <ResponsiveContainer>
                  <AreaChart data={performanceData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="timestamp" />
                    <YAxis />
                    <RechartsTooltip />
                    <Legend />
                    <Area 
                      type="monotone" 
                      dataKey="cpu_usage" 
                      stackId="1"
                      stroke="#8884d8" 
                      fill="#8884d8"
                      name="CPU Usage (%)"
                    />
                    <Area 
                      type="monotone" 
                      dataKey="memory_usage" 
                      stackId="1"
                      stroke="#82ca9d" 
                      fill="#82ca9d"
                      name="Memory Usage (%)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6">
                  API Response Times (24h)
                </Typography>
                {loading.performance && (
                  <CircularProgress size={20} />
                )}
              </Box>
              <Box sx={{ width: '100%', height: 300 }}>
                <ResponsiveContainer>
                  <LineChart data={performanceData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="timestamp" />
                    <YAxis />
                    <RechartsTooltip />
                    <Legend />
                    <Line 
                      type="monotone" 
                      dataKey="response_time" 
                      stroke="#ff7c7c" 
                      name="Response Time (ms)"
                    />
                    <Line 
                      type="monotone" 
                      dataKey="active_connections" 
                      stroke="#8884d8" 
                      name="Active Connections"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* LLM Status */}
      {systemHealth?.local_llm && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <OllamaIcon color="primary" sx={{ mr: 1 }} />
              <Typography variant="h6">
                Local LLM Status (Ollama)
              </Typography>
            </Box>
            
            <Grid container spacing={2}>
              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <Typography variant="body2" color="textSecondary">
                  Status
                </Typography>
                <Chip
                  label={systemHealth.local_llm.enabled ? 'Enabled' : 'Disabled'}
                  color={systemHealth.local_llm.enabled ? 'success' : 'default'}
                  size="small"
                />
              </Grid>
              
              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <Typography variant="body2" color="textSecondary">
                  Health
                </Typography>
                <Chip
                  label={systemHealth.local_llm.healthy ? 'Healthy' : 'Unhealthy'}
                  color={systemHealth.local_llm.healthy ? 'success' : 'error'}
                  size="small"
                />
              </Grid>
              
              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <Typography variant="body2" color="textSecondary">
                  Embedding Model
                </Typography>
                <Typography variant="body1">
                  {systemHealth.local_llm.embedding_model}
                </Typography>
              </Grid>
              
              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <Typography variant="body2" color="textSecondary">
                  Chat Model
                </Typography>
                <Typography variant="body1">
                  {systemHealth.local_llm.chat_model}
                </Typography>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Detailed Service Information */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Detailed Service Status
          </Typography>
          
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Service</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Uptime</TableCell>
                  <TableCell>Response Time</TableCell>
                  <TableCell>Last Check</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {services.map((service) => (
                  <TableRow key={service.name} hover>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        {getStatusIcon(service.status)}
                        <Typography sx={{ ml: 1 }}>
                          {service.name}
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={service.status}
                        color={getStatusColor(service.status) as any}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>{formatUptime(service.uptime_percentage)}</TableCell>
                    <TableCell>{formatResponseTime(service.response_time_ms)}</TableCell>
                    <TableCell>
                      {service.last_check ? new Date(service.last_check).toLocaleString() : 'Never'}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>

          {services.length === 0 && !loading.services && (
            <Alert severity="info" sx={{ mt: 2 }}>
              No detailed service information available.
            </Alert>
          )}
        </CardContent>
      </Card>
    </Box>
  );
}