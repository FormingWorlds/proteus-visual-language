# Changelog

All notable changes to the PROTEUS Visual Language are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/); this project
uses [semantic versioning](https://semver.org/). The major version tracks
the design generation (Thermocline launches the v1 series) and also bumps
on breaking changes, such as removing or renaming a token. Git tags carry a
`v` prefix (`v1.0.0`); the published packages use the same number without
it.

## [Unreleased]

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

[unreleased]: https://github.com/FormingWorlds/proteus-visual-language/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/FormingWorlds/proteus-visual-language/releases/tag/v1.1.0
[1.0.0]: https://github.com/FormingWorlds/proteus-visual-language/releases/tag/v1.0.0
