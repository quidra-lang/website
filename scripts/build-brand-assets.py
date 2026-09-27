#!/usr/bin/env python3
"""Build the website's brand image assets from the official Quidra logo PNGs.

Usage:
    python3 scripts/build-brand-assets.py /path/to/quidra-core-checkout

The core checkout is the `quidra-lang/quidra` repository. Only two files are
read from it, and neither is modified:

    <core>/assets/logo/quidra-symbol.png    950x950  RGBA three-loop knot
    <core>/assets/logo/quidra-wordmark.png  1010x218 RGBA navy letterforms

Everything is written relative to the website root (the parent of `scripts/`):

    public/brand/quidra-symbol-96.png       symbol, transparent, 4% padding (256-colour palette)
    public/brand/quidra-symbol-512.png      symbol, transparent, 4% padding (full RGBA)
    public/favicon.ico                      16 + 32 + 48 px symbol frames, transparent
    public/favicon-32.png                   the 32 px frame as a standalone PNG
    public/apple-touch-icon.png             180x180, opaque #0B0E14, 12% padding
    public/icon-192.png, icon-512.png       opaque #0B0E14, 14% padding (web manifest)
    public/icon-512-maskable.png            opaque #0B0E14, 20% padding (maskable manifest icon)
    public/og-image.png                     1200x630 Open Graph card

The outputs are committed to the repository: the site build does not run this
script. Re-run it only when the official logo PNGs change, then commit the
regenerated files. It is deterministic (no timestamps, no randomness), so
re-running it on unchanged inputs produces byte-identical files.

Requirements: Python 3, Pillow >= 10, and macOS system fonts for the Open
Graph text (Helvetica Neue Medium/Regular from HelveticaNeue.ttc, Menlo from
Menlo.ttc; Helvetica.ttc and Monaco.ttf are accepted as fallbacks). Text is
rendered at 2x and downsampled with Lanczos so it stays crisp.

The copy on the Open Graph cards comes from the core repository:
  - tagline "Maximum Meaning Per Token"      (README.md, line 3)
  - "A statically typed, native language for humans and language models."
    paraphrases README.md line 5
  - "quidra-lang.com" is the site URL in src/config/site.ts
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

LANCZOS = Image.Resampling.LANCZOS

# ---------------------------------------------------------------------------
# Palette (website dark theme) and copy
# ---------------------------------------------------------------------------
BG_DARK = (0x0B, 0x0E, 0x14)  # opaque icon and OG background
TEXT_LIGHT = (0xE6, 0xE9, 0xEF)  # light wordmark, tagline
TEXT_MUTED = (0xA8, 0xB0, 0xBD)  # OG subtitle
TEXT_DIM = (0x6F, 0x78, 0x86)  # OG domain line

TAGLINE = "Maximum Meaning Per Token"
SUBTITLE = "A statically typed, native language for humans and language models."
DOMAIN = "quidra-lang.com"

# Font roles -> ordered candidates of (file, family, style). The .ttc face
# index is discovered by name so a reshuffled collection cannot pick the wrong
# weight silently.
FONT_CANDIDATES = {
    "display": [
        ("/System/Library/Fonts/HelveticaNeue.ttc", "Helvetica Neue", "Medium"),
        ("/System/Library/Fonts/Helvetica.ttc", "Helvetica", "Bold"),
    ],
    "text": [
        ("/System/Library/Fonts/HelveticaNeue.ttc", "Helvetica Neue", "Regular"),
        ("/System/Library/Fonts/Helvetica.ttc", "Helvetica", "Regular"),
    ],
    "mono": [
        ("/System/Library/Fonts/Menlo.ttc", "Menlo", "Regular"),
        ("/System/Library/Fonts/Monaco.ttf", "Monaco", "Regular"),
        ("/System/Library/Fonts/HelveticaNeue.ttc", "Helvetica Neue", "Regular"),
    ],
}

# Open Graph render scale: draw at 2x, downsample once with Lanczos.
OG_SCALE = 2
OG_SIZE_BUDGET = 200 * 1024  # target; the hard ceiling below is 250 KB
OG_SIZE_CEILING = 250 * 1024

_font_report: dict[str, str] = {}


# ---------------------------------------------------------------------------
# Image helpers
# ---------------------------------------------------------------------------
def trim_alpha(im: Image.Image) -> Image.Image:
    """Crop an RGBA image to the bounding box of its non-transparent pixels."""
    bbox = im.getchannel("A").getbbox()
    if bbox is None:
        raise ValueError("image is fully transparent")
    return im.crop(bbox)


def scale_to_fit(im: Image.Image, box_w: float, box_h: float) -> Image.Image:
    """Lanczos-resize preserving aspect ratio so the image fits in box_w x box_h.

    Pillow resizes RGBA in premultiplied space internally, so anti-aliased
    edges do not pick up the (black) RGB of the transparent surround.
    """
    s = min(box_w / im.width, box_h / im.height)
    size = (max(1, round(im.width * s)), max(1, round(im.height * s)))
    return im.resize(size, LANCZOS)


def scale_to_height(im: Image.Image, height: int) -> Image.Image:
    return im.resize((max(1, round(im.width * height / im.height)), height), LANCZOS)


def fit_square(
    im: Image.Image, size: int, pad: float, bg: tuple[int, int, int] | None = None
) -> Image.Image:
    """Center `im` in a size x size canvas with `pad` (fraction of size) on each side.

    Returns RGBA with a transparent background when bg is None, otherwise an
    opaque RGB image filled with bg.
    """
    inner = size * (1 - 2 * pad)
    scaled = scale_to_fit(im, inner, inner)
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0) if bg is None else (*bg, 255))
    offset = ((size - scaled.width) // 2, (size - scaled.height) // 2)
    canvas.alpha_composite(scaled, offset)
    return canvas if bg is None else canvas.convert("RGB")


def recolor(im: Image.Image, rgb: tuple[int, int, int]) -> Image.Image:
    """Replace every pixel's RGB with a flat colour, keeping the alpha channel exactly."""
    out = Image.new("RGB", im.size, rgb)
    out.putalpha(im.getchannel("A"))
    return out


def png_bytes(im: Image.Image) -> bytes:
    buf = io.BytesIO()
    im.save(buf, "PNG", optimize=True)
    return buf.getvalue()


def save_png(im: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path, "PNG", optimize=True)


# ---------------------------------------------------------------------------
# Fonts
# ---------------------------------------------------------------------------
def _find_face(path: str, family: str, style: str, size: int) -> ImageFont.FreeTypeFont | None:
    if not Path(path).exists():
        return None
    for index in range(32):
        try:
            font = ImageFont.truetype(path, size, index=index)
        except OSError:
            return None  # ran past the last face in the collection
        if font.getname() == (family, style):
            return font
    return None


def load_font(role: str, size: int) -> ImageFont.FreeTypeFont:
    for path, family, style in FONT_CANDIDATES[role]:
        font = _find_face(path, family, style, size)
        if font is not None:
            _font_report.setdefault(role, f"{family} {style} ({path})")
            return font
    tried = ", ".join(f"{fam} {sty}" for _, fam, sty in FONT_CANDIDATES[role])
    raise SystemExit(f"error: no usable font for role '{role}' (tried: {tried})")


def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: float) -> list[str]:
    """Greedy word wrap; every returned line measures <= max_width."""
    lines: list[str] = []
    current = ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if current and font.getlength(candidate) > max_width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


# ---------------------------------------------------------------------------
# Open Graph cards
# ---------------------------------------------------------------------------
class OGCanvas:
    """A 2x RGB canvas with helpers that take 1x coordinates."""

    def __init__(self, width: int, height: int):
        self.s = OG_SCALE
        self.size = (width, height)
        self.im = Image.new("RGB", (width * self.s, height * self.s), BG_DARK)
        self.draw = ImageDraw.Draw(self.im)

    def paste(self, art: Image.Image, x: float, y: float) -> None:
        """Alpha-composite an RGBA image whose top-left lands at 1x (x, y)."""
        layer = Image.new("RGBA", self.im.size, (0, 0, 0, 0))
        layer.alpha_composite(art, (round(x * self.s), round(y * self.s)))
        self.im.paste(layer, (0, 0), layer)

    def text(self, x: float, baseline: float, text: str, role: str, size: int, fill, anchor="ls"):
        font = load_font(role, size * self.s)
        self.draw.text((x * self.s, baseline * self.s), text, font=font, fill=fill, anchor=anchor)

    def finish(self) -> Image.Image:
        return self.im.resize(self.size, LANCZOS)


def measure(role: str, size: int, text: str) -> float:
    return load_font(role, size).getlength(text)


def render_og_landscape(symbol: Image.Image, wordmark_light: Image.Image) -> Image.Image:
    W, H = 1200, 630
    S = OG_SCALE
    c = OGCanvas(W, H)

    # Symbol: ~300px tall, vertically centred, left edge at x=110.
    sym_h = 300
    sym = scale_to_height(symbol, sym_h * S)
    sym_x, sym_y = 110, (H - sym_h) / 2
    c.paste(sym, sym_x, sym_y)

    # Text column to the right of the symbol. The tagline is the widest line
    # and sets the column width; 50px is the largest size at which
    # "Maximum Meaning Per Token" fits with a right margin >= 50px.
    col_x = sym_x + sym.width / S + 40
    right_margin = 50
    col_w = W - right_margin - col_x
    tagline_size = 50
    assert measure("display", tagline_size, TAGLINE) <= col_w, "tagline would be clipped"

    wm_h = 88
    wm = scale_to_height(wordmark_light, wm_h * S)
    wm_y = 196
    c.paste(wm, col_x, wm_y)

    tagline_baseline = wm_y + wm_h + 66
    c.text(col_x, tagline_baseline, TAGLINE, "display", tagline_size, TEXT_LIGHT)

    sub_size, sub_leading = 28, 36
    sub_font = load_font("text", sub_size)
    lines = wrap_text(SUBTITLE, sub_font, col_w)
    baseline = tagline_baseline + 48
    for line in lines:
        c.text(col_x, baseline, line, "text", sub_size, TEXT_MUTED)
        baseline += sub_leading

    # Domain, bottom-right, monospace.
    c.text(W - right_margin, H - 46, DOMAIN, "mono", 24, TEXT_DIM, anchor="rs")
    return c.finish()


def save_og(im: Image.Image, path: Path) -> str:
    """Save an opaque OG card, falling back to a dithered 256-colour palette
    only if the full-colour PNG exceeds the 250 KB ceiling."""
    rgb = png_bytes(im)
    note = f"rgb={len(rgb)}B"
    data = rgb
    if len(rgb) > OG_SIZE_CEILING:
        # quantize() only dithers when given an explicit palette, so build the
        # adaptive palette first and then re-quantize against it with dithering.
        palette = im.quantize(256)
        pal = im.quantize(palette=palette, dither=Image.Dither.FLOYDSTEINBERG)
        q = png_bytes(pal)
        note += f" quantized={len(q)}B -> using quantized"
        data = q
    elif len(rgb) > OG_SIZE_BUDGET:
        note += " (over the 200 KB target, under the 250 KB ceiling)"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return note


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return 2
    core = Path(argv[1]).expanduser().resolve()
    symbol_src = core / "assets" / "logo" / "quidra-symbol.png"
    wordmark_src = core / "assets" / "logo" / "quidra-wordmark.png"
    for p in (symbol_src, wordmark_src):
        if not p.is_file():
            print(f"error: missing official logo file: {p}", file=sys.stderr)
            return 1

    site = Path(__file__).resolve().parent.parent
    public = site / "public"
    brand = public / "brand"
    notes: dict[str, str] = {}

    symbol = trim_alpha(Image.open(symbol_src).convert("RGBA"))
    wordmark = trim_alpha(Image.open(wordmark_src).convert("RGBA"))

    # -- brand symbols (transparent, 4% padding) ---------------------------
    for size in (96, 512):
        im = fit_square(symbol, size, 0.04)
        if size == 96:
            # 256-colour palette is visually identical at this size and ~3x
            # smaller; at 512 it mottles the silver gradients, so that one
            # keeps full RGBA.
            rgba_len = len(png_bytes(im))
            im = im.quantize(256, method=Image.Quantize.FASTOCTREE)
            notes[f"brand/quidra-symbol-{size}.png"] = f"quantized (rgba would be {rgba_len}B)"
        save_png(im, brand / f"quidra-symbol-{size}.png")

    # -- favicons -------------------------------------------------------------
    master = fit_square(symbol, 256, 0.0)
    frames = {n: master.resize((n, n), LANCZOS) for n in (16, 32, 48)}
    save_png(frames[32], public / "favicon-32.png")
    public.mkdir(parents=True, exist_ok=True)
    master.save(
        public / "favicon.ico",
        format="ICO",
        sizes=[(16, 16), (32, 32), (48, 48)],
        append_images=list(frames.values()),  # exact-size frames are used as-is
    )

    save_png(fit_square(symbol, 180, 0.12, BG_DARK), public / "apple-touch-icon.png")
    save_png(fit_square(symbol, 192, 0.14, BG_DARK), public / "icon-192.png")
    save_png(fit_square(symbol, 512, 0.14, BG_DARK), public / "icon-512.png")
    save_png(fit_square(symbol, 512, 0.20, BG_DARK), public / "icon-512-maskable.png")

    # -- Open Graph -----------------------------------------------------------
    wordmark_light_full = recolor(wordmark, TEXT_LIGHT)
    notes["og-image.png"] = save_og(render_og_landscape(symbol, wordmark_light_full), public / "og-image.png")

    # -- report ---------------------------------------------------------------
    print(f"core:  {core}")
    print(f"site:  {site}")
    for role, desc in sorted(_font_report.items()):
        print(f"font[{role}]: {desc}")
    outputs = [
        "brand/quidra-symbol-96.png", "brand/quidra-symbol-512.png",
        "favicon.ico", "favicon-32.png", "apple-touch-icon.png",
        "icon-192.png", "icon-512.png", "icon-512-maskable.png",
        "og-image.png",
    ]
    print(f"{'file':34} {'size':>9} {'bytes':>8}  mode")
    for rel in outputs:
        p = public / rel
        with Image.open(p) as im:
            dims = f"{im.width}x{im.height}"
            mode = im.mode
            if p.suffix == ".ico":
                dims = "+".join(f"{w}" for w, _ in sorted(im.info["sizes"]))
        extra = f"  [{notes[rel]}]" if rel in notes else ""
        print(f"public/{rel:27} {dims:>9} {p.stat().st_size:>8}  {mode}{extra}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
