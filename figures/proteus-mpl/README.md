# proteus-mpl

PROTEUS Thermocline matplotlib theme. Publication-grade figures whose colors,
fonts, and surfaces match the slides, the website, and the docs.

## Install

```bash
pip install proteus-mpl
```

From a checkout of the repository: `pip install figures/proteus-mpl` (or cd
into the folder and `pip install .`).

## Use

```python
import proteus_mpl
proteus_mpl.use()          # light: Paper background — papers, light slides
# proteus_mpl.use("dark")  # dark: Void background — dark slides, hero figures
```

## What you get

- **Cycles** — light: five of the six module-domain colours (stellar's pale
  tint is omitted on Paper) + ink + fog (`proteus_mpl.CYCLE`); dark: a
  substitution cycle with light-safe tones (`CYCLE_DARK`). The domain set and
  the light cycle are CVD-checked (Machado 2009, min pairwise ΔE 16.4). Keep
  legends on multi-series plots.
- **Module domain colors** — `proteus_mpl.DOMAINS["interior"]` etc. Use these
  whenever a line *is* a module (SPIDER output → interior red). Stable across
  every paper, talk, and diagram.
- **Colormaps** — `proteus` (sequential, Void→Paper; default for imshow /
  pcolormesh), `proteus_div` (diverging, light midpoint — print-safe for
  anomalies/residuals), `proteus_phase` (the brand ramp, magma→void→ocean,
  dark midpoint — hero figures and dark slides). `_r` reversals registered.
- **Type** — Instrument Sans labels, Spline Sans Mono available for ticks via
  `fontfamily="Spline Sans Mono"`; titles bold, left-aligned. To bundle the
  fonts, copy the TTFs from the repository's [`fonts/`](https://github.com/FormingWorlds/proteus-visual-language/tree/main/fonts) folder
  into `src/proteus_mpl/fonts/`; missing fonts fall back gracefully.
- **Publication settings** — 300 dpi savefig, tight bbox, TrueType embedding
  (fonttype 42), text-as-paths SVG. Prefer `fig.savefig("fig.pdf")`.

## Conventions

- Size figures at final printed size (A&A column ≈ 3.5 in) and keep default
  font sizes — never shrink a huge figure down.
- Light figures on light surfaces, dark figures on dark — no visible card.
- `transparent=True` when a journal page must show through.
- Magma is the *hot signal*: reserve it for the series you want the room to
  look at. Everything else starts from Ocean.
