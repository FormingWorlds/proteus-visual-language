# Figure conventions

The rules that make every PROTEUS figure recognizably PROTEUS — across
papers, talks, posters, docs, and the website.

## Module domain colours — the core convention

When a plotted series *is* a module's output, it uses that module's domain
colour. Identical in every artifact, no exceptions:

| Domain | Modules | Hex |
|---|---|---|
| Interior | SPIDER · Aragog · Zalmoxis | `#E23D28` |
| Outgassing | CALLIOPE · Atmodeller | `#A03123` |
| Tidal | LovePy · Obliqua | `#593E74` |
| Chemistry & escape | VULCAN · ZEPHYRUS | `#1B6FA8` |
| Atmosphere | AGNI · JANUS | `#4FA3D9` |
| Stellar | MORS | `#E0A32E` |

CVD-checked (Machado 2009, protan/deutan/tritan @ full severity): min
pairwise ΔE = 16.4 (target ≥ 12). Still: always keep a legend or direct
labels; never encode meaning in colour alone. Stellar is solar gold; for
gold fills, bars, or thin marks on light surfaces use the deepened
`--pt-solar-deep` `#C8860F` (bright gold is 2.22:1 on white, fine for lines
with a legend, marginal for small marks).

## Categorical cycles — for series that are not module outputs

Series without a module identity use the proteus-mpl cycle
(`proteus_mpl.CYCLE` / `CYCLE_DARK`). Both cycles are neutral-first: the
first line of a plot draws in ink (light) or paper (dark), so magma stays a
deliberate signal rather than the default.

- **Light (Paper or white), 9 colours:** ink, magma, solar, verdant, ocean,
  tidal, outgassing, fog, azure. Worst-pair CVD ΔE 15.7.
- **Dark (Void), 6 colours:** paper, magma, solar, brightened verdant, ice,
  lightened tidal. Worst-pair CVD ΔE 16.8.

## Many series — switch to line style past the cycle

Past the cycle, encode additional series with **line style** (solid, dashed,
dotted, dash-dot), not more hues: 9 colours × 4 styles = 36 distinguishable
series. Two hard rules, both CVD-driven:

- Never mix extra neutral greys into the colour cycle. A grey sitting next
  to a desaturated hue collapses the worst-pair ΔE to ~6.
- Do not add saturated hues beyond the cycle. The pink/rose region is
  already unusable (it collides with fog under deuteranopia), and every
  further hue shrinks the margin for colour-blind readers.

## Colormaps

- `proteus` (sequential, Void→Paper): 2D fields, colorbars. Default.
- `proteus_div` (diverging, light midpoint): anomalies/residuals in papers.
- `proteus_phase` (magma→void→ocean, dark midpoint): the brand ramp — hero
  figures, dark slides, outreach. Hot is ALWAYS left/low, cool right/high.
- Never rainbow/jet; never warm strata ramps.
- Greyscale safety: the phase and diverging ramps are not greyscale-safe
  (magma and ocean have nearly equal luminance). When a figure must survive
  greyscale reproduction, use the `proteus` sequential map, whose luminance
  rises monotonically from Void to Paper.

## Temperature/phase semantics

Red = hot/molten, blue = cool/solidified/volatile — matching the physics and
the logo. Do not use red/blue for arbitrary category pairs where a reader
could mistake them for hot/cold.

## Typography in figures

- Labels/ticks: Instrument Sans (via proteus-mpl defaults).
- Axis units and run identifiers: Spline Sans Mono
  (`fontfamily="Spline Sans Mono"`), tracked uppercase for eyebrow-style
  annotations.
- Titles: bold, left-aligned (never centered).

## Sizing

- Author at final printed size: A&A single column ≈ 3.5 in wide (use
  `figsize=(5, 3.75)` and let reduction land at ~3.5), full width ≈ 7.1 in.
- Slides: half text-width at 1920×1080 keeps labels readable from the back.
- Keep default proteus-mpl font sizes; if labels look too big, the figure
  is too large.

## Surfaces

- `use()` (Paper) for papers and light slides; `use("dark")` (Void) for
  darkframes and hero surfaces. The figure background must match the slide —
  no visible card edge.
- Journal white pages: `use("white")` for a pure-white background, or keep
  the Paper theme and save with `fig.savefig(..., transparent=True)`.

## The one-hot rule

Magma `#E23D28` is the highest-energy mark on any figure. If everything is
red, nothing is. One hot series, one hot annotation, or one hot region per
figure — the rest of the palette starts from Ocean.
