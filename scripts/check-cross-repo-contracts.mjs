#!/usr/bin/env node
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const root = resolve(import.meta.dirname, '..');
const index = readFileSync(resolve(root, 'src/pages/index.astro'), 'utf8');
const started = readFileSync(resolve(root, 'src/pages/get-started.astro'), 'utf8');
const combined = index + '\n' + started;

const stale = [
  'It has no Run button',
  'It deliberately has no Run button',
  'nothing uploaded anywhere',
  'source never leaves the tab',
  'neural autodiff foundation',
];

const problems = [];
for (const phrase of stale) {
  if (combined.includes(phrase)) problems.push(`stale cross-repository claim: ${phrase}`);
}

for (const [label, source, required] of [
  ['home', index, [
    'same language version and exact Core commit',
    '<li><b>Build</b>',
    '<li><b>Run</b>',
    'sandboxed native runner',
    'Core tensor/autograd primitives',
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
