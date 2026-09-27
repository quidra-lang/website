import eslintPluginAstro from 'eslint-plugin-astro';
import tseslint from 'typescript-eslint';

export default [
  { ignores: ['dist/**', '.astro/**', '.wrangler/**', 'node_modules/**'] },
  ...tseslint.configs.recommended,
  ...eslintPluginAstro.configs.recommended,
  ...eslintPluginAstro.configs['jsx-a11y-recommended'],
  {
    files: ['**/*.astro'],
    rules: {
      // A horizontally scrolling table container is made keyboard-reachable with
      // role="region" + aria-label + tabindex="0" (the documented pattern for
      // scrollable regions); the rule otherwise only allows interactive roles.
      'astro/jsx-a11y/no-noninteractive-tabindex': ['error', { roles: ['region', 'tabpanel'], allowExpressionValues: true }],
    },
  },
  {
    files: ['scripts/**/*.mjs'],
    languageOptions: { globals: { console: 'readonly', process: 'readonly', URL: 'readonly' } },
  },
];
