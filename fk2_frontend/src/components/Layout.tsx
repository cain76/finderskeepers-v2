import React, { useEffect } from 'react';
import {
  Box,
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Badge,
  Chip,
  Alert,
  Snackbar,
  useMediaQuery,
  useTheme,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Dashboard as DashboardIcon,
  Psychology as SessionsIcon,
  Description as DocumentsIcon,
  Search as SearchIcon,
  AccountTree as GraphIcon,
  Chat as ChatIcon,
  MonitorHeart as MonitoringIcon,
  Settings as SettingsIcon,
  Notifications as NotificationsIcon,
  Close as CloseIcon,
} from '@mui/icons-material';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { useAppStore, useConnectionStatus, useErrors } from '@/stores/appStore';
import { useWebSocket } from '@/hooks/useWebSocket';
import { apiService } from '@/services/api';

const DRAWER_WIDTH = 280;

interface NavigationItem {
  text: string;
  icon: React.ReactNode;
  path: string;
  badge?: number;
}

export default function Layout() {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const navigate = useNavigate();
  const location = useLocation();
  
  const { 
    sidebarOpen, 
    setSidebarOpen, 
    setConnectionStatus,
    sessions,
    errors,
    removeError 
  } = useAppStore();
  
  const connectionStatus = useConnectionStatus();
  
  // Initialize WebSocket connection
  const { isConnected } = useWebSocket({
    clientId: 'frontend-client',
    onConnect: () => {
      console.log('Frontend WebSocket connected');
    },
    onDisconnect: () => {
      console.log('Frontend WebSocket disconnected');
    },
    onError: (error) => {
      console.error('Frontend WebSocket error:', error);
    },
  });

  // Check API health on mount
  useEffect(() => {
    const checkHealth = async () => {
      try {
        await apiService.health();
        setConnectionStatus({ api: 'connected' });
      } catch (error) {
        console.error('API health check failed:', error);
        setConnectionStatus({ api: 'error' });
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 30000); // Check every 30 seconds
    return () => clearInterval(interval);
  }, [setConnectionStatus]);

  const handleDrawerToggle = () => {
    setSidebarOpen(!sidebarOpen);
  };

  const handleNavigation = (path: string) => {
    navigate(path);
    if (isMobile) {
      setSidebarOpen(false);
    }
  };

  const handleCloseError = (errorId: string) => {
    removeError(errorId);
  };

  const getConnectionStatusColor = () => {
    if (connectionStatus.api === 'connected' && isConnected) {
      return 'success';
    } else if (connectionStatus.api === 'error' || connectionStatus.websocket === 'error') {
      return 'error';
    } else {
      return 'warning';
    }
  };

  const getConnectionStatusText = () => {
    if (connectionStatus.api === 'connected' && isConnected) {
      return 'Connected';
    } else if (connectionStatus.api === 'error' || connectionStatus.websocket === 'error') {
      return 'Error';
    } else {
      return 'Connecting...';
    }
  };

  const navigationItems: NavigationItem[] = [
    {
      text: 'Dashboard',
      icon: <DashboardIcon />,
      path: '/',
    },
    {
      text: 'Agent Sessions',
      icon: <SessionsIcon />,
      path: '/sessions',
      badge: sessions.filter(s => s.status === 'active').length,
    },
    {
      text: 'Documents',
      icon: <DocumentsIcon />,
      path: '/documents',
    },
    {
      text: 'Vector Search',
      icon: <SearchIcon />,
      path: '/search',
    },
    {
      text: 'Knowledge Graph',
      icon: <GraphIcon />,
      path: '/graph',
    },
    {
      text: 'Chat Interface',
      icon: <ChatIcon />,
      path: '/chat',
    },
    {
      text: 'System Monitoring',
      icon: <MonitoringIcon />,
      path: '/monitoring',
    },
    {
      text: 'Settings',
      icon: <SettingsIcon />,
      path: '/settings',
    },
  ];

  const currentPageTitle = navigationItems.find(item => item.path === location.pathname)?.text || 'Dashboard';

  const drawer = (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ p: 3, borderBottom: '1px solid rgba(255, 255, 255, 0.12)' }}>
        <Typography variant="h5" sx={{ fontWeight: 700, color: 'primary.main' }}>
          FindersKeepers
        </Typography>
        <Typography variant="caption" sx={{ color: 'text.secondary' }}>
          v2.0 AI Knowledge Hub
        </Typography>
      </Box>
      
      <List sx={{ flex: 1, pt: 2 }}>
        {navigationItems.map((item) => (
          <ListItem key={item.text} disablePadding sx={{ px: 2, py: 0.5 }}>
            <ListItemButton
              onClick={() => handleNavigation(item.path)}
              selected={location.pathname === item.path}
              sx={{
                borderRadius: 2,
                '&.Mui-selected': {
                  backgroundColor: 'primary.main',
                  '&:hover': {
                    backgroundColor: 'primary.dark',
                  },
                },
                '&:hover': {
                  backgroundColor: 'rgba(255, 255, 255, 0.05)',
                },
              }}
            >
              <ListItemIcon sx={{ 
                color: location.pathname === item.path ? 'white' : 'text.secondary',
                minWidth: 36 
              }}>
                {item.badge ? (
                  <Badge badgeContent={item.badge} color="error">
                    {item.icon}
                  </Badge>
                ) : (
                  item.icon
                )}
              </ListItemIcon>
              <ListItemText 
                primary={item.text}
                sx={{
                  '& .MuiListItemText-primary': {
                    fontSize: '0.875rem',
                    fontWeight: location.pathname === item.path ? 600 : 400,
                    color: location.pathname === item.path ? 'white' : 'text.primary',
                  },
                }}
              />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
    </Box>
  );

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      {/* App Bar */}
      <AppBar
        position="fixed"
        sx={{
          width: { md: `calc(100% - ${sidebarOpen ? DRAWER_WIDTH : 0}px)` },
          ml: { md: sidebarOpen ? `${DRAWER_WIDTH}px` : 0 },
          backgroundColor: 'background.paper',
          borderBottom: '1px solid rgba(255, 255, 255, 0.12)',
          boxShadow: 'none',
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="toggle navigation"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { md: sidebarOpen ? 'none' : 'flex' } }}
          >
            <MenuIcon />
          </IconButton>
          
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1, color: 'text.primary' }}>
            {currentPageTitle}
          </Typography>
          
          {/* Connection Status */}
          <Chip
            icon={<MonitoringIcon />}
            label={getConnectionStatusText()}
            color={getConnectionStatusColor()}
            variant="outlined"
            size="small"
            sx={{ mr: 2 }}
          />
          
          {/* Notifications */}
          <IconButton color="inherit">
            <Badge badgeContent={errors.length} color="error">
              <NotificationsIcon />
            </Badge>
          </IconButton>
        </Toolbar>
      </AppBar>

      {/* Navigation Drawer */}
      <Box
        component="nav"
        sx={{ width: { md: sidebarOpen ? DRAWER_WIDTH : 0 }, flexShrink: { md: 0 } }}
      >
        <Drawer
          variant={isMobile ? 'temporary' : 'persistent'}
          open={sidebarOpen}
          onClose={handleDrawerToggle}
          ModalProps={{
            keepMounted: true, // Better open performance on mobile.
          }}
          sx={{
            '& .MuiDrawer-paper': {
              boxSizing: 'border-box',
              width: DRAWER_WIDTH,
              backgroundColor: 'background.paper',
              borderRight: '1px solid rgba(255, 255, 255, 0.12)',
            },
          }}
        >
          {drawer}
        </Drawer>
      </Box>

      {/* Main Content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { md: `calc(100% - ${sidebarOpen ? DRAWER_WIDTH : 0}px)` },
          mt: 8, // Account for AppBar height
          minHeight: 'calc(100vh - 64px)',
          backgroundColor: 'background.default',
        }}
      >
        <Outlet />
      </Box>

      {/* Error Snackbars */}
      {errors.map((error, index) => (
        <Snackbar
          key={error.id}
          open={true}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
          sx={{ bottom: { xs: 90 + index * 60, sm: 20 + index * 60 } }}
        >
          <Alert
            onClose={() => handleCloseError(error.id)}
            severity="error"
            variant="filled"
            action={
              <IconButton
                aria-label="close"
                color="inherit"
                size="small"
                onClick={() => handleCloseError(error.id)}
              >
                <CloseIcon fontSize="inherit" />
              </IconButton>
            }
          >
            {error.message}
          </Alert>
        </Snackbar>
      ))}
    </Box>
  );
}
