# Logo

The PROTEUS mark: an all-caps **Sora ExtraBold** wordmark with the phase glyph
standing in for the **O**. The glyph is a molten core cooling outward through
concentric rings — the magma→ocean story in miniature.

**The geometry is invariant.** Recolour the glyph; never redraw it.

## Files

```
logo/
├── glyph/     the phase glyph, every colorway × four formats:
│   ── SVG (vector):  glyph_phase.svg (multi-colour master),
│                  glyph_phase_dark.svg (master palette, dark surfaces),
│                  glyph_phase_light.svg (tuned for light), glyph_magma/ocean/
│                  ice/ink/paper/azure/outgassing/tidal/solar.svg (single),
│                  glyph_mono.svg (currentColor, SVG-only by design)
│   ── PDF (vector, tight-cropped to the glyph): glyph_phase.pdf,
│                  glyph_phase_dark/light.pdf, plus every single colorway
│                  (glyph_magma/ocean/ice/ink/paper/azure/outgassing/tidal/
│                  solar.pdf)
│   ── PNG (pixel, transparent, 950×998): glyph_phase_dark/light.png plus
│                  every single colorway (glyph_magma/ocean/ice/ink/paper/
│                  azure/outgassing/tidal/solar.png)
│   ── JPG (pixel, on background): glyph_phase_dark.jpg (on Void),
│                  glyph_phase_light.jpg (on Paper), plus every single
│                  colorway composited on its natural surface
├── lockup/    PROTEUS wordmark (Sora ExtraBold + phase glyph):
│            proteus-lockup-dark.png / .jpg (on Void) and
│            proteus-lockup-light.png / .jpg (on Paper); these panels carry the
│            clearspace baked in, and the JPGs are the default ready-to-ship
│            form for no-transparency contexts (a Discord avatar, an image
│            embed), rendering cleanly anywhere;
│            *-transparent.{png,pdf} (paper or ink letters, no background; the
│            PDF is fully vector, wordmark text and phase glyph both as paths);
│            *-on-black.jpg / *-on-white.jpg (plain compositions on pure
│            black/white surfaces, the one sanctioned exception to the
│            no-pure-black-or-white rule; use only when a pure surface is
│            specifically required)
└── favicon/   favicon.svg + favicon.pdf (phase glyph, vector) + favicon.png /
             favicon-light.png (pixel)
```

**Formats:** SVG for anything that scales (web, docs, print) — `glyph_mono.svg`
inherits `currentColor` for inline embedding; PDF for vector placement in print
and LaTeX workflows, tight-cropped to the glyph; PNG where transparency is needed
(slides, matplotlib, favicons); JPG where transparency isn't available, composited
on Void or Paper.

**Themes:** `phase_dark` / single-colour `paper` / `ice` / `magma` / `azure` /
`solar` sit on dark surfaces; `phase_light` / `ink` / `ocean` / `outgassing` / `tidal`
sit on light. The JPGs are composited accordingly (Void behind the dark-surface
colorways, Paper behind the light-surface ones). The multi-colour
`glyph_phase.svg` works on either.

## Rules

- **Clear space:** keep at least 1× cap height clear on all sides.
- **Minimum lockup width:** 90 px. Below that, use the glyph alone with the
  wordmark set beside it, not under it.
- **Colour:** the letters are Paper (on dark) or Ink (on light); the glyph
  carries the colour. Use one hot moment (magma) per surface at most.
- **Tag:** "framework" in Spline Sans Mono Medium, tracked +52%, at (26/150)
  of the wordmark size, tucked into the lower-right corner (raised 0.03x,
  inset 0.32x of the wordmark size; box measures, the final letter's ink
  lands about 0.41x in); drop it below 200 px lockup width.
- **Never:** rotate, mirror, add glow/shadow, outline, stretch, or place the glyph
  on a busy background without a scrim. The bright arc always sweeps in from the
  left; every asset shares that single handedness.

Full guidance: [`../docs/logo.md`](../docs/logo.md).
