# Logo

<img src="../logo/glyph/glyph_phase.svg" alt="PROTEUS phase glyph" width="120">

The PROTEUS mark is an all-caps **Sora ExtraBold** wordmark with the **phase
glyph** standing in for the **O**. The glyph is a molten core cooling outward
through three concentric broken rings — the magma→ocean story in miniature.

## The geometry is invariant

Recolour the glyph; **never redraw it**. The construction (solid core + three
broken concentric rings, asymmetric breaks) is fixed. All colorways are recolours
of one master vector.

## Colorways

| Name | Use | Core → rim |
|---|---|---|
| `phase` | default, full-colour | magma core → azure rim (the whole story) |
| `magma` | hot contexts, single-colour | all `#E23D28` |
| `ocean` | cool/interactive, single-colour | all `#1B6FA8` |
| `ice` | cool highlight on dark | all `#A8D4E8` |
| `ink` | mono on light surfaces | all `#10151B` |
| `paper` | mono on dark surfaces | all `#F2F5F7` |
| `mono` | inherits `currentColor` | any (for inline embedding) |

Plus module domain tints (`azure`, `outgassing`, `tidal`, `solar`, …) — see
[module-colors.md](module-colors.md). `solar` is the stellar domain gold
(`#E0A32E`), at home on dark surfaces.

## File matrix

Every colorway ships in three formats, in [`../logo/glyph/`](../logo/glyph/)
(`glyph_mono.svg` is the one deliberate exception: SVG-only, inheriting
`currentColor` for inline embedding):

- **SVG** (vector) — `glyph_<name>.svg`. Scales to any size; preferred for web,
  docs, print.
- **PNG** (pixel, transparent) — `glyph_<name>.png` (950×998); the phase
  colorway ships as `glyph_phase_dark.png` / `glyph_phase_light.png`. For
  raster contexts needing transparency (slides, matplotlib, favicons).
- **JPG** (pixel, on background) — `glyph_<name>.jpg` on Void or Paper, with
  the same `_dark` / `_light` naming for phase. For contexts that can't do
  transparency (some social/email).

Wordmark lockups live in [`../logo/lockup/`](../logo/lockup/) as
`proteus-lockup-dark.png` (on Void) and `proteus-lockup-light.png` (on Paper),
plus background-free `*-transparent.png` and `*-transparent.pdf` variants of
both (for READMEs, composited layouts, and print; the PDF wordmark is vector
text) and plain `*-on-black.jpg` / `*-on-white.jpg` compositions for contexts
without transparency (the one sanctioned exception to the
no-pure-black-or-white rule) —
the wordmark is **Sora ExtraBold**, so it also reproduces live in HTML (see
`../site/logo-lockups.html`) and the glyph itself is vector (`glyph_phase.svg`).
Favicon in [`../logo/favicon/`](../logo/favicon/): `favicon.svg` (phase glyph)
plus `favicon.png` / `favicon-light.png`.

## Rules

- **Clear space:** keep at least 1× cap height clear on all sides.
- **Minimum lockup width:** 90 px. Below that, glyph alone with the wordmark set
  *beside* it, not under.
- **Colour split:** letters are Paper (on dark) or Ink (on light); the glyph
  carries the colour.
- **Tag:** "framework" in Spline Sans Mono Medium, lowercase, tracked +52%,
  at (26/150) of the wordmark size, right-aligned and tucked into the
  lower-right corner: raised 0.03x and inset 0.32x of the wordmark size.
  These are CSS box measures; the tracking trails the final letter, so its
  ink lands about 0.41x in from the wordmark's right edge.
  Drop it below 200 px lockup width.
- **Never:** rotate, add glow/shadow, outline, stretch, or place on a busy
  background without a scrim.
