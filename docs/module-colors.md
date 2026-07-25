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
| Accretion | `--pt-dom-accretion` | `#A38F7A` | Morrigan |

Stellar is solar gold, the star's own colour. On light surfaces the token
deepens to `#C8860F` so the gold keeps adequate contrast (bright gold reads at
2.22:1 on white); in matplotlib use `COLORS["solar_deep"]` for stellar fills
or thin marks on light figures.

Accretion is a muted clay, the rock the planets are built from. It is a
low-chroma warm neutral: legible as a filled swatch on either surface, but on
paper it sits at 2.83:1, so treat it like Atmosphere and Stellar and give thin
lines or small marks a legend rather than leaning on the hue.

## Colour-blind safety

The colours are checked as a **set** under protanopia, deuteranopia, and
tritanopia (Machado 2009, full severity), measured as the CIE76 difference
`ΔE*ab` in CIE Lab under D65, with the simulation applied in linear RGB. The
metric is part of the claim: CIEDE2000 returns substantially smaller numbers
for the same pairs, so a figure quoted without its formula cannot be
reproduced. `tokens/check_cvd.py` performs the measurement and prints every
pair; CI runs it whenever the tokens or these docs change.

On the dark surface set every pair holds ΔE ≥ 16.4, the tightest being Interior
against Outgassing under protanopia. That floor is why Tidal is a desaturated
violet `#593E74` rather than a green or a mid-purple, either of which would
collide with the reds or the blues, and why gold works for Stellar: it sits far
from both in every dichromacy projection.

The light surface set is a different set, because Stellar deepens to `#C8860F`
there, and it is tighter. Interior against Stellar falls to ΔE 11.4 under
deuteranopia, just under the ≥ 12 target in
[figure-conventions.md](figure-conventions.md). Closing that gap means
recolouring Interior or Stellar, which would change module identity across the
whole ecosystem, so it stands as a known limit rather than a pending fix: in
light-surface figures, give those two a legend or a direct label.

Accretion clay `#A38F7A` holds a minimum ΔE of 29.6 against the other six on
both surface sets, its tightest pair being Interior under protanopia, and 11.4
against the rest of the palette. The saturated candidates fail, and they fail in
two different ways. The intuitive earth tones land far below the dark floor,
burnt sienna at 4.8 and umber at 9.0 against Outgassing. A saturated olive-green
clears the domains at 21.0 and then lands 3.8 from `--pt-verdant` under
deuteranopia, trading a collision with the modules for one with the accents; the
brand green itself reaches only 15.7 against Atmosphere under tritanopia. What
clears all three constraints at once, separation from the domains, separation
from the accents, and legibility on Void and on Paper, is low in chroma. A
desaturated sage passes the same three, but green already means something here,
Verdant marks the habitable endpoint, so accretion takes the mineral colour
instead. `check_cvd.py` prints every candidate with the hex its figure was
measured on, scored against the domains and against the rest of the palette.

### Against the rest of the palette

The floor is enforced among the domain colours only. Measured against the
accents, status colours, and ramp anchors, the domains sit much closer: Tidal
is 3.1 from `--pt-abyss` under protanopia, Interior 3.9 from `--pt-warning`
under deuteranopia, Accretion 11.4 from `--pt-verdant` under deuteranopia.
Tightening those would mean recolouring either the semantic set or a module
identity, so `check_cvd.py` reports them and does not fail on them. The
practical consequence is a rule, not a number: a figure that mixes module
identity with status or ramp colour needs a legend, whatever the hues do.

**Do not remap or extend** these without re-running `tokens/check_cvd.py`. If a
new domain is added, pick its colour by maximising the minimum pairwise ΔE
across all dichromacy types against the existing set, check the result on both
surface sets, and read the cross-palette section of the output before settling
on it. The script keeps the roster of domains it expects and fails when
`tokens.css` declares a different set, so a new domain has to be named in
`EXPECTED_DOMAINS` too; that is what stops a colour going missing from passing
as a smaller palette that clears its floor.

## In practice

- Reserve these exact colours for module identity and domain-coded data. Don't
  reuse them decoratively.
- In figures, pair each module's line/marker with its domain colour and keep it
  identical across every paper (see [figure-conventions.md](figure-conventions.md)).
- Module badges: the glyph tinted to the domain colour + the name in Sora +
  domain label in tracked mono. Ready-made in [`../community/`](../community/).
