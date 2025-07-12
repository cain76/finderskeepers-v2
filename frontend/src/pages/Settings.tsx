// FindersKeepers v2 - Settings Page

import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  FormControl,
  FormLabel,
  RadioGroup,
  FormControlLabel,
  Radio,
  Divider,
  Button,
  Chip,
  Stack,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  LightMode as LightModeIcon,
  DarkMode as DarkModeIcon,
  SettingsBrightness as SystemIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { useTheme } from '../stores/appStore';
import useSystemTheme from '../hooks/useSystemTheme';

const Settings: React.FC = () => {
  const { theme, resolvedTheme, setTheme, toggleTheme, isDark, isLight, isSystem } = useTheme();
  const { systemPreference, isSystemDark } = useSystemTheme();

  const handleThemeChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const newTheme = event.target.value as 'light' | 'dark' | 'system';
    setTheme(newTheme);
  };

  const getThemeIcon = (themeMode: string) => {
    switch (themeMode) {
      case 'light':
        return <LightModeIcon fontSize="small" />;
      case 'dark':
        return <DarkModeIcon fontSize="small" />;
      case 'system':
        return <SystemIcon fontSize="small" />;
      default:
        return <SystemIcon fontSize="small" />;
    }
  };

  const getStatusColor = (themeMode: string) => {
    if (themeMode === theme) {
      return 'primary';
    }
    return 'default';
  };

  return (
    <Box sx={{ maxWidth: 800, mx: 'auto', p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Settings
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Configure your FindersKeepers v2 preferences
      </Typography>

      <Stack spacing={3}>
        {/* Theme Settings */}
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6" sx={{ flexGrow: 1 }}>
                Appearance
              </Typography>
              <Tooltip title="Toggle between light and dark">
                <IconButton onClick={toggleTheme} color="primary">
                  {isDark ? <LightModeIcon /> : <DarkModeIcon />}
                </IconButton>
              </Tooltip>
            </Box>

            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Choose how FindersKeepers looks to you. Select a single theme, or sync with your system and automatically switch between day and night themes.
            </Typography>

            <FormControl component="fieldset">
              <FormLabel component="legend" sx={{ mb: 2 }}>
                Theme Mode
              </FormLabel>
              <RadioGroup
                value={theme}
                onChange={handleThemeChange}
                sx={{ gap: 1 }}
              >
                <FormControlLabel
                  value="light"
                  control={<Radio />}
                  label={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <LightModeIcon fontSize="small" />
                      <span>Light</span>
                      {isLight && (
                        <Chip size="small" label="Active" color="primary" variant="outlined" />
                      )}
                    </Box>
                  }
                />
                <FormControlLabel
                  value="dark"
                  control={<Radio />}
                  label={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <DarkModeIcon fontSize="small" />
                      <span>Dark</span>
                      {isDark && !isSystem && (
                        <Chip size="small" label="Active" color="primary" variant="outlined" />
                      )}
                    </Box>
                  }
                />
                <FormControlLabel
                  value="system"
                  control={<Radio />}
                  label={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <SystemIcon fontSize="small" />
                      <span>System</span>
                      {isSystem && (
                        <Chip 
                          size="small" 
                          label={`Active (${systemPreference})`} 
                          color="primary" 
                          variant="outlined" 
                        />
                      )}
                    </Box>
                  }
                />
              </RadioGroup>
            </FormControl>

            <Divider sx={{ my: 3 }} />

            {/* Theme Status */}
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Current Status
              </Typography>
              <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                <Chip
                  icon={getThemeIcon(theme)}
                  label={`Preference: ${theme.charAt(0).toUpperCase() + theme.slice(1)}`}
                  color={getStatusColor(theme)}
                  variant="outlined"
                />
                <Chip
                  icon={getThemeIcon(resolvedTheme)}
                  label={`Applied: ${resolvedTheme.charAt(0).toUpperCase() + resolvedTheme.slice(1)}`}
                  color="primary"
                />
                {isSystem && (
                  <Chip
                    icon={getThemeIcon(systemPreference)}
                    label={`System: ${systemPreference.charAt(0).toUpperCase() + systemPreference.slice(1)}`}
                    color="secondary"
                    variant="outlined"
                  />
                )}
              </Box>
            </Box>
          </CardContent>
        </Card>

        {/* Application Settings */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Application
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              General application preferences and behavior settings.
            </Typography>
            
            <Stack spacing={2}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Typography variant="body1">
                  Real-time updates
                </Typography>
                <Chip label="Enabled" color="success" size="small" />
              </Box>
              
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Typography variant="body1">
                  Vector search
                </Typography>
                <Chip label="Enabled" color="success" size="small" />
              </Box>
              
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Typography variant="body1">
                  Knowledge graph
                </Typography>
                <Chip label="Enabled" color="success" size="small" />
              </Box>
            </Stack>
          </CardContent>
        </Card>

        {/* Quick Actions */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Quick Actions
            </Typography>
            <Stack direction="row" spacing={2} sx={{ mt: 2 }}>
              <Button
                variant="outlined"
                startIcon={<RefreshIcon />}
                onClick={() => window.location.reload()}
              >
                Refresh Application
              </Button>
              <Button
                variant="outlined"
                startIcon={isDark ? <LightModeIcon /> : <DarkModeIcon />}
                onClick={toggleTheme}
              >
                Toggle Theme
              </Button>
            </Stack>
          </CardContent>
        </Card>
      </Stack>
    </Box>
  );
};

export default Settings;