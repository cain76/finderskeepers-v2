import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// Vite configuration for the redesigned FindersKeepers v2 frontend.
// This configuration enables the React plugin and exposes port 3000 on
// all network interfaces. Enhanced with proxy configuration for API calls
// and WebSocket connections to the FastAPI backend.
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  
  // Only expose VITE_ prefixed environment variables for security
  const clientEnv = Object.keys(env)
    .filter(key => key.startsWith('VITE_'))
    .reduce((filtered, key) => {
      filtered[`process.env.${key}`] = JSON.stringify(env[key])
      return filtered
    }, {})
  
  return {
    plugins: [react()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    server: {
      host: '0.0.0.0',
      port: 3000,
      proxy: {
        '/api': {
          target: env.VITE_API_URL || 'http://localhost:8000',
          changeOrigin: true,
          secure: false,
        },
        '/ws': {
          target: env.VITE_WS_URL || 'ws://localhost:8000',
          ws: true,
          changeOrigin: true,
        },
      },
    },
    define: clientEnv,
  }
})