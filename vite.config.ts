import { defineConfig } from 'vite';

// LOPAD build config. Phaser is split into its own chunk so game code rebuilds stay small.
export default defineConfig({
  base: './',
  server: { port: 8080 },
  build: {
    rollupOptions: {
      output: { manualChunks: { phaser: ['phaser'] } },
    },
  },
});
