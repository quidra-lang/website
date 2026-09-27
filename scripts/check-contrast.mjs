#!/usr/bin/env node
/**
 * WCAG contrast check for the site palette (src/styles/global.css) and the two
 * Shiki syntax themes (src/lib/shiki-theme.ts). Fails when body text falls
 * below 4.5:1 or large/UI text below 3:1.
 */
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const root = resolve(new URL('..', import.meta.url).pathname);
const css = readFileSync(resolve(root, 'src/styles/global.css'), 'utf8');
const themeSource = readFileSync(resolve(root, 'src/lib/shiki-theme.ts'), 'utf8');

function parseTokens(source) {
  const light = {};
  const dark = {};
  for (const m of source.matchAll(/--([\w-]+):\s*light-dark\((#[0-9a-f]{6}),\s*(#[0-9a-f]{6})\)/gi)) {
    light[m[1]] = m[2];
    dark[m[1]] = m[3];
  }
  return { light, dark };
}

function parsePalette(source, name) {
  const block = source.match(new RegExp(`const ${name}: Palette = \\{([^}]+)\\}`))[1];
  return Object.fromEntries(Array.from(block.matchAll(/(\w+):\s*'(#[0-9a-f]{6})'/gi), (m) => [m[1], m[2]]));
}

function luminance(hex) {
  const [r, g, b] = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255).map((c) => (c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4));
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}
function contrast(a, b) {
  const [l1, l2] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (l1 + 0.05) / (l2 + 0.05);
}

const tokens = parseTokens(css);
const palettes = { light: parsePalette(themeSource, 'light'), dark: parsePalette(themeSource, 'dark') };
let failures = 0;

function check(label, fg, bg, min) {
  const ratio = contrast(fg, bg);
  const ok = ratio >= min;
  if (!ok) failures++;
  console.log(`${ok ? '✓' : '✗'} ${label.padEnd(44)} ${fg} on ${bg}  ${ratio.toFixed(2)}:1  (min ${min})`);
}

for (const mode of ['light', 'dark']) {
  const t = tokens[mode];
  console.log(`\n${mode} palette`);
  check('fg on bg', t.fg, t.bg, 4.5);
  check('fg-2 on bg', t['fg-2'], t.bg, 4.5);
  check('fg-3 on bg (small labels)', t['fg-3'], t.bg, 4.5);
  check('fg-2 on bg-2', t['fg-2'], t['bg-2'], 4.5);
  check('fg-3 on bg-2', t['fg-3'], t['bg-2'], 4.5);
  check('accent-text on bg (links)', t['accent-text'], t.bg, 4.5);
  check('accent-text on bg-code', t['accent-text'], t['bg-code'], 4.5);
  check('accent-ink on accent (buttons)', t['accent-ink'], t.accent, 4.5);
  check('rule-strong on bg (borders, non-text)', t['rule-strong'], t.bg, 1.2);
  check('ok on bg', t.ok, t.bg, 4.5);
  check('err on bg-2 (diagnostics)', t.err, t['bg-2'], 4.5);

  const p = palettes[mode];
  console.log(`${mode} syntax theme on code background ${p.bg}`);
  for (const [name, color] of Object.entries(p)) {
    if (name === 'bg') continue;
    check(`syntax ${name}`, color, p.bg, 4.5);
  }
}

console.log(failures ? `\n${failures} contrast failure(s)` : '\nAll contrast checks passed');
process.exit(failures ? 1 : 0);
