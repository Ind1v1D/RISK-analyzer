import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// The dev proxy forwards /api to FastAPI so the frontend can use relative
// URLs and we avoid CORS setup during development.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
