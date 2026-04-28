import { defineConfig, type Plugin } from 'vite'
import { resolve } from 'path'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

const apiTarget = process.env.VITE_API_URL || 'http://localhost:8100'

/**
 * Rewrites /app and /app/* requests to serve app.html,
 * so the SPA handles all sub-routes under /app.
 */
function appFallback(): Plugin {
  return {
    name: 'app-fallback',
    configureServer(server) {
      server.middlewares.use((req, _res, next) => {
        if (req.url && (req.url === '/app' || req.url.startsWith('/app/'))) {
          req.url = '/app.html'
        }
        next()
      })
    },
  }
}

export default defineConfig({
  plugins: [react(), tailwindcss(), appFallback()],
  build: {
    rollupOptions: {
      input: {
        marketing: resolve(__dirname, 'index.html'),
        app: resolve(__dirname, 'app.html'),
      },
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/parse': apiTarget,
      '/classify': apiTarget,
      '/health': apiTarget,
      '/extract-approval': apiTarget,
      '/review': apiTarget,
      '/templates': apiTarget,
      '/v1': apiTarget,
    },
  },
})
