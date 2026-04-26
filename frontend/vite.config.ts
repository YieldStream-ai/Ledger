import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

const apiTarget = process.env.VITE_API_URL || 'http://localhost:8100'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      '/parse': apiTarget,
      '/classify': apiTarget,
      '/health': apiTarget,
      '/extract-approval': apiTarget,
      '/v1': apiTarget,
    },
  },
})
