# @formingworlds/proteus-tokens

The single source of truth for the PROTEUS (Thermocline) visual system:
colours, type, spacing, radii, the phase ramp, and the module domain colours.

Three formats, one source. `tokens.json` and `tokens.scss` are generated from
`tokens.css` — edit the CSS, regenerate the other two.

## Install

```bash
npm install @formingworlds/proteus-tokens
```

## Use

**CSS custom properties**
```css
@import "@formingworlds/proteus-tokens/tokens.css";

.hot   { color: var(--pt-magma); }
.panel { background: var(--pt-void); border: var(--pt-border-d); }
```

**SCSS**
```scss
@use "@formingworlds/proteus-tokens/tokens.scss" as pt;
.hot { color: pt.$pt-magma; }
```

**JSON** (JS/TS, build tooling, Style Dictionary, etc.)
```js
import tokens from "@formingworlds/proteus-tokens";
tokens["pt-magma"]; // "#E23D28"
```

## Light / dark

`tokens.css` is dark-first. Opt into light by setting `data-theme="light"` on
the root element — the dark surface/text tokens remap to their light values, so
everything that references them flips at once. Regions meant to stay dark in
both themes (code blocks, hero bands) restore the dark tokens locally.

## Key groups

- Brand core: `--pt-magma`, `--pt-ocean`, `--pt-azure`, `--pt-ice`, …
- Accents: `--pt-solar` (deepens to `--pt-solar-deep` on light), `--pt-verdant`
  — highlight one element, or extend the data cycle.
- Surfaces: dark (`--pt-void`, `--pt-basalt`, `--pt-line-d`, `--pt-text-d*`)
  and light (`--pt-paper*`, `--pt-ink*`, `--pt-line-l`).
- Phase ramp: `--pt-p1`…`--pt-p9` (magma → void → ocean, diverging).
- Module domain colours: `--pt-dom-interior/outgassing/tidal/chem/atmos/stellar`
  — stable and colour-blind-checked.
- Type, spacing (8-pt grid), radii (0–8 px), elevation, gradients.

License: Apache-2.0.
