#!/usr/bin/env bash
# Copies the self-hosted font files from the pinned @fontsource packages into
# src/assets/fonts. Run after bumping a font package; the copies are committed
# so builds never fetch fonts from the network.
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
dest="$root/src/assets/fonts"
mkdir -p "$dest"
cp "$root/node_modules/@fontsource-variable/inter/files/inter-latin-wght-normal.woff2" "$dest/"
for weight in 400 500 600; do
  cp "$root/node_modules/@fontsource/ibm-plex-mono/files/ibm-plex-mono-latin-${weight}-normal.woff2" "$dest/"
done
ls -la "$dest"
