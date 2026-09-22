import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { uipathCodedApps } from '@uipath/coded-apps-dev';

export default defineConfig({
  base: './',
  plugins: [react(), uipathCodedApps()],
});
