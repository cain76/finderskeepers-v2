import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Vite configuration for the redesigned FindersKeepers v2 frontend.
// This configuration enables the React plugin and exposes port 3000 on
// all network interfaces. It deliberately keeps things simple
// so that the Dockerfile can run `npm run dev` without needing
// any additional arguments beyond the host and port.
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 3000,
  },
});