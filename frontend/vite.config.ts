import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@components': path.resolve(__dirname, './src/components'),
      '@pages': path.resolve(__dirname, './src/pages'),
      '@services': path.resolve(__dirname, './src/services'),
      '@types': path.resolve(__dirname, './src/types'),
      '@utils': path.resolve(__dirname, './src/utils'),
    },
  },
  server: {
    port: 3000,
    host: true,
    proxy: {
      '/api': {
        target: 'http://fastapi:80',  // Using Docker service name
        changeOrigin: true,
        secure: false,
      },
      '/health': {
        target: 'http://fastapi:80',  // Using Docker service name
        changeOrigin: true,
        secure: false,
      },
      '/docs': {
        target: 'http://fastapi:80',  // Using Docker service name
        changeOrigin: true,
        secure: false,
      },
      '/ws': {
        target: 'ws://fastapi:80',  // Using Docker service name
        ws: true,
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    chunkSizeWarningLimit: 1600,
  },
  define: {
    'process.env': {},
  },
})
