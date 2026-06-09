import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/test/setup.ts',
    include: ['src/test/**/*.{test,spec}.{ts,tsx}'],
    exclude: ['node_modules', 'e2e/**', '.next/**'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'lcov', 'html'],
      exclude: [
        'node_modules/**',
        'src/test/**',
        '**/*.config.*',
        '**/e2e/**',
        'src/app/**',       
        '.next/**',
      ],
      
      thresholds: {
        lines: 0,
        functions: 0,
        branches: 0,
      },
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
})
