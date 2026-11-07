#!/usr/bin/env node
// Verifies the Quidra TextMate grammar (src/lib/quidra.tmLanguage.json) with Shiki.
//
// Usage:
//   node scripts/check-grammar.mjs [--dump FILE] [--js-engine] [EXTRA_PATH...]
//
// Default corpus: every *.qui under website/examples (recursively) plus every
// *.qui under the core compiler checkout's examples/ directory (recursively).
// EXTRA_PATH arguments (files or directories) are added to the corpus.
//
// The core checkout is resolved as ../quidra relative to the website root, or
// from the QUIDRA_CORE_DIR environment variable.
//
// Exit code 1 when a keyword, operator, string, number, or comment token is
// left with only the base scope (or when the grammar itself is malformed).

import { readFileSync, readdirSync, statSync, existsSync } from 'node:fs';
import { dirname, join, resolve, relative, extname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHighlighter, createJavaScriptRegexEngine } from 'shiki';

const scriptDir = dirname(fileURLToPath(import.meta.url));
const websiteRoot = resolve(scriptDir, '..');
const grammarPath = join(websiteRoot, 'src', 'lib', 'quidra.tmLanguage.json');
const siteExamplesDir = join(websiteRoot, 'examples');
const coreDir = process.env.QUIDRA_CORE_DIR
  ? resolve(process.env.QUIDRA_CORE_DIR)
  : resolve(websiteRoot, '..', 'quidra');
const coreExamplesDir = join(coreDir, 'examples');

const BASE_SCOPE = 'source.quidra';
const LANG = 'quidra';
const THEME = 'github-dark';

// Identifier-shaped tokens that must never be left unscoped. Everything here is
// confirmed by docs/spec/grammar.ebnf, docs/spec/language.md, and src/lexer.cpp.
const RESERVED_WORDS = new Set([
  // control flow
  'if', 'elif', 'else', 'for', 'while', 'match', 'return', 'break', 'continue', 'try', 'then', 'parallel',
  // declarations and modifiers
  'import', 'public', 'extern', 'cli', 'enum', 'class', 'private', 'const', 'local', 'export', 'literal',
  // operators spelled as words
  'and', 'or', 'not', 'AND', 'OR', 'XOR', 'NOT',
  // literals
  'true', 'false', 'none', 'void', 'inf',
  // control-character constants
  'NL', 'HT', 'CR', 'DQ', 'BS', 'FF', 'VT', 'BL',
  // built-in types
  'int', 'int8', 'int16', 'int32', 'int64', 'bool', 'string', 'bin', 'error',
  'tensor', 'func', 'Iterator', 'map', 'distinct', 'nat', 'nat8', 'nat16', 'nat32', 'nat64',
  'real', 'real16', 'real16b', 'real32', 'real64', 'com', 'com16', 'com16b', 'com32', 'com64',
]);

const IDENTIFIER = /^[A-Za-z_][A-Za-z0-9_]*$/;

// ---------------------------------------------------------------------------
// CLI parsing
// ---------------------------------------------------------------------------

const argv = process.argv.slice(2);
let dumpFile = null;
let useJsEngine = false;
const extraPaths = [];
for (let i = 0; i < argv.length; i += 1) {
  const arg = argv[i];
  if (arg === '--dump') {
    dumpFile = argv[i + 1];
    if (!dumpFile) fail('--dump requires a FILE argument');
    i += 1;
  } else if (arg.startsWith('--dump=')) {
    dumpFile = arg.slice('--dump='.length);
  } else if (arg === '--js-engine') {
    useJsEngine = true;
  } else if (arg === '--help' || arg === '-h') {
    printUsage();
    process.exit(0);
  } else if (arg.startsWith('--')) {
    fail(`unknown option ${arg}`);
  } else {
    extraPaths.push(resolve(arg));
  }
}

function printUsage() {
  console.log('usage: node scripts/check-grammar.mjs [--dump FILE] [--js-engine] [EXTRA_PATH...]');
}

function fail(message) {
  console.error(`check-grammar: ${message}`);
  process.exit(1);
}

// ---------------------------------------------------------------------------
// Grammar loading and structural validation
// ---------------------------------------------------------------------------

const grammar = JSON.parse(readFileSync(grammarPath, 'utf8'));
validateGrammar(grammar);

function validateGrammar(g) {
  const problems = [];
  if (g.name !== LANG) problems.push(`"name" must be "${LANG}" (got ${JSON.stringify(g.name)})`);
  if (g.scopeName !== BASE_SCOPE) problems.push(`"scopeName" must be "${BASE_SCOPE}"`);
  if (!Array.isArray(g.fileTypes) || !g.fileTypes.includes('qui')) problems.push('"fileTypes" must include "qui"');
  if (!Array.isArray(g.patterns) || g.patterns.length === 0) problems.push('"patterns" must be a non-empty array');
  if (typeof g.repository !== 'object' || g.repository === null) problems.push('"repository" must be an object');

  const repositoryKeys = new Set(Object.keys(g.repository ?? {}));
  const includes = new Set();
  const scopeNames = new Set();
  walk(g, (node) => {
    if (typeof node.include === 'string') includes.add(node.include);
    if (typeof node.name === 'string' && node !== g) scopeNames.add(node.name);
    if (typeof node.match === 'string') compileCheck(node.match, problems);
    if (typeof node.begin === 'string') compileCheck(node.begin, problems);
    if (typeof node.end === 'string') compileCheck(node.end, problems);
  });
  for (const inc of includes) {
    if (inc === '$self' || inc === '$base') continue;
    if (!inc.startsWith('#')) {
      problems.push(`external include ${inc} is not allowed in a self-contained grammar`);
      continue;
    }
    if (!repositoryKeys.has(inc.slice(1))) problems.push(`include ${inc} does not exist in the repository`);
  }
  for (const key of repositoryKeys) {
    if (!includes.has(`#${key}`)) problems.push(`repository rule #${key} is never included`);
  }
  for (const name of scopeNames) {
    if (name !== BASE_SCOPE && !name.endsWith('.quidra')) problems.push(`scope ${name} does not end with .quidra`);
  }
  if (problems.length > 0) {
    console.error('Grammar structure problems:');
    for (const p of problems) console.error(`  - ${p}`);
    process.exit(1);
  }
}

function walk(node, visit) {
  if (Array.isArray(node)) {
    for (const item of node) walk(item, visit);
    return;
  }
  if (typeof node !== 'object' || node === null) return;
  visit(node);
  for (const value of Object.values(node)) walk(value, visit);
}

// Only a syntax sanity check: Oniguruma is the authoritative engine. The JS
// RegExp constructor rejects a few Oniguruma-only constructs, so a failure here
// is reported as a warning rather than a structural problem.
function compileCheck(source) {
  try {
    new RegExp(source, 'u');
  } catch {
    try {
      new RegExp(source);
    } catch (error) {
      console.warn(`warning: pattern is not a valid JavaScript RegExp (Oniguruma may still accept it): ${source}\n         ${error.message}`);
    }
  }
}

// ---------------------------------------------------------------------------
// Corpus
// ---------------------------------------------------------------------------

function collectQui(root, out) {
  if (!existsSync(root)) return;
  const st = statSync(root);
  if (st.isFile()) {
    if (extname(root) === '.qui') out.push(root);
    return;
  }
  for (const entry of readdirSync(root, { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name))) {
    const full = join(root, entry.name);
    if (entry.isDirectory()) {
      if (entry.name === 'node_modules' || entry.name.startsWith('.')) continue;
      collectQui(full, out);
    } else if (entry.isFile() && extname(entry.name) === '.qui') {
      out.push(full);
    }
  }
}

const files = [];
collectQui(siteExamplesDir, files);
collectQui(coreExamplesDir, files);
for (const extra of extraPaths) collectQui(extra, files);
const uniqueFiles = [...new Set(files)];

if (dumpFile) {
  const target = resolve(dumpFile);
  if (!existsSync(target)) fail(`--dump target does not exist: ${target}`);
  if (!uniqueFiles.includes(target)) uniqueFiles.push(target);
}

if (uniqueFiles.length === 0) {
  fail(`no .qui files found under ${siteExamplesDir} or ${coreExamplesDir}`);
}

// ---------------------------------------------------------------------------
// Tokenization
// ---------------------------------------------------------------------------

const highlighter = await createHighlighter({
  langs: [grammar],
  themes: [THEME],
  ...(useJsEngine ? { engine: createJavaScriptRegexEngine({ forgiving: false }) } : {}),
});

/** @returns {{content:string, scopes:string[]}[][]} one array of TextMate tokens per line */
function tokenizeFile(code) {
  const lines = highlighter.codeToTokensBase(code, {
    lang: LANG,
    theme: THEME,
    includeExplanation: 'scopeName',
  });
  return lines.map((themedTokens) => {
    const out = [];
    for (const token of themedTokens) {
      if (!token.explanation || token.explanation.length === 0) {
        out.push({ content: token.content, scopes: [BASE_SCOPE] });
        continue;
      }
      for (const part of token.explanation) {
        out.push({ content: part.content, scopes: part.scopes.map((s) => s.scopeName) });
      }
    }
    return out;
  });
}

for (const source of [
  'int count := 3',
  'name := "Quidra"',
  'for value := values[]',
  'int add(int a, int b := 1)',
  'tensor<real32>{nat H, W := H * 2} image := tensor.zeros([32, 64])',
]) {
  const tokens = tokenizeFile(source)[0] ?? [];
  const highlighted = tokens.filter((token) => token.content === ':=' &&
    token.scopes.includes('keyword.operator.assignment.quidra'));
  if (highlighted.length !== source.split(':=').length - 1) {
    fail(`binding initializer is not highlighted as one operator: ${source}`);
  }
}

const defaultParameter = tokenizeFile('string greet(label := "hello")')[0] ?? [];
if (!defaultParameter.some((token) => token.content === 'label' &&
    token.scopes.includes('variable.parameter.quidra'))) {
  fail('a parameter with a default loses parameter highlighting');
}

// Check develop collection types even when released examples do not use them.
// The name set remains available to user-defined functions.
for (const [source, expected] of [
  ['map<string, int> entries', 'map'],
  ['map <string, int> entries', 'map'],
  ['distinct<string> seen', 'distinct'],
  ['distinct <string> seen', 'distinct'],
]) {
  const tokens = tokenizeFile(source)[0] ?? [];
  if (!tokens.some((token) => token.content === expected &&
      token.scopes.includes('storage.type.primitive.quidra'))) {
    fail(`collection type is not highlighted: ${source}`);
  }
}

for (const [source, declaration, parameters = []] of [
  ['func<int()> callback := answer'],
  ['func<int(int)>[] callbacks := []'],
  ['map<string, func<int(int)>> callbacks := map.new()'],
  ['int apply(func<int(int, int)> callback, int value)', 'apply', ['callback', 'value']],
  ['int visit(map<string, func<func<int()>(int)>> callbacks, int value)', 'visit', ['callbacks', 'value']],
  ['func<int(func<int()>)> make_consumer()', 'make_consumer'],
  ['func<map<string, func<int()>>(func<int(int)>[])> make_table()', 'make_table'],
  ['extern func<map<string, func<int()>>(int)> make_foreign_callback()', 'make_foreign_callback'],
  ['int spaced(func <int(int)> callback, int value)', 'spaced', ['callback', 'value']],
  ['func <int()> make_callback()', 'make_callback'],
  ['func<int>(int) legacy(func<int>(int) callback)', 'legacy', ['callback']],
]) {
  const tokens = tokenizeFile(source)[0] ?? [];
  const hasScope = (content, scope) => tokens.some((token) => token.content === content &&
    token.scopes.includes(scope));
  const angles = tokens.filter((token) => token.scopes.includes(
    `punctuation.section.angle.${token.content === '<' ? 'begin' : 'end'}.quidra`));
  if (!hasScope('func', 'storage.type.primitive.quidra') ||
      angles.map((token) => token.content).join('') !== source.replace(/[^<>]/g, '') ||
      (declaration && !hasScope(declaration, 'entity.name.function.quidra')) ||
      parameters.some((name) => !hasScope(name, 'variable.parameter.quidra'))) {
    fail(`function type is not highlighted in its declaration: ${source}`);
  }
}

// Namespace highlighting follows Core's reserved namespaces. Package names
// and former namespaces remain ordinary identifiers outside an import context.
const manifestPath = join(coreDir, 'quidra.manifest.json');
const standardModules = existsSync(manifestPath)
  ? JSON.parse(readFileSync(manifestPath, 'utf8')).standard_modules
  : ['cli', 'file', 'environment', 'test', 'time', 'gpu', 'autograd', 'reflect',
    'random', 'process', 'map', 'distinct', 'json', 'http', 'tensor'];
for (const name of standardModules) {
  for (const separator of ['.', ' . ']) {
    const source = `${name}${separator}member()`;
    const tokens = tokenizeFile(source)[0] ?? [];
    if (!tokens.some((token) => token.content === name &&
        token.scopes.includes('support.namespace.quidra'))) {
      fail(`Core standard namespace is not highlighted: ${source}`);
    }
  }
}
for (const name of ['math', 'stats', 'linear', 'signal', 'image', 'video', 'neural']) {
  const tokens = tokenizeFile(`${name}.member()`)[0] ?? [];
  if (tokens.some((token) => token.content === name &&
      token.scopes.includes('support.namespace.quidra'))) {
    fail(`ordinary identifier is highlighted as a Core standard namespace: ${name}`);
  }
}

for (const format of [
  '3', '3.', '03.', '.0', '.2', '.02', '03.2', ':3', '03.2:3', '3:3',
  '1000', '01000.', '.01000', ':003', '03 . 02 : 003',
  'base=2', 'base=16,upper', 'upper,base=16', 'base = 036',
]) {
  const source = `println("{value:${format}}")`;
  const tokens = tokenizeFile(source)[0] ?? [];
  if (!tokens.some((token) => token.content === format &&
      token.scopes.includes('constant.other.format-spec.quidra'))) {
    fail(`numeric format specification is not highlighted: ${source}`);
  }
}

for (const format of [
  '03', '0', '0.', '.', '03:3', '3:3:3', 'int=3:3',
  '1001', '01001.2', '.1001', ':1001', '3:1001', ':000', 'base=1', 'base=37',
  'int=3', 'frac=2', 'sig=3', 'group=3', 'zero',
  'group=3,frac=2', 'group=3,int=12,zero',
]) {
  const source = `println("{value:${format}}")`;
  const tokens = tokenizeFile(source)[0] ?? [];
  if (tokens.some((token) => token.scopes.includes('constant.other.format-spec.quidra'))) {
    fail(`invalid or abolished numeric format specification is highlighted as valid: ${source}`);
  }
}

for (const [source, format] of [
  ['println("{values[1:3][0]:3}")', '3'],
  ['println("{values[indices[1:3][0]:<limit][0]:03.2:3}")', '03.2:3'],
  ['println("{values[1:3]}")', null],
  ['println("{values[indices[1:3][0]:<limit]}")', null],
]) {
  const tokens = tokenizeFile(source)[0] ?? [];
  const formats = tokens.filter((token) =>
    token.scopes.includes('constant.other.format-spec.quidra'));
  if (format === null ? formats.length !== 0 :
    formats.length !== 1 || formats[0].content !== format) {
    fail(`slice colons and numeric format specifications are confused: ${source}`);
  }
}

for (const [source, content, scope] of [
  ['value := inf', 'inf', 'constant.numeric.quidra'],
  ['value := -inf', 'inf', 'constant.numeric.quidra'],
  ['squared := value ^ 2', '^', 'keyword.operator.arithmetic.quidra'],
  ['count := #values', '#', 'keyword.operator.arithmetic.quidra'],
  ['println("{#values}")', '#', 'keyword.operator.arithmetic.quidra'],
  ['ordered := left < right', '<', 'keyword.operator.comparison.quidra'],
  ['shifted := left >> right', '>>', 'keyword.operator.bitwise.quidra'],
]) {
  const tokens = tokenizeFile(source)[0] ?? [];
  if (!tokens.some((token) => token.content === content && token.scopes.includes(scope))) {
    fail(`numeric literal or operator is not highlighted: ${source}`);
  }
}

function effectiveScopes(scopes) {
  return scopes.filter((s) => s !== BASE_SCOPE && !s.startsWith('meta.'));
}

function innermostScope(scopes) {
  const eff = effectiveScopes(scopes);
  return eff.length > 0 ? eff[eff.length - 1] : `(${BASE_SCOPE} only)`;
}

// ---------------------------------------------------------------------------
// Report
// ---------------------------------------------------------------------------

const scopeCounts = new Map();
const allScopes = new Set();
const unscopedNonIdentifiers = []; // { file, line, content }
const unscopedReserved = []; // { file, line, content }
let totalTokens = 0;
let plainIdentifierCount = 0;

function displayPath(file) {
  const relWebsite = relative(websiteRoot, file);
  if (!relWebsite.startsWith('..')) return relWebsite;
  const relCore = relative(coreDir, file);
  if (!relCore.startsWith('..')) return `quidra/${relCore}`;
  return file;
}

for (const file of uniqueFiles) {
  const code = readFileSync(file, 'utf8');
  const lines = tokenizeFile(code);
  lines.forEach((tokens, lineIndex) => {
    for (const token of tokens) {
      if (token.content.trim() === '') continue;
      totalTokens += 1;
      for (const s of token.scopes) allScopes.add(s);
      const inner = innermostScope(token.scopes);
      scopeCounts.set(inner, (scopeCounts.get(inner) ?? 0) + 1);

      if (effectiveScopes(token.scopes).length > 0) continue;
      const content = token.content.trim();
      if (IDENTIFIER.test(content)) {
        if (RESERVED_WORDS.has(content)) {
          unscopedReserved.push({ file, line: lineIndex + 1, content });
        } else {
          plainIdentifierCount += 1;
        }
      } else {
        unscopedNonIdentifiers.push({ file, line: lineIndex + 1, content });
      }
    }
  });
}

if (dumpFile) {
  const target = resolve(dumpFile);
  const code = readFileSync(target, 'utf8');
  const sourceLines = code.split(/\r?\n/);
  const lines = tokenizeFile(code);
  console.log(`# dump of ${displayPath(target)}`);
  lines.forEach((tokens, i) => {
    console.log(`${String(i + 1).padStart(4)} | ${sourceLines[i] ?? ''}`);
    for (const token of tokens) {
      if (token.content.trim() === '') continue;
      const scopes = token.scopes.filter((s) => s !== BASE_SCOPE);
      console.log(`       ${JSON.stringify(token.content).padEnd(28)} ${scopes.length > 0 ? scopes.join(' ') : '(unscoped)'}`);
    }
  });
  console.log('');
}

console.log(`Grammar: ${relative(websiteRoot, grammarPath)} (${useJsEngine ? 'JavaScript regex engine' : 'Oniguruma engine'})`);
console.log(`Files tokenized: ${uniqueFiles.length}`);
for (const f of uniqueFiles) console.log(`  ${displayPath(f)}`);
console.log(`Total non-whitespace tokens: ${totalTokens}`);
console.log(`Plain identifiers left with the base scope only: ${plainIdentifierCount}`);
console.log('');
console.log('Tokens per innermost scope:');
const sortedCounts = [...scopeCounts.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
const width = Math.max(...sortedCounts.map(([s]) => s.length));
for (const [scope, count] of sortedCounts) console.log(`  ${scope.padEnd(width)}  ${String(count).padStart(6)}`);
console.log('');
console.log(`Distinct scopes emitted (${allScopes.size}):`);
for (const s of [...allScopes].sort()) console.log(`  ${s}`);
console.log('');

let failed = false;
if (unscopedNonIdentifiers.length > 0) {
  failed = true;
  console.log(`Unscoped non-identifier tokens (${unscopedNonIdentifiers.length}):`);
  for (const t of unscopedNonIdentifiers) console.log(`  ${displayPath(t.file)}:${t.line}  ${JSON.stringify(t.content)}`);
  console.log('');
} else {
  console.log('Unscoped non-identifier tokens: none');
}
if (unscopedReserved.length > 0) {
  failed = true;
  console.log(`Unscoped reserved words (${unscopedReserved.length}):`);
  for (const t of unscopedReserved) console.log(`  ${displayPath(t.file)}:${t.line}  ${JSON.stringify(t.content)}`);
  console.log('');
} else {
  console.log('Unscoped reserved words: none');
}

if (failed) {
  console.log('\nRESULT: FAIL');
  process.exit(1);
}
console.log('\nRESULT: OK');
