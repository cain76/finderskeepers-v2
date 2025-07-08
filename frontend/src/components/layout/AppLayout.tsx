// FindersKeepers v2 - Main Application Layout

import React from 'react';
import {
  AppBar,
  Box,
  CssBaseline,
  Drawer,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Typography,
  Badge,
  Chip,
  Alert,
  Snackbar,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Dashboard as DashboardIcon,
  Psychology as SessionsIcon,
  Description as DocumentsIcon,
  Search as SearchIcon,
  AccountTree as GraphIcon,
  MonitorHeart as MonitoringIcon,
  Settings as SettingsIcon,
  Notifications as NotificationsIcon,
  Close as CloseIcon,
} from '@mui/icons-material';
import { useNavigate, useLocation, Outlet } from 'react-router-dom';
import { useAppStore, useErrors, useConnectionStatus, useActiveSessionsCount } from '@/stores/appStore';
import { useWebSocket } from '@/hooks/useWebSocket';

const drawerWidth = 240;

interface NavigationItem {
  text: string;
  icon: React.ReactElement;
  path: string;
  badge?: number;
}

export default function AppLayout() {
  const [mobileOpen, setMobileOpen] = React.useState(false);
  const [snackbarOpen, setSnackbarOpen] = React.useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  
  const removeError = useAppStore(state => state.removeError);
  const errors = useErrors();
  const connectionStatus = useConnectionStatus();
  const activeSessionsCount = useActiveSessionsCount();
  
  // Setup WebSocket connection
  const { isConnected } = useWebSocket({
    onConnect: () => console.log('WebSocket connected'),
    onDisconnect: () => console.log('WebSocket disconnected'),
    onError: (error) => console.error('WebSocket error:', error),
  });

  // Show snackbar for new errors
  React.useEffect(() => {
    if (errors.length > 0 && errors[0].severity === 'critical') {
      setSnackbarOpen(true);
    }
  }, [errors]);

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const handleNavigation = (path: string) => {
    navigate(path);
    setMobileOpen(false);
  };

  const handleCloseSnackbar = () => {
    setSnackbarOpen(false);
    if (errors.length > 0) {
      removeError(errors[0].code);
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
      badge: activeSessionsCount,
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

  const getConnectionStatusColor = () => {
    if (connectionStatus.api === 'connected' && isConnected) {
      return 'success';
    } else if (connectionStatus.api === 'connected' || isConnected) {
      return 'warning';
    } else {
      return 'error';
    }
  };

  const getConnectionStatusText = () => {
    if (connectionStatus.api === 'connected' && isConnected) {
      return 'All systems operational';
    } else if (connectionStatus.api === 'connected') {
      return 'API connected, WebSocket offline';
    } else if (isConnected) {
      return 'WebSocket connected, API offline';
    } else {
      return 'Systems offline';
    }
  };

  const drawer = (
    <div>
      <Toolbar>
        <Typography variant="h6" noWrap component="div">
          FindersKeepers v2
        </Typography>
      </Toolbar>
      <List>
        {navigationItems.map((item) => (
          <ListItem key={item.text} disablePadding>
            <ListItemButton
              selected={location.pathname === item.path}
              onClick={() => handleNavigation(item.path)}
            >
              <ListItemIcon>
                {item.badge && item.badge > 0 ? (
                  <Badge badgeContent={item.badge} color="primary">
                    {item.icon}
                  </Badge>
                ) : (
                  item.icon
                )}
              </ListItemIcon>
              <ListItemText primary={item.text} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
    </div>
  );

  return (
    <Box sx={{ display: 'flex' }}>
      <CssBaseline />
      
      {/* App Bar */}
      <AppBar
        position="fixed"
        sx={{
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          ml: { sm: `${drawerWidth}px` },
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { sm: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            {navigationItems.find(item => item.path === location.pathname)?.text || 'Dashboard'}
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

      {/* Drawer */}
      <Box
        component="nav"
        sx={{ width: { sm: drawerWidth }, flexShrink: { sm: 0 } }}
        aria-label="navigation menu"
      >
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{
            keepMounted: true, // Better open performance on mobile.
          }}
          sx={{
            display: { xs: 'block', sm: 'none' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
        >
          {drawer}
        </Drawer>
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', sm: 'block' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
          open
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
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          minHeight: '100vh',
          backgroundColor: 'background.default',
        }}
      >
        <Toolbar />
        <Outlet />
      </Box>

      {/* Error Snackbar */}
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert
          onClose={handleCloseSnackbar}
          severity="error"
          variant="filled"
          action={
            <IconButton
              size="small"
              aria-label="close"
              color="inherit"
              onClick={handleCloseSnackbar}
            >
              <CloseIcon fontSize="small" />
            </IconButton>
          }
        >
          {errors.length > 0 && errors[0].message}
        </Alert>
      </Snackbar>
    </Box>
  );
}