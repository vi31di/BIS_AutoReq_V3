import { defineConfig } from 'vite';
import { resolve } from 'path';

export default defineConfig({
  root: 'src',
  build: {
    outDir: '../dist',
    emptyOutDir: true,
    rollupOptions: {
      input: {
        index: resolve(__dirname, 'src/index.html'),
        main: resolve(__dirname, 'src/pages/index.html'),
        library: resolve(__dirname, 'src/pages/library.html'),
        login: resolve(__dirname, 'src/pages/login.html')
      }
    }
  },
  server: {
    port: 3000,
    open: '/pages/index.html'
  }
});
