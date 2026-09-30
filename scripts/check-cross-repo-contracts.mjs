#!/usr/bin/env node
import { execFileSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const root = resolve(import.meta.dirname, '..');
const index = readFileSync(resolve(root, 'src/pages/index.astro'), 'utf8');
const started = readFileSync(resolve(root, 'src/pages/get-started.astro'), 'utf8');
const docs = readFileSync(resolve(root, 'src/pages/docs.astro'), 'utf8');
const siteConfig = readFileSync(resolve(root, 'src/config/site.ts'), 'utf8');
const exampleManifest = JSON.parse(readFileSync(resolve(root, 'examples/manifest.json'), 'utf8'));
const combined = index + '\n' + started + '\n' + docs;

const stale = [
  'It has no Run button',
  'It deliberately has no Run button',
  'nothing uploaded anywhere',
  'source never leaves the tab',
  'neural autodiff foundation',
  'neural values',
];

const problems = [];

const siteVersion = /quidraVersion:\s*'([^']+)'/.exec(siteConfig)?.[1];
let coreRef = process.env.QUIDRA_CORE_REF ?? '';
if (!coreRef) {
  try {
    coreRef = execFileSync('git', ['branch', '--show-current'], {
      cwd: root,
      encoding: 'utf8',
      stdio: ['ignore', 'pipe', 'ignore'],
    }).trim();
  } catch {
    coreRef = '';
  }
}

if (!siteVersion) {
  problems.push('site config: could not read quidraVersion');
}
if (!/^quidra \d+\.\d+\.\d+$/.test(String(exampleManifest.compiler))) {
  problems.push(`examples manifest: invalid compiler identity: ${String(exampleManifest.compiler)}`);
}
if (coreRef === 'main' && siteVersion && exampleManifest.compiler !== `quidra ${siteVersion}`) {
  problems.push(
    `main release drift: site config says ${siteVersion}, examples manifest says ${String(exampleManifest.compiler)}`,
  );
}

for (const phrase of stale) {
  if (combined.includes(phrase)) problems.push(`stale cross-repository claim: ${phrase}`);
}

for (const [label, source, required] of [
  ['home', index, [
    'same language version and exact Core commit',
    '<li><b>Build</b>',
    '<li><b>Run</b>',
    'sandboxed native runner',
    'Core keeps language, tensor, autograd, device and extension mechanisms.',
    'Generic mathematics, reusable neural-network',
    'concrete DNN model architectures live in explicit first-party packages',
    'The cards below describe the current development architecture.',
    'The released compiler and install instructions on this',
    'const developTree = (href: string) => `${href}/tree/develop`;',
    'developTree(links.core)',
    'developTree(links.playgroundRepo)',
    'developTree(links.math)',
    'developTree(links.nn)',
    'developTree(links.vision)',
    'developTree(links.video)',
    'developTree(links.dnn)',
  ]],
  ['get-started', started, [
    'Build and Run send source only when you',
    'separately sandboxed native runner',
    'language version and exact',
    'Core commit match the WebAssembly frontend',
  ]],
]) {
  for (const phrase of required) {
    if (!source.includes(phrase)) problems.push(`${label}: missing contract text: ${phrase}`);
  }
}

if (problems.length) {
  for (const problem of problems) console.error(`  ✗ ${problem}`);
  process.exit(1);
}
console.log('cross-repository copy contracts: OK');
