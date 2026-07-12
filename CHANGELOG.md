# Changelog

All notable changes to the PROTEUS Visual Language are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/); this project
uses [semantic versioning](https://semver.org/). The major version tracks
the design generation (Thermocline launches the v1 series) and also bumps
on breaking changes, such as removing or renaming a token. Git tags carry a
`v` prefix (`v1.0.0`); the published packages use the same number without
it.

## [Unreleased]

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

[unreleased]: https://github.com/FormingWorlds/proteus-visual-language/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/FormingWorlds/proteus-visual-language/releases/tag/v1.0.0
