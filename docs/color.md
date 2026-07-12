# Colour

Every value is a token in [`../tokens/tokens.css`](../tokens/tokens.css). Never
hard-code a colour that exists as a token.

## Brand core

| Token | Hex | Role |
|---|---|---|
| `--pt-magma` | `#E23D28` | the hot signal — one moment per surface |
| `--pt-mantle` | `#8E1F12` | deep red, hot fills |
| `--pt-crimson` | `#C2362B` | magma deepened for light surfaces |
| `--pt-ocean` | `#1B6FA8` | interactive, links |
| `--pt-abyss` | `#14406B` | deep blue, heading accents on light |
| `--pt-azure` | `#4FA3D9` | eyebrows, active nav on dark |
| `--pt-ice` | `#A8D4E8` | cool highlight on dark |

## Surfaces

**Dark (default):** Void `#05070B` (page) · Basalt `#0E131B` (cards) · Basalt-2
`#12202E` (hover) · lines `#1A2230` · text `#E9EEF2` / `#9FB0BE` / `#5A6B7A`.

**Light (mirror):** Paper `#F2F5F7` (page) · Paper-2 `#FFFFFF` (cards) · Paper-3
`#E3E9EE` (inset) · lines `#D2DAE1` · ink `#10151B` / `#3E4A55` / `#7A8894`.

Never pure black or white. No warm creams, no amber/gold — those belong to the
sibling Interra project.

## The phase ramp

`--pt-p1`…`--pt-p9`: a diverging ramp **magma → void → ocean**.

```
#E23D28 → #8E1F12 → #3A120C → #05070B → #0E2A45 → #14406B → #1B6FA8 → #4FA3D9 → #A8D4E8
```

Use it for the phase band (page/section closings) and as the diverging colormap
in figures (see [figure-conventions.md](figure-conventions.md)). **Always
hot-left → cold-right. Never reversed.**

## Light / dark

`tokens.css` is dark-first. Set `data-theme="light"` on the root to remap the
dark surface/text tokens to their light values — everything that references them
flips at once. Regions meant to stay dark in both themes (code blocks, hero
bands) restore the dark tokens locally. This mechanism drives the toggle on the
website, docs, and poster; the Beamer theme mirrors it with `mode=light|dark`.

## Rules

- **Magma is scarce** — the active item, the key number, the one thing to look
  at. If everything is red, nothing is.
- **Blue is the living layer** — links, hovers, active states, animation.
- Contrast ≥ 4.5:1 for body text in both themes.
