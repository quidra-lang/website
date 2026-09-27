/**
 * Loads the verified example programs from /examples at build time. Every
 * file there passes `quidra check`, `quidra fmt --check` and, when runnable,
 * `quidra run` with the recorded output (see scripts/check-examples.sh).
 */
import manifest from '../../examples/manifest.json';

const sources = import.meta.glob('../../examples/**/*.qui', { query: '?raw', import: 'default', eager: true }) as Record<string, string>;
const outputs = import.meta.glob('../../examples/**/*.{out,diag,json}', { query: '?raw', import: 'default', eager: true }) as Record<string, string>;

function read(table: Record<string, string>, relative: string): string {
  const key = Object.keys(table).find((k) => k.endsWith(`/examples/${relative}`));
  if (!key) throw new Error(`Missing example file: examples/${relative}`);
  return table[key];
}

export interface Example {
  id: string;
  title: string;
  summary: string;
  file: string;
  code: string;
  run: boolean;
  args: string[];
  output?: string;
}

export interface InvalidExample {
  id: string;
  title: string;
  file: string;
  code: string;
  /** Exact output of `quidra check FILE`. */
  diagnostic: string;
  /** Exact output of `quidra check FILE --json`, when recorded. */
  diagnosticJson?: string;
  diagnosticCode: string;
}

export const compilerVersion: string = manifest.compiler;

export const examples: Example[] = manifest.examples.map((entry) => ({
  id: entry.id,
  title: entry.title,
  summary: entry.summary,
  file: entry.file,
  code: read(sources, entry.file),
  run: entry.run,
  args: 'args' in entry && Array.isArray(entry.args) ? (entry.args as string[]) : [],
  output: entry.run && entry.output ? read(outputs, entry.output) : undefined,
}));

export const invalidExamples: InvalidExample[] = manifest.invalid.map((entry) => ({
  id: entry.id,
  title: entry.title,
  file: entry.file,
  code: read(sources, `invalid/${entry.file}`),
  diagnostic: read(outputs, `invalid/${entry.diagnostic}`),
  diagnosticJson: Object.keys(outputs).some((k) => k.endsWith(`/examples/invalid/${entry.id}.json`))
    ? read(outputs, `invalid/${entry.id}.json`)
    : undefined,
  diagnosticCode: entry.code,
}));

export function example(id: string): Example {
  const found = examples.find((e) => e.id === id);
  if (!found) throw new Error(`Unknown example id: ${id}`);
  return found;
}

export function invalidExample(id: string): InvalidExample {
  const found = invalidExamples.find((e) => e.id === id);
  if (!found) throw new Error(`Unknown invalid example id: ${id}`);
  return found;
}
