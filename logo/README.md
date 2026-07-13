# Logo

The PROTEUS mark: an all-caps **Sora ExtraBold** wordmark with the phase glyph
standing in for the **O**. The glyph is a molten core cooling outward through
concentric rings — the magma→ocean story in miniature.

**The geometry is invariant.** Recolour the glyph; never redraw it.

## Files

```
logo/
├── glyph/     the phase glyph, every colorway × three formats:
│   ── SVG (vector):  glyph_phase.svg (multi-colour), glyph_magma/ocean/ice/
│                  ink/paper/azure/outgassing/tidal/solar.svg (single),
│                  glyph_mono.svg (currentColor, SVG-only by design)
│   ── PNG (pixel, transparent, 950×998): glyph_phase_dark/light.png plus
│                  every single colorway (glyph_magma/ocean/ice/ink/paper/
│                  azure/outgassing/tidal/solar.png)
│   ── JPG (pixel, on background): glyph_phase_dark.jpg (on Void),
│                  glyph_phase_light.jpg (on Paper), plus every single
│                  colorway composited on its natural surface
├── lockup/    PROTEUS wordmark (Sora ExtraBold + phase glyph):
│            proteus-lockup-dark.png (on Void) / proteus-lockup-light.png (on Paper);
│            *-transparent.{png,pdf} (paper or ink letters, no background; the
│            PDF carries the wordmark as vector text);
│            *-on-black.jpg / *-on-white.jpg (plain compositions for contexts
│            without transparency; these plain surfaces are the one sanctioned
│            exception to the no-pure-black-or-white rule)
└── favicon/   favicon.svg (phase glyph) + favicon.png / favicon-light.png
```

**Formats:** SVG for anything that scales (web, docs, print) — `glyph_mono.svg`
inherits `currentColor` for inline embedding; PNG where transparency is needed
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
- **Never:** rotate, add glow/shadow, outline, stretch, or place the glyph on a
  busy background without a scrim.

Full guidance: [`../docs/logo.md`](../docs/logo.md).
