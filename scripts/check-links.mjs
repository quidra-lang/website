#!/usr/bin/env node
/**
 * Verifies every internal link, asset reference and fragment in the built site.
 *
 *   node scripts/check-links.mjs [dist]            internal targets only
 *   node scripts/check-links.mjs [dist] --external also HEAD/GET every external URL
 *
 * No dependencies: the HTML is our own build output, so a conservative regex
 * over href/src/srcset attributes is sufficient.
 */
import { readdirSync, readFileSync, statSync, existsSync } from 'node:fs';
import { join, dirname, resolve, extname } from 'node:path';

const args = process.argv.slice(2);
const dist = resolve(args.find((a) => !a.startsWith('--')) ?? 'dist');
const checkExternal = args.includes('--external');
/** Absolute URLs on the site's own origin (canonical links, JSON-LD) are checked as internal paths. */
const SITE_ORIGIN = 'https://quidra-lang.com';

if (!existsSync(dist)) {
  console.error(`check-links: ${dist} does not exist. Run the build first.`);
  process.exit(2);
}

function walk(dir) {
  return readdirSync(dir).flatMap((name) => {
    const full = join(dir, name);
    return statSync(full).isDirectory() ? walk(full) : [full];
  });
}

const htmlFiles = walk(dist).filter((f) => f.endsWith('.html'));
const ids = new Map(); // file -> Set(ids)
const problems = [];
const external = new Map(); // url -> [pages]

const attr = /\b(?:href|src)=["']([^"']+)["']/g;
const idAttr = /\bid=["']([^"']+)["']/g;

for (const file of htmlFiles) {
  const html = readFileSync(file, 'utf8');
  ids.set(file, new Set(Array.from(html.matchAll(idAttr), (m) => m[1])));
}

function resolveTarget(fromFile, url) {
  const [pathPart, hash] = url.split('#');
  let target;
  if (pathPart === '') target = fromFile;
  else if (pathPart.startsWith('/')) target = join(dist, pathPart);
  else target = resolve(dirname(fromFile), pathPart);
  if (extname(target) === '') target = join(target, 'index.html');
  return { target, hash };
}

for (const file of htmlFiles) {
  const html = readFileSync(file, 'utf8');
  const page = file.slice(dist.length);
  for (const match of html.matchAll(attr)) {
    let url = match[1];
    if (url.startsWith('mailto:') || url.startsWith('data:') || url.startsWith('javascript:')) continue;
    if (url === SITE_ORIGIN || url.startsWith(`${SITE_ORIGIN}/`)) url = url.slice(SITE_ORIGIN.length) || '/';
    if (/^https?:\/\//.test(url)) {
      if (!external.has(url)) external.set(url, []);
      external.get(url).push(page);
      continue;
    }
    if (url.startsWith('//')) {
      problems.push(`${page}: protocol-relative URL ${url}`);
      continue;
    }
    const { target, hash } = resolveTarget(file, url);
    if (!existsSync(target)) {
      problems.push(`${page}: broken link ${url} (expected ${target.slice(dist.length)})`);
      continue;
    }
    if (hash) {
      const targetIds = ids.get(target);
      if (targetIds && !targetIds.has(hash)) problems.push(`${page}: missing fragment #${hash} in ${url}`);
    }
    const pathOnly = url.split('#')[0];
    if (pathOnly.startsWith('/') && !pathOnly.endsWith('/') && extname(pathOnly) === '') {
      problems.push(`${page}: internal link without trailing slash ${url}`);
    }
  }
}

console.log(`check-links: ${htmlFiles.length} pages, ${external.size} distinct external URLs`);

if (checkExternal) {
  const results = await Promise.all(
    Array.from(external.keys()).map(async (url) => {
      try {
        let response = await fetch(url, { method: 'HEAD', redirect: 'follow' });
        if (response.status === 405 || response.status === 403) response = await fetch(url, { method: 'GET', redirect: 'follow' });
        return { url, ok: response.ok, status: response.status };
      } catch (error) {
        return { url, ok: false, status: String(error) };
      }
    }),
  );
  for (const r of results) {
    if (!r.ok) problems.push(`external ${r.status}: ${r.url} (on ${external.get(r.url).join(', ')})`);
  }
  console.log(`check-links: ${results.filter((r) => r.ok).length}/${results.length} external URLs reachable`);
}

if (problems.length) {
  for (const p of problems) console.error(`  ✗ ${p}`);
  process.exit(1);
}
console.log('check-links: OK');
