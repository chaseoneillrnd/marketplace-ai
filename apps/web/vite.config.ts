/// <reference types="vitest" />
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  root: __dirname,
  plugins: [react()],
  resolve: {
    alias: {
      '@skillhub/shared-types': path.resolve(__dirname, '../../libs/shared-types/src/index.ts'),
      '@skillhub/ui': path.resolve(__dirname, '../../libs/ui/src/index.ts'),
    },
  },
  server: {
    port: 5173,
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test-setup.ts'],
    css: true,
  },
});
