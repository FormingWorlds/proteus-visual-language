# Changelog

All notable changes to the PROTEUS Visual Language are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/); this project
uses [semantic versioning](https://semver.org/). The major version tracks
the design generation (Thermocline launches the v1 series) and also bumps
on breaking changes, such as removing or renaming a token. Git tags carry a
`v` prefix (`v1.0.0`); the published packages use the same number without
it.

## [1.2.0] - 2026-07-25

### Added
- **Accretion domain colour**: clay (`--pt-dom-accretion` `#A38F7A`) for Morrigan and the accretion domain, taking the module palette to seven. It keeps a minimum ΔE of 29.6 against the other six under protanopia, deuteranopia, and tritanopia (Machado 2009 at full severity, CIE76 `ΔE*ab`), comfortably above the 16.0 floor the check enforces on the dark surface set, and holds the same figure on the light set. The intuitive earth tones land far below that floor, burnt sienna at 4.8 and umber at 9.0 against Outgassing. An olive-green clears the domains at 21.0 and then sits 3.8 from `--pt-verdant` under deuteranopia, trading a collision with the modules for one with the accents, and the brand green itself reaches only 15.7 against Atmosphere under tritanopia. Clay clears both sets by the widest margin of any domain. Its two nearest neighbours in the rest of the palette are `--pt-verdant` at 11.39 and `--pt-positive` at 11.45, both under deuteranopia, close enough that a figure mixing accretion data with status colour needs a legend either way. Like Stellar and Atmosphere it is a light-toned hue, 2.8:1 on Paper, so small marks in it want a legend rather than the hue alone.
- proteus-mpl gains `DOMAINS["accretion"]` and the Beamer theme gains `ProteusDomAccretion`, so the colour is available in figures and decks alongside the CSS token.
- `glyph_clay` colorway in SVG, PNG, JPG, and PDF, completing the domain-tint matrix at seven. Same geometry as every other colorway, recoloured; the JPG sits on Void, where clay reads at 6.5:1 against 2.8:1 on paper.
- Morrigan joins the module identity grid and the coupling diagram in the community kit, as the accretion node.
- `tokens/check_cvd.py`, run in CI alongside the other token checks, measures every domain pair under all three dichromacies on both surface sets and fails when one drops below its floor. The docs asked contributors to re-run the CVD check before remapping or extending the domain colours; this is that check. It reads the hexes from `tokens.css`, names the metric, and lists the rejected accretion candidates with the hex each figure was measured on, so the quoted numbers can be reproduced rather than taken on trust. It also measures the domains against the accents, status colours, and ramp anchors and reports those pairs without failing on them, since the tight ones there (Tidal 3.1 from `--pt-abyss`, Interior 3.9 from `--pt-warning`) can only be closed by recolouring one set or the other. It holds the roster as well as the floors: it fails when `tokens.css` declares a set of domains other than the one it expects, and on either surface block it fails on a domain written in a form it cannot measure, so a colour that is removed, renamed, or moved behind a `var()` cannot pass as a smaller palette with a wider minimum. `CROSS_PALETTE` is a required minimum rather than an exact roster, so an accent that is renamed or moved behind a `var()` fails the check while a newly added one is measured once it is listed there. It reads the two blocks the palette ships in and nothing else, so a value set inside a media query or a cascade layer cannot stand in for the shipped one. Everywhere else in the file a domain colour is allowed only when it repeats the value one of those two blocks gives that domain. Custom properties inherit, so `:root:root`, `:root body` and an `@media screen` wrapper all reach the page: a component retint that restores a base colour passes, and any other colour is refused rather than measured underneath the rule that would actually win. A selector list is judged part by part, because a list such as `:root, body` also declares the colour on body, where a later `:root` block takes it back for the root element alone and leaves the visible page on the value the list gave it. An `@property` registration is read the same way through its `initial-value`, which is what an element computes wherever the property does not reach it by inheritance, so a registration declaring `inherits: false` cannot hand the whole page below the root a colour the palette never measured. Every `initial-value` in the block is read, since a repeated descriptor resolves the way a repeated declaration does, and the at-rule keyword is matched in whatever case it is written, the way CSS matches it. It also requires the light block to come after the base one, since the two select the root element at equal specificity and the block written last is the one that applies, and it refuses a nested rule rather than skipping it.
- `tokens/check_cvd_selftest.py`, also run in CI, pins how the separability check reads `tokens.css`. It runs sixty-three cases against a scratch copy of `tokens/` and asserts two things about each, the exit code and the reason printed with it, so a case cannot pass on an unrelated failure. Eighteen are valid CSS the check has to keep reading, among them the committed palette itself, a compound `[data-theme="light"] .hero` rule and a `:root > .panel` subtree that each repeat a shipped colour, that same colour repeated under `@media screen`, again through a `:root, body` list, and again as the initial value of an `@property` registration, a theme selector written as a selector list, with single quotes, without quotes, and with the case-insensitive `i` flag against a differently cased value, a final declaration with no semicolon, a byte-order mark, a priority flag, and braces inside quoted, parenthesised, and custom-property values. The other forty-five have to be caught, among them a domain behind a `var()`, a three-digit hex, a missing or extra token, a value shadowed later in the same block, a nested `&` rule, a collision hidden behind comment markers inside string values, a good value left inside a media query or cascade layer, a domain retinted through `:root:root`, `html`, `:root body`, a subtree, `@media screen`, `@supports`, or two nested at-rules, either palette block listed with another element and then taken back for the root alone, an `@property` registration whose initial value is another domain's colour, is missing altogether, or opens on a shipped colour and repeats the descriptor with an unmeasured one, a light block written before the base palette, and a collision confined to one surface set or to one dichromacy. The unmutated case also pins one measured figure per dichromacy, so a simulation matrix cannot be rewritten and still report the palette as sound. The working tree is never touched.

### Changed
- The colour-blind safety notes in `docs/module-colors.md` and `docs/figure-conventions.md` now name the difference metric and report both surface sets. The 16.36 minimum describes the dark set; on the light set, where Stellar deepens to `#C8860F` for contrast on paper, Interior against Stellar measures 11.44 under deuteranopia, just under the ≥ 12 target. Closing it would mean recolouring a module identity across the ecosystem, so it is documented as a known limit with the advice to label those two series in light-surface figures.

## [1.1.2] - 2026-07-14

### Changed
- `proteus-mpl` and `@formingworlds/proteus-tokens` now carry and release from the same version, keeping the PyPI and npm packages in lockstep. `proteus-mpl` moves to 1.1.2 with no code or colour changes.

### Added
- `tokens/check_versions.py`, run in CI on pull requests and again as a release preflight, asserts that `tokens/package.json` and `figures/proteus-mpl/pyproject.toml` declare the same version. The release stops before either package publishes if the two disagree, so they cannot drift apart.

## [1.1.1] - 2026-07-14

### Added
- On-brand JPG lockup panels in `logo/lockup/`: `proteus-lockup-dark.jpg` (on Void) and `proteus-lockup-light.jpg` (on Paper), 924x540 with the clearspace baked in. These are the ready-to-ship form for contexts without transparency (a Discord avatar, an image embed), giving the wordmark the same on-brand JPG treatment the glyph colorways already have. The pure `*-on-black.jpg` / `*-on-white.jpg` compositions stay for the surfaces that need them.
- Vector PDF exports for the whole glyph set in `logo/glyph/`: every single colorway (`glyph_magma` through `glyph_solar`), the multi-colour `glyph_phase`, and `glyph_phase_dark` / `glyph_phase_light`, each tight-cropped to the glyph, plus `logo/favicon/favicon.pdf`. This completes SVG/PNG/JPG/PDF parity for the glyph; `glyph_mono` stays SVG-only by design.
- SVG sources completing the phase set under its two surface names: `glyph_phase_light.svg`, a light-surface variant with deepened tones, and `glyph_phase_dark.svg`, the master palette under the dark-surface name, alongside the multi-colour master `glyph_phase.svg`.

### Changed
- The transparent lockup PDFs (`proteus-lockup-dark-transparent.pdf` and `-light-transparent.pdf`) are now fully vector: the wordmark text and the phase glyph both ship as paths, replacing the earlier form that carried the glyph as an embedded raster. Page box and layout are unchanged.
- Glyph handedness is consistent across every format. The vector glyphs (SVG and PDF) share the orientation of the raster and lockup assets, with the bright arc sweeping in from the left in each deliverable.

## [1.1.0] - 2026-07-13

### Added
- **Accent colours**: Solar Gold (`--pt-solar` `#E0A32E`, auto-deepening to `--pt-solar-deep` `#C8860F` on light surfaces) for the star and its irradiation, and Verdant (`--pt-verdant` `#57A05C`) for the habitable endpoint. Both widen the categorical plot cycle for many-line figures and are CVD-validated as a set (Machado 2009): light cycle worst-pair ΔE 15.7, dark 16.8.
- proteus-mpl: `CYCLE` grows to 9 colours and `CYCLE_DARK` (still 6) swaps azure and grey for solar and a brightened verdant, both cycles reordered neutral-first (first series draws in ink/paper); `COLORS` gains `solar`, `solar_deep`, `verdant`; a `use("white")` variant for journals that require a pure-white page; the OFL brand fonts now ship inside the package and register automatically.
- Beamer: `ProteusSolar` / `ProteusSolarDeep` / `ProteusVerdant` colours and `\solar{}` / `\verdant{}` helpers; `\solar{}` follows the active frame surface.
- `glyph_solar` colorway (SVG, PNG, JPG) completing the domain-tint matrix.
- Background-free lockup exports in `logo/lockup/`: transparent PNG and PDF
  (vector wordmark text) in both letter colours, and plain on-black / on-white
  JPG compositions for contexts without transparency. The README uses the
  transparent pair.

### Changed
- **Framework tag position**: the tag sits tucked into the lockup's lower-right corner (raised 0.03x, inset 0.32x of the wordmark size) in every template and page; all eight lockup exports regenerated, the transparent exports now measure 1554x370.
- **Stellar (MORS) domain colour** from pale ice `#A8D4E8` to Solar Gold `#E0A32E`: the star gets its own colour, the six-domain CVD minimum stays at ΔE 16.4, and the recolour fixes ice being nearly invisible (1.59:1) on white pages.
- `docs/color.md` restructured into primaries / accents / neutrals tiers.

## [1.0.0] - 2026-07-12

First public release of the **Thermocline** visual language.

### Added
- **Tokens** (`tokens/`): full light + dark palette, type scale, spacing, radii,
  the magma→void→ocean phase ramp, and the six module domain colours — shipped
  as `tokens.css`, `tokens.json`, and `tokens.scss`.
- **Logo** (`logo/`): the phase glyph in all colorways (phase dark/light, magma,
  ice, ink, paper, ocean, and per-domain tints), wordmark lockups, and favicon
  source.
- **Templates** (`templates/`): production stylesheets for web (`site.css`),
  docs (`extra.css` for zensical/mkdocs, plus `docs.css`), decks, and an A0
  poster. Light/dark toggle via `theme.js`.
- **proteus-mpl** (`figures/`): pip-installable matplotlib theme with
  colour-blind-checked cycles and the phase + sequential colormaps.
- **Beamer theme** (`talks/`): LaTeX presentation theme.
- **Community kit** (`community/`): GitHub social/README banners, module
  identity badges, the coupler diagram language, and a sticker sheet.
- **Brand guide**: interactive (`site/`) + per-topic Markdown (`docs/`).

[1.2.0]: https://github.com/FormingWorlds/proteus-visual-language/releases/tag/v1.2.0
[1.1.2]: https://github.com/FormingWorlds/proteus-visual-language/releases/tag/v1.1.2
[1.1.1]: https://github.com/FormingWorlds/proteus-visual-language/releases/tag/v1.1.1
[1.1.0]: https://github.com/FormingWorlds/proteus-visual-language/releases/tag/v1.1.0
[1.0.0]: https://github.com/FormingWorlds/proteus-visual-language/releases/tag/v1.0.0
