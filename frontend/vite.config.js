import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// In production the container's nginx serves the build and proxies /api and
// /tiles. These proxies mirror that so dev behaves identically.
const proxy = {
  '/api': {
    target: 'http://127.0.0.1:8000',
    changeOrigin: true,
  },
  '/tiles': {
    target: 'https://server.arcgisonline.com',
    changeOrigin: true,
    secure: true,
    rewrite: (path) => path.replace(/^\/tiles/, '/ArcGIS/rest/services'),
  },
}

export default defineConfig({
  plugins: [react()],
  server: { port: 3000, proxy },
  preview: { port: 3000, proxy },
})
