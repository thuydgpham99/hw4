import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  // vite.config.ts runs before Vite loads .env files, so process.env does not
  // see them — loadEnv is what reads .env / .env.local here.
  const env = loadEnv(mode, process.cwd(), '')

  return {
    plugins: [react()],
    server: {
      // Honour PORT when the environment assigns one; otherwise Vite's default.
      port: env.PORT ? Number(env.PORT) : undefined,
      proxy: {
        // Defaults to the port the assignment specifies. Override with
        // VITE_API_TARGET in frontend/.env.local when 8000 is already taken.
        '/api': {
          target: env.VITE_API_TARGET || 'http://127.0.0.1:8000',
          changeOrigin: true,
          // Agent replies involve several model round trips, so the proxy must
          // not give up before the backend answers.
          timeout: 120_000,
          proxyTimeout: 120_000,
        },
      },
    },
  }
})
