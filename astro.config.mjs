// @ts-check
import { defineConfig, fontProviders } from 'astro/config';
import sitemap from '@astrojs/sitemap';

// The official Quidra website: a fully static site, pre-rendered at build time.
// No adapter, no server code, no runtime configuration.
export default defineConfig({
  site: 'https://quidra-lang.com',
  trailingSlash: 'always',
  compressHTML: true,
  integrations: [sitemap()],
  fonts: [
    {
      provider: fontProviders.local(),
      name: 'Inter',
      cssVariable: '--font-sans',
      fallbacks: ['system-ui', 'sans-serif'],
      options: {
        variants: [
          {
            weight: '100 900',
            style: 'normal',
            src: ['./src/assets/fonts/inter-latin-wght-normal.woff2'],
          },
        ],
      },
    },
    {
      provider: fontProviders.local(),
      name: 'IBM Plex Mono',
      cssVariable: '--font-mono',
      fallbacks: ['ui-monospace', 'Menlo', 'monospace'],
      options: {
        variants: [
          { weight: 400, style: 'normal', src: ['./src/assets/fonts/ibm-plex-mono-latin-400-normal.woff2'] },
          { weight: 500, style: 'normal', src: ['./src/assets/fonts/ibm-plex-mono-latin-500-normal.woff2'] },
          { weight: 600, style: 'normal', src: ['./src/assets/fonts/ibm-plex-mono-latin-600-normal.woff2'] },
        ],
      },
    },
  ],
});
