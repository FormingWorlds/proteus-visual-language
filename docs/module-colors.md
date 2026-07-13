# Module colours

Each PROTEUS physical domain has a stable colour, used everywhere a module is
named or its data is plotted: the website module grid, docs badges, the coupler
diagram, and paper figures. Consistency across all of these is the point — a
reader learns the colour once.

| Domain | Token | Hex | Modules |
|---|---|---|---|
| Interior | `--pt-dom-interior` | `#E23D28` | SPIDER, Aragog, Zalmoxis |
| Outgassing | `--pt-dom-outgassing` | `#A03123` | CALLIOPE, Atmodeller |
| Tidal | `--pt-dom-tidal` | `#593E74` | LovePy, Obliqua |
| Chemistry & escape | `--pt-dom-chem` | `#1B6FA8` | VULCAN, ZEPHYRUS |
| Atmosphere | `--pt-dom-atmos` | `#4FA3D9` | AGNI, JANUS |
| Stellar | `--pt-dom-stellar` | `#E0A32E` | MORS |

Stellar is solar gold, the star's own colour. On light surfaces the token
deepens to `#C8860F` so the gold keeps adequate contrast (bright gold reads at
2.22:1 on white); in matplotlib use `COLORS["solar_deep"]` for stellar fills
or thin marks on light figures.

## Colour-blind safety

The six colours were checked as a **set** under protanopia, deuteranopia, and
tritanopia (Machado 2009, full severity). Every pair keeps a perceptual
separation of ΔE ≥ 16.4 under all three — which is why Tidal is a desaturated
violet `#593E74` rather than a green or a mid-purple that would collide with
the reds or blues, and why gold works for Stellar: it sits far from both the
reds and the blues in every dichromacy projection.

**Do not remap or extend** these without re-running the CVD ΔE check. If a new
domain is added, pick its colour by maximising the minimum pairwise ΔE across
all dichromacy types against the existing six.

## In practice

- Reserve these exact colours for module identity and domain-coded data. Don't
  reuse them decoratively.
- In figures, pair each module's line/marker with its domain colour and keep it
  identical across every paper (see [figure-conventions.md](figure-conventions.md)).
- Module badges: the glyph tinted to the domain colour + the name in Sora +
  domain label in tracked mono. Ready-made in [`../community/`](../community/).
