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

// Keep every example on the current Core output API. Diagnostic fixtures are
// source-revision-locked, so any intentional edit updates their golden metadata.
for (const [directory, entries] of [
  ["examples", exampleManifest.examples],
  ["examples/invalid", exampleManifest.invalid],
]) {
  for (const entry of entries) {
    const path = `${directory}/${entry.file}`;
    const source = readFileSync(resolve(root, path), "utf8");
    if (/\bprint(?:\s*\.\s*line\s*\(|\(NL\))/.test(source)) {
      problems.push(`${path}: use println for console line output`);
    }
  }
}
if (/\bprint(?:\s*\.\s*line\s*\(|\(NL\))/.test(combined)) {
  problems.push("published documentation still uses obsolete console line output syntax");
}

if (!docs.includes('map<K, V> and distinct<T> collections')) {
  problems.push('docs index: missing current develop collection type names');
}
if (!docs.includes('set is available for user functions')) {
  problems.push('docs index: user-defined set naming is not documented');
}

const grammar = JSON.parse(readFileSync(resolve(root, 'src/lib/quidra.tmLanguage.json'), 'utf8'));
const collectionTypes = grammar.repository?.['primitive-type']?.match ?? '';
if (!collectionTypes.includes('map(?=\\s*<)') ||
    !collectionTypes.includes('distinct(?=\\s*<)') ||
    collectionTypes.includes('set(?=\\s*<)')) {
  problems.push('TextMate grammar: collection names are out of sync with Core');
}

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
if (siteVersion?.startsWith('0.5.') && /const hello\s*=\s*`println\(/.test(started)) {
  problems.push('get-started: the public Quidra 0.5 compiler does not support println');
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
    'Core provides the language, tensors, numeric reductions, autograd, devices and extension mechanisms.',
    'First-party packages provide linear algebra',
    'collections, text parsing, encoding, reusable neural-network semantics, image processing, video decoding and concrete DNN model architectures.',
    'The cards below describe the current development architecture.',
    'The released compiler and install instructions on this',
    'const developTree = (href: string) => `${href}/tree/develop`;',
    'developTree(links.core)',
    'developTree(links.playgroundRepo)',
    'developTree(links.math)',
    'developTree(links.collections)',
    'developTree(links.text)',
    'developTree(links.encoding)',
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
