import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// While i work on my laptop, the React page runs on :5173 and Django on :8000.
// This proxy sends /api and /admin to Django, so the browser sees one site
// (no CORS setup and go extra packages needed).
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:8000',
      '/admin': 'http://127.0.0.1:8000',
      '/static': 'http://127.0.0.1:8000',
    },
  },
})
