/**
 * Site-wide constants. Every external URL the site links to lives here so a
 * future split into docs.quidra-lang.com / playground.quidra-lang.com is a
 * one-line change.
 *
 * `quidraVersion` is the latest released compiler version (the `vX.Y.Z` tag on
 * quidra-lang/quidra `main`). Update it when a new core release ships.
 */
export const site = {
  name: 'Quidra',
  tagline: 'Maximum Meaning Per Token',
  url: 'https://quidra-lang.com',
  description:
    'Quidra is a statically typed, natively compiled general-purpose programming language designed for both humans and language models. Maximum Meaning Per Token.',
  quidraVersion: '0.4.0',
  releaseDate: '2026-09-29',
} as const;

const org = 'https://github.com/quidra-lang';
const core = `${org}/quidra`;

export const links = {
  org,
  core,
  coreIssues: `${core}/issues`,
  releases: `${core}/releases`,
  latestRelease: `${core}/releases/tag/v${site.quidraVersion}`,
  license: `${core}/blob/main/LICENSE`,
  playground: 'https://quidra-lang.github.io/playground/',
  playgroundRepo: `${org}/playground`,
  vision: `${org}/vision`,
  dnn: `${org}/dnn`,
  website: `${org}/website`,
  docs: {
    readme: `${core}#readme`,
    language: `${core}/blob/main/docs/spec/language.md`,
    numericAndBin: `${core}/blob/main/docs/spec/numeric-and-bin.md`,
    grammar: `${core}/blob/main/docs/spec/grammar.ebnf`,
    llmGuide: `${core}/blob/main/docs/spec/llm-guide.md`,
    architecture: `${core}/blob/main/docs/spec/architecture.md`,
    diagnostics: `${core}/blob/main/docs/spec/diagnostics.md`,
    patchSchema: `${core}/blob/main/docs/spec/patch-schema.md`,
    packages: `${core}/blob/main/docs/packages.md`,
    development: `${core}/blob/main/docs/development.md`,
    examples: `${core}/tree/main/examples`,
    benchmark: `${core}/blob/main/benchmark/README.md`,
  },
} as const;

/** Release assets published for the current version (names from the release workflow). */
export const releaseAssets = [
  { platform: 'Linux (Debian/Ubuntu, x86_64)', file: 'quidra-linux-amd64.deb' },
  { platform: 'Linux (portable, x86_64)', file: 'quidra-linux-x86_64.tar.gz' },
  { platform: 'macOS (Apple silicon)', file: 'quidra-macos-arm64.tar.gz' },
  { platform: 'Windows (x86_64)', file: 'quidra-windows-x86_64.zip' },
] as const;

export function releaseAssetUrl(file: string): string {
  return `${core}/releases/download/v${site.quidraVersion}/${file}`;
}

/** Primary navigation. Internal paths are relative to this site. */
export const navigation = [
  { label: 'Get started', href: '/get-started/' },
  { label: 'Docs', href: '/docs/' },
  { label: 'Benchmarks', href: '/benchmarks/' },
  { label: 'Playground', href: links.playground, external: true },
  { label: 'GitHub', href: links.core, external: true },
] as const;
