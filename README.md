# quidra-lang.com

The official website of the [Quidra programming language](https://github.com/quidra-lang/quidra),
served at **https://quidra-lang.com**.

It is a fully static site: no backend, no database, no secrets. Every Quidra
program shown on it is a real file under `examples/` that CI checks, formats
and runs against the matching Core branch, so `develop` can evolve with Core
`develop` without being constrained by the latest release.

## Stack

| | |
| --- | --- |
| Framework | [Astro](https://astro.build) 7, TypeScript, static output |
| Styling | one hand-written stylesheet (`src/styles/global.css`); light and dark via `light-dark()` |
| Fonts | Inter (variable) and IBM Plex Mono, self-hosted from `src/assets/fonts/` through Astro's Fonts API |
| Syntax highlighting | Shiki at build time with the project's own Quidra TextMate grammar (`src/lib/quidra.tmLanguage.json`) |
| Client JavaScript | three small progressive enhancements only: theme toggle, example tabs, copy buttons |
| Hosting | Cloudflare Workers static assets (`wrangler.jsonc`); also deployable as-is to Cloudflare Pages |

## Local development

Requires Node 24 (see `.node-version`) and, for the example checks, a Quidra
compiler from the matching Core branch on `PATH`: Website `develop` is
verified with Core `develop`, while Website `main` is verified with Core
`main`.

```bash
npm ci
npm run dev        # http://localhost:4321
```

## Build and verification

```bash
npm run build                          # static site into dist/
npm run check                          # astro check (types, templates)
npm run lint                           # eslint (TypeScript, Astro, a11y rules)
npm run preview                        # serve dist/ locally

bash scripts/check-examples.sh         # every example: quidra check, fmt --check, run == recorded output
node scripts/check-grammar.mjs         # every example token is scoped by the Quidra grammar
node scripts/check-contrast.mjs        # WCAG contrast of the palette and both syntax themes
node scripts/check-links.mjs dist      # internal links and fragments in the built site
node scripts/check-links.mjs dist --external   # additionally probes every external URL
```

`npm run verify` runs the build-independent checks; `.github/workflows/ci.yml`
runs all of them on every push using a compiler built from the matching Core
branch. Pull requests use the target branch, so a PR into `develop` verifies
against Core `develop` and a PR into `main` verifies against Core `main`.
First-party packages used by the examples, currently Math, are checked out from
that same branch as well. On `develop`, `examples/manifest.json` records the
matching development compiler version even when it is newer than the public
release in `src/config/site.ts`; on `main`, those versions must agree.

## Deployment

The production build is `dist/`. Two equivalent ways to publish it on Cloudflare:

**Workers (recommended by Cloudflare for new projects).** `wrangler.jsonc`
declares a static-assets-only Worker named `quidra-website`. Locally:

```bash
npm run build && npx wrangler deploy
```

With Workers Builds (Git integration) use build command `npm run build` and
deploy command `npx wrangler deploy`. Attach the custom domain
`quidra-lang.com` to the Worker in the dashboard (Settings › Domains & Routes).

**Pages.** Connect the repository, framework preset *Astro*, build command
`npm run build`, output directory `dist`, then add `quidra-lang.com` as a custom
domain.

`public/_headers` sets security headers and immutable caching for fingerprinted
assets; `npm run build` appends a Content-Security-Policy whose script hashes
match the inline scripts of that build (`scripts/write-headers.mjs`). Both
platforms read the resulting `dist/_headers`. No account id, token or environment variable is
required anywhere in this repository, and `.env` files are git-ignored.

## Domain

Canonical origin: `https://quidra-lang.com` (set in `astro.config.mjs` and
`src/config/site.ts`). The structure anticipates `docs.quidra-lang.com` and
`playground.quidra-lang.com`: every external destination is defined once in
`src/config/site.ts`, and `/docs/` is an index page that can become a redirect.

## Branches

Work lands on `develop`; `main` is fast-forwarded to publish, mirroring the
other Quidra repositories. No `feature/*` branches.

## Directory structure

```
.
├── .github/workflows/ci.yml  build, verification and example checks on every push
├── .node-version           Node release used locally and in CI
├── astro.config.mjs        site URL, sitemap, self-hosted fonts
├── eslint.config.js        lint rules (TypeScript, Astro, jsx-a11y)
├── tsconfig.json           strict TypeScript for .astro and .ts files
├── package.json            scripts (dev, build, check, lint, verify, deploy)
├── wrangler.jsonc          Cloudflare Workers static-assets config (no secrets)
├── LICENSE                 MIT
├── examples/               Quidra programs shown on the site + recorded outputs
│   ├── manifest.json       titles, summaries, arguments, compiler version
│   └── invalid/            intentionally rejected programs + exact diagnostics
├── public/                 static files copied verbatim: favicons, web manifest,
│                           Open Graph and brand PNGs, robots.txt, _headers
├── scripts/
│   ├── check-examples.sh       every example against the compiler
│   ├── check-grammar.mjs       grammar coverage of every example token
│   ├── check-contrast.mjs      WCAG contrast of palette and syntax themes
│   ├── check-links.mjs         internal (and optionally external) links in dist/
│   ├── write-headers.mjs       post-build: dist/_headers with a hash-based CSP
│   ├── build-brand-assets.py   regenerates public/ images from the official logo PNGs
│   ├── sync-benchmarks.py      regenerates src/data/benchmarks.json from the core repo
│   └── sync-fonts.sh           copies the pinned font files from node_modules
└── src/
    ├── assets/fonts/       woff2 files and their licenses
    ├── components/         Astro components (CodeBlock, ExampleTabs, Header, …)
    ├── config/site.ts      site constants and every external URL
    ├── data/benchmarks.json published benchmark result (generated)
    ├── layouts/Base.astro  document shell, metadata, Open Graph, JSON-LD
    ├── lib/                Quidra grammar, Shiki themes, highlighter, example loader
    ├── pages/              /, /get-started/, /docs/, /benchmarks/, 404
    └── styles/global.css   design tokens and all shared styles
```

## Updating for a new Quidra release

The website is the final step of an unqualified coordinated Quidra release.
Core's `docs/development.md` is the canonical cross-repository release procedure.
The coordinated release is not complete until the production website has been
updated and verified.

1. Set `quidraVersion` and `releaseDate` in `src/config/site.ts` to the
   released Core version and date.
2. Re-run `bash scripts/check-examples.sh` with the released compiler and update
   any recorded output or diagnostic that legitimately changed, plus `compiler`
   in `examples/manifest.json`.
3. Update release/download links and Math/NN/Vision/Video/DNN references to
   the same shared version as Core. First-party computational package versions
   are lockstep; the website must not present independent package versions.
4. Do not run or regenerate benchmarks as part of a release. If a formal
   benchmark run was completed separately and is explicitly intended for
   publication, synchronize that existing result with
   `python3 scripts/sync-benchmarks.py ../quidra`.
5. Run `npm ci`, `npm run verify`, `npm run build`, and
   `node scripts/check-links.mjs dist --external`. Require the Website
   `develop` CI to pass.
6. Fast-forward `main` to the verified `develop` state, deploy with the
   configured Cloudflare Workers build or `npm run deploy`, and verify the live
   `https://quidra-lang.com` version, release/download links, docs links, and
   Playground link. Only then is the coordinated Quidra release complete.

## License

MIT, matching Quidra Core. The Quidra logo assets in `public/brand/` are the
official assets from the core repository.
