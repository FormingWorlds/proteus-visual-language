# Contributing to the PROTEUS Visual Language

Thanks for helping keep the PROTEUS identity coherent. A few ground rules keep
the system from drifting.

## Golden rule: tokens are the source of truth

Every colour, font, size, radius, and shadow lives in
[`tokens/tokens.css`](tokens/tokens.css). If you need a value, use a token. If
the value doesn't exist yet, **add it to the tokens first**, then regenerate the
derived formats (see below) — never hard-code a raw hex or px in a stylesheet or
template.

### Regenerate derived token formats

`tokens.json` and `tokens.scss` are generated from `tokens.css`. After editing
`tokens.css`, run `python3 tokens/check_sync.py --write` to regenerate them,
and commit all three together. CI runs the same script in check mode
(`python3 tokens/check_sync.py`, no arguments) to verify the three files
agree; run it locally before pushing.

Some artifacts duplicate token values by hand because they cannot read CSS:
the docs stylesheets (`templates/docs/`), the matplotlib theme
(`figures/proteus-mpl`, including its style sheets and colour cycles), the
Beamer theme (`talks/beamer`), the hex values quoted in the docs pages and
brand-guide plates, the logo SVGs, and the light-theme blocks inside
`tokens.css` itself. After a token value change, update those copies too;
CI runs `python3 tokens/check_copies.py` to verify them against
`tokens.css`.

## What must not change without a design review

- **Glyph geometry.** The phase glyph's concentric-ring construction is fixed.
  Recolour it (colorways live in `logo/glyph/`); never redraw it.
- **The three typefaces.** Sora, Instrument Sans, Spline Sans Mono. Never
  Space Grotesk or JetBrains Mono; the stack is a deliberate identity choice.
- **The module domain colours.** They are stable and colour-blind-checked as a
  set (see [`docs/module-colors.md`](docs/module-colors.md)). Don't remap or
  extend them without re-running the CVD ΔE check.
- **The phase gradient direction.** Always hot-left → cold-right.

## Proposing a change

1. Open an issue describing the change and why the current system doesn't cover
   it. Attach a screenshot or mock.
2. For anything touching the four items above, wait for a maintainer's ✅ before
   a PR — these are deliberate constraints, not oversights.
3. Keep PRs scoped: a token change, a new template, or a doc fix — not all
   three at once.

## Releasing

Tag releases as `vX.Y.Z` (semantic versioning; Thermocline launches the v1
series, and the major version bumps on a new design generation or a breaking
change). The tag triggers the release workflow, which publishes
`@formingworlds/proteus-tokens` to npm and `proteus-mpl` to PyPI. Before
tagging, set the same version without the `v` prefix (e.g. `1.0.0`) in
`tokens/package.json` and `figures/proteus-mpl/pyproject.toml`, and bump
`CHANGELOG.md` in the same PR.

Questions: proteus_dev@formingworlds.space
