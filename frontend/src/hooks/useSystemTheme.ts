// FindersKeepers v2 - System Theme Detection Hook

import { useEffect, useState } from 'react';
import { useTheme } from '../stores/appStore';

export const useSystemTheme = () => {
  const { theme, resolvedTheme, setTheme } = useTheme();
  const [systemPreference, setSystemPreference] = useState<'light' | 'dark'>('light');

  useEffect(() => {
    // Initial system preference detection
    if (typeof window === 'undefined') return;
    
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const initialPreference = mediaQuery.matches ? 'dark' : 'light';
    setSystemPreference(initialPreference);

    // Listen for system preference changes
    const handleChange = (e: MediaQueryListEvent) => {
      const newPreference = e.matches ? 'dark' : 'light';
      setSystemPreference(newPreference);
      
      // If user has system theme selected, update resolved theme
      if (theme === 'system') {
        // Force re-evaluation by setting theme again
        setTheme('system');
      }
    };

    // Add event listener
    mediaQuery.addEventListener('change', handleChange);

    // Cleanup
    return () => {
      mediaQuery.removeEventListener('change', handleChange);
    };
  }, [theme, setTheme]);

  return {
    systemPreference,
    isSystemDark: systemPreference === 'dark',
    isSystemLight: systemPreference === 'light',
  };
};

export default useSystemTheme;