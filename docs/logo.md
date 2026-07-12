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

Plus module domain tints (`azure`, `outgassing`, `tidal`, …) — see
[module-colors.md](module-colors.md).

## File matrix

Every colorway ships in three formats, in [`../logo/glyph/`](../logo/glyph/):

- **SVG** (vector) — `glyph_<name>.svg`. Scales to any size; preferred for web,
  docs, print. `glyph_mono.svg` uses `currentColor`.
- **PNG** (pixel, transparent) — `glyph_<name>.png` (950×998). For raster
  contexts needing transparency (slides, matplotlib, favicons).
- **JPG** (pixel, on background) — `glyph_<name>.jpg` on Void or Paper. For
  contexts that can't do transparency (some social/email).

Wordmark lockups live in [`../logo/lockup/`](../logo/lockup/) as
`proteus-lockup-dark.png` (on Void) and `proteus-lockup-light.png` (on Paper) —
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
- **Never:** rotate, add glow/shadow, outline, stretch, or place on a busy
  background without a scrim.
