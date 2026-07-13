# Colour

Every value is a token in [`../tokens/tokens.css`](../tokens/tokens.css). Never
hard-code a colour that exists as a token. The palette is organised in three
tiers: **primaries**, **accents**, and **neutrals**.

## Primaries: text, titles, backgrounds

| Token | Hex | Role |
|---|---|---|
| `--pt-magma` | `#E23D28` | the hot signal — one moment per surface |
| `--pt-mantle` | `#8E1F12` | deep red, hot fills |
| `--pt-crimson` | `#C2362B` | magma deepened for light surfaces |
| `--pt-ocean` | `#1B6FA8` | interactive, links |
| `--pt-abyss` | `#14406B` | deep blue, heading accents on light |
| `--pt-void` / `--pt-ink` | `#05070B` / `#10151B` | ground on dark, text on light |
| `--pt-paper` | `#F2F5F7` | ground on light |

## Accents: highlight one element, or extend a data series

| Token | Hex | Role |
|---|---|---|
| `--pt-solar` | `#E0A32E` | **the star and its irradiation**, the energy source of the magma-to-ocean transition; auto-deepens to `--pt-solar-deep` `#C8860F` on light surfaces (3.06:1 on white) |
| `--pt-verdant` | `#57A05C` | **the habitable endpoint**: surface, biosphere, the temperate outcome |
| `--pt-azure` | `#4FA3D9` | eyebrows, active nav on dark; also the last slot of the plot cycle |
| `--pt-ice` | `#A8D4E8` | cool highlight on dark |

The palette spans the full physical arc: star, magma, ocean, verdant. Solar
and verdant are accents, not new primaries: a single highlighted element, or
the extra range a many-series figure needs. Reserve magma for the one hot
moment; reach for the accents only when the range is genuinely required.
Verdant is distinct from the semantic `--pt-positive` (`#2E8B57`), which stays
reserved for success and status UI.

## Neutrals: footers, eyebrows, low-priority

Dark text tiers `--pt-text-d2` / `--pt-text-d3` (`#9FB0BE` / `#5A6B7A`), light
tiers `--pt-ink-2` / `--pt-ink-3` (`#3E4A55` / `#7A8894`). Softer than the
primaries; for supporting metadata, captions, and chrome, never for a
highlighted element.

## Surfaces

**Dark (default):** Void `#05070B` (page) · Basalt `#0E131B` (cards) · Basalt-2
`#12202E` (hover) · lines `#1A2230` · text `#E9EEF2` / `#9FB0BE` / `#5A6B7A`.

**Light (mirror):** Paper `#F2F5F7` (page) · Paper-2 `#FDFDFE` (cards) · Paper-3
`#E3E9EE` (inset) · lines `#D2DAE1` · ink `#10151B` / `#3E4A55` / `#7A8894`.

Never pure black or white, and no warm creams. Gold appears only as an accent,
never as a surface or a large fill.

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
website and the standalone docs shell; the poster and the mkdocs drop-in
implement the same light/dark pairing with their own switches, and the Beamer
theme mirrors it with `mode=light|dark`.

## Rules

- **Magma is scarce** — the active item, the key number, the one thing to look
  at. If everything is red, nothing is.
- **Blue is the living layer** — links, hovers, active states, animation.
- Contrast ≥ 4.5:1 for body text in both themes.
