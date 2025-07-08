// FindersKeepers v2 - Agent Sessions Page

import React from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Button,
  TextField,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  LinearProgress,
  Alert,
} from '@mui/material';
import {
  Search as SearchIcon,
  Refresh as RefreshIcon,
  PlayArrow as PlayIcon,
  Visibility as ViewIcon,
  Psychology as SessionIcon,
  AccessTime as TimeIcon,
  Assignment as ActionIcon,
  Speed as PerformanceIcon,
} from '@mui/icons-material';
import { useWebSocket } from '@/hooks/useWebSocket';
import { apiService } from '@/services/api';
import type { AgentSession, AgentAction } from '@/types';

interface SessionStats {
  totalSessions: number;
  activeSessions: number;
  completedToday: number;
  avgDuration: number;
  errorRate: number;
}

export default function AgentSessions() {
  const [sessions, setSessions] = React.useState<AgentSession[]>([]);
  const [stats, setStats] = React.useState<SessionStats>({
    totalSessions: 0,
    activeSessions: 0,
    completedToday: 0,
    avgDuration: 0,
    errorRate: 0,
  });
  const [loading, setLoading] = React.useState(true);
  const [searchQuery, setSearchQuery] = React.useState('');
  const [statusFilter, setStatusFilter] = React.useState<string>('all');
  const [agentFilter, setAgentFilter] = React.useState<string>('all');
  const [selectedSession, setSelectedSession] = React.useState<AgentSession | null>(null);
  const [sessionActions, setSessionActions] = React.useState<AgentAction[]>([]);
  const [detailsOpen, setDetailsOpen] = React.useState(false);

  const { subscribe } = useWebSocket();

  // Real-time session updates
  React.useEffect(() => {
    const unsubscribe = subscribe('session_update', (data: AgentSession) => {
      setSessions(prev => {
        const index = prev.findIndex(s => s.id === data.id);
        if (index >= 0) {
          const updated = [...prev];
          updated[index] = data;
          return updated;
        } else {
          return [data, ...prev];
        }
      });
    });

    return unsubscribe;
  }, [subscribe]);

  // Load sessions data
  const loadSessions = async () => {
    try {
      setLoading(true);
      
      const response = await apiService.getSessions({
        limit: 100,
        agent_type: agentFilter !== 'all' ? agentFilter : undefined,
        status: statusFilter !== 'all' ? statusFilter : undefined,
      });

      if (response.success && response.data) {
        setSessions(response.data);
        
        // Calculate stats
        const total = response.data.length;
        const active = response.data.filter(s => s.status === 'active').length;
        const today = new Date().toDateString();
        const completedToday = response.data.filter(s => 
          s.status === 'completed' && 
          new Date(s.session_start).toDateString() === today
        ).length;
        
        const durations = response.data
          .filter(s => s.session_end)
          .map(s => new Date(s.session_end!).getTime() - new Date(s.session_start).getTime());
        const avgDuration = durations.length > 0 
          ? durations.reduce((a, b) => a + b, 0) / durations.length 
          : 0;

        const errorSessions = response.data.filter(s => s.status === 'error').length;
        const errorRate = total > 0 ? errorSessions / total : 0;

        setStats({
          totalSessions: total,
          activeSessions: active,
          completedToday,
          avgDuration: avgDuration / (1000 * 60), // Convert to minutes
          errorRate,
        });
      }
    } catch (error) {
      console.error('Failed to load sessions:', error);
    } finally {
      setLoading(false);
    }
  };

  // Load session actions
  const loadSessionActions = async (sessionId: string) => {
    try {
      const response = await apiService.getSessionActions(sessionId);
      if (response.success && response.data) {
        setSessionActions(response.data);
      }
    } catch (error) {
      console.error('Failed to load session actions:', error);
    }
  };

  // Handle session details
  const handleViewDetails = async (session: AgentSession) => {
    setSelectedSession(session);
    await loadSessionActions(session.id);
    setDetailsOpen(true);
  };

  React.useEffect(() => {
    loadSessions();
  }, [statusFilter, agentFilter]);

  const filteredSessions = sessions.filter(session => {
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      return (
        session.agent_type.toLowerCase().includes(query) ||
        session.id.toLowerCase().includes(query) ||
        (session.metadata?.project_name && session.metadata.project_name.toLowerCase().includes(query))
      );
    }
    return true;
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'success';
      case 'completed': return 'info';
      case 'error': return 'error';
      case 'terminated': return 'warning';
      default: return 'default';
    }
  };

  const formatDuration = (start: string, end?: string) => {
    const startTime = new Date(start);
    const endTime = end ? new Date(end) : new Date();
    const duration = endTime.getTime() - startTime.getTime();
    const minutes = Math.floor(duration / (1000 * 60));
    const seconds = Math.floor((duration % (1000 * 60)) / 1000);
    return `${minutes}m ${seconds}s`;
  };

  if (loading) {
    return (
      <Box sx={{ width: '100%', mt: 2 }}>
        <LinearProgress />
        <Typography variant="body2" sx={{ mt: 1, textAlign: 'center' }}>
          Loading agent sessions...
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ flexGrow: 1 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Agent Sessions
        </Typography>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={loadSessions}
        >
          Refresh
        </Button>
      </Box>

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <SessionIcon color="primary" sx={{ mr: 2 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="body2">
                    Total Sessions
                  </Typography>
                  <Typography variant="h4">
                    {stats.totalSessions}
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
                <PlayIcon color="success" sx={{ mr: 2 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="body2">
                    Active Now
                  </Typography>
                  <Typography variant="h4">
                    {stats.activeSessions}
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
                <TimeIcon color="info" sx={{ mr: 2 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="body2">
                    Avg Duration
                  </Typography>
                  <Typography variant="h4">
                    {stats.avgDuration.toFixed(1)}m
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
                <PerformanceIcon color="warning" sx={{ mr: 2 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="body2">
                    Error Rate
                  </Typography>
                  <Typography variant="h4">
                    {(stats.errorRate * 100).toFixed(1)}%
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Filters */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, md: 6 }}>
          <TextField
            fullWidth
            variant="outlined"
            placeholder="Search sessions..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <FormControl fullWidth>
            <InputLabel>Status</InputLabel>
            <Select
              value={statusFilter}
              label="Status"
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <MenuItem value="all">All Status</MenuItem>
              <MenuItem value="active">Active</MenuItem>
              <MenuItem value="completed">Completed</MenuItem>
              <MenuItem value="error">Error</MenuItem>
              <MenuItem value="terminated">Terminated</MenuItem>
            </Select>
          </FormControl>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <FormControl fullWidth>
            <InputLabel>Agent Type</InputLabel>
            <Select
              value={agentFilter}
              label="Agent Type"
              onChange={(e) => setAgentFilter(e.target.value)}
            >
              <MenuItem value="all">All Agents</MenuItem>
              <MenuItem value="claude">Claude</MenuItem>
              <MenuItem value="gpt">GPT</MenuItem>
              <MenuItem value="local">Local</MenuItem>
              <MenuItem value="custom">Custom</MenuItem>
            </Select>
          </FormControl>
        </Grid>
      </Grid>

      {/* Sessions Table */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Session History ({filteredSessions.length})
          </Typography>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Session ID</TableCell>
                  <TableCell>Agent Type</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Started</TableCell>
                  <TableCell>Duration</TableCell>
                  <TableCell>Actions</TableCell>
                  <TableCell align="right">Operations</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredSessions.map((session) => (
                  <TableRow key={session.id} hover>
                    <TableCell>
                      <Typography variant="body2" fontFamily="monospace">
                        {session.id.substring(0, 8)}...
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip 
                        label={session.agent_type}
                        variant="outlined"
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={session.status}
                        color={getStatusColor(session.status) as any}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      {new Date(session.session_start).toLocaleString()}
                    </TableCell>
                    <TableCell>
                      {formatDuration(session.session_start, session.session_end)}
                    </TableCell>
                    <TableCell>
                      {session.total_actions || 0}
                    </TableCell>
                    <TableCell align="right">
                      <Tooltip title="View Details">
                        <IconButton 
                          size="small"
                          onClick={() => handleViewDetails(session)}
                        >
                          <ViewIcon />
                        </IconButton>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
          
          {filteredSessions.length === 0 && (
            <Alert severity="info" sx={{ mt: 2 }}>
              No sessions found matching your criteria.
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Session Details Dialog */}
      <Dialog
        open={detailsOpen}
        onClose={() => setDetailsOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Session Details: {selectedSession?.agent_type} - {selectedSession?.id?.substring(0, 8)}
        </DialogTitle>
        <DialogContent>
          {selectedSession && (
            <Box>
              <Typography variant="subtitle1" gutterBottom>
                Session Information
              </Typography>
              <Grid container spacing={2} sx={{ mb: 3 }}>
                <Grid size={{ xs: 6 }}>
                  <Typography variant="body2" color="textSecondary">
                    Status
                  </Typography>
                  <Chip
                    label={selectedSession.status}
                    color={getStatusColor(selectedSession.status) as any}
                    size="small"
                  />
                </Grid>
                <Grid size={{ xs: 6 }}>
                  <Typography variant="body2" color="textSecondary">
                    Duration
                  </Typography>
                  <Typography variant="body1">
                    {formatDuration(selectedSession.session_start, selectedSession.session_end)}
                  </Typography>
                </Grid>
              </Grid>

              <Typography variant="subtitle1" gutterBottom>
                Actions ({sessionActions.length})
              </Typography>
              <List dense>
                {sessionActions.map((action, index) => (
                  <ListItem key={action.id || index}>
                    <ListItemIcon>
                      <ActionIcon />
                    </ListItemIcon>
                    <ListItemText
                      primary={action.action_type}
                      secondary={`${action.action_type} - ${new Date(action.timestamp).toLocaleString()}`}
                    />
                  </ListItem>
                ))}
              </List>
              
              {sessionActions.length === 0 && (
                <Alert severity="info">
                  No actions recorded for this session.
                </Alert>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailsOpen(false)}>
            Close
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}