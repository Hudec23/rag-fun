import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: { '/api': { target: process.env.API_PROXY_TARGET ?? 'http://localhost:8000' } },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['tests/setup/setup.ts'],
    include: ['tests/**/*.test.{ts,tsx}'],
    css: false,
  },
})
