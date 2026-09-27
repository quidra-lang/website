#!/usr/bin/env node
/**
 * Post-build step: writes dist/_headers from public/_headers plus a strict
 * Content-Security-Policy whose script-src allows only same-origin scripts and
 * the exact inline scripts Astro emitted (by SHA-256 hash). Runs as part of
 * `npm run build`; the site has no analytics, no third-party scripts and no
 * remote fonts, so nothing else needs to be allowed.
 *
 *   node scripts/write-headers.mjs [dist]
 */
import { createHash } from 'node:crypto';
import { readdirSync, readFileSync, statSync, writeFileSync, existsSync } from 'node:fs';
import { join, resolve } from 'node:path';

const root = resolve(new URL('..', import.meta.url).pathname);
const dist = resolve(process.argv[2] ?? join(root, 'dist'));
const template = readFileSync(join(root, 'public', '_headers'), 'utf8');

if (!existsSync(dist)) {
  console.error(`write-headers: ${dist} does not exist. Run astro build first.`);
  process.exit(2);
}

function walk(dir) {
  return readdirSync(dir).flatMap((name) => {
    const full = join(dir, name);
    return statSync(full).isDirectory() ? walk(full) : [full];
  });
}

const hashes = new Set();
let inlineCount = 0;
for (const file of walk(dist).filter((f) => f.endsWith('.html'))) {
  const html = readFileSync(file, 'utf8');
  for (const match of html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)) {
    const attrs = match[1];
    const body = match[2];
    if (/\bsrc\s*=/.test(attrs)) continue; // external: covered by 'self'
    if (/type\s*=\s*["']application\/ld\+json["']/i.test(attrs)) continue; // data, not executed
    if (!body.trim()) continue;
    hashes.add(`'sha256-${createHash('sha256').update(body, 'utf8').digest('base64')}'`);
    inlineCount++;
  }
}

const csp = [
  "default-src 'self'",
  `script-src 'self' ${Array.from(hashes).sort().join(' ')}`.trim(),
  "style-src 'self' 'unsafe-inline'",
  "img-src 'self' data:",
  "font-src 'self'",
  "connect-src 'self'",
  "manifest-src 'self'",
  "object-src 'none'",
  "base-uri 'self'",
  "form-action 'self'",
  "frame-ancestors 'none'",
  'upgrade-insecure-requests',
].join('; ');

// Insert the CSP into the first "/*" block of the template.
const lines = template.split('\n');
const index = lines.findIndex((line) => line.trim() === '/*');
if (index === -1) {
  console.error('write-headers: public/_headers has no "/*" block');
  process.exit(2);
}
lines.splice(index + 1, 0, `  Content-Security-Policy: ${csp}`);
writeFileSync(join(dist, '_headers'), lines.join('\n'));
console.log(`write-headers: ${inlineCount} inline script(s), ${hashes.size} distinct hash(es) → ${join(dist, '_headers')}`);
