# PROTEUS Figure Conventions (Thermocline v1.0)

The rules that make every PROTEUS figure recognizably PROTEUS — across
papers, talks, posters, docs, and the website.

## 1. Module domain colors — the core convention

When a plotted series *is* a module's output, it uses that module's domain
color. Identical in every artifact, no exceptions:

| Domain | Modules | Hex |
|---|---|---|
| Interior | SPIDER · Aragog · Zalmoxis | `#E23D28` |
| Outgassing | CALLIOPE · Atmodeller | `#A03123` |
| Tidal | LovePy · Obliqua | `#593E74` |
| Chemistry & escape | VULCAN · ZEPHYRUS | `#1B6FA8` |
| Atmosphere | AGNI · JANUS | `#4FA3D9` |
| Stellar | MORS | `#A8D4E8` |

CVD-checked (Machado 2009, protan/deutan/tritan @ full severity): min
pairwise ΔE = 16.4 (target ≥ 12). Still: always keep a legend or direct
labels; never encode meaning in color alone.

## 2. Colormaps

- `proteus` (sequential, Void→Paper): 2D fields, colorbars. Default.
- `proteus_div` (diverging, light midpoint): anomalies/residuals in papers.
- `proteus_phase` (magma→void→ocean, dark midpoint): the brand ramp — hero
  figures, dark slides, outreach. Hot is ALWAYS left/low, cool right/high.
- Never rainbow/jet; never Interra's warm strata ramps.

## 3. Temperature/phase semantics

Red = hot/molten, blue = cool/solidified/volatile — matching the physics and
the logo. Do not use red/blue for arbitrary category pairs where a reader
could mistake them for hot/cold.

## 4. Typography in figures

- Labels/ticks: Instrument Sans (via proteus-mpl defaults).
- Axis units and run identifiers: Spline Sans Mono
  (`fontfamily="Spline Sans Mono"`), tracked uppercase for eyebrow-style
  annotations.
- Titles: bold, left-aligned (never centered).

## 5. Sizing

- Author at final printed size: A&A single column ≈ 3.5 in wide (use
  `figsize=(5, 3.75)` and let reduction land at ~3.5), full width ≈ 7.1 in.
- Slides: half text-width at 1920×1080 keeps labels readable from the back.
- Keep default proteus-mpl font sizes; if labels look too big, the figure
  is too large.

## 6. Surfaces

- `use()` (Paper) for papers and light slides; `use("dark")` (Void) for
  darkframes and hero surfaces. The figure background must match the slide —
  no visible card edge.
- Journal white pages: `fig.savefig(..., transparent=True)`.

## 7. The one-hot rule

Magma `#E23D28` is the highest-energy mark on any figure. If everything is
red, nothing is. One hot series, one hot annotation, or one hot region per
figure — the rest of the palette starts from Ocean.
