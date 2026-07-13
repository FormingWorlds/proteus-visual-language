# Applications

How the system shows up across surfaces. Each has a ready-made starting point in
this repo.

## Web — `templates/web/`
Shared chrome in `site.css`: sticky header with a magma active-tick, dropdown
nav, hairline tables, phase-rule footer. Light/dark via `theme.js` (OS-aware,
persisted). The full site (home, modules, demos, validation, publications,
license, people) lives with the production website; the stylesheet here is the
shared chrome it is built from.

## Docs (zensical / mkdocs) — `templates/docs/`
Drop `extra.css` into any module's docs build, add the logo + favicon, done.
This one stylesheet across every module's docs is the homogeneity mechanism.
Dark (default, OS-aware) and light schemes included. `docs.css` + `docs.js` are
the standalone docs shell (header, tabs, 3-column, scroll-spy TOC, magma-spine
code blocks, admonitions, domain badges).

## Decks — `templates/deck/`
`deck-templates.html`: title, section, bullets, text+figure, figure-hero, table,
statement, closing — in **both light and dark**. Driven by `deck-stage.js`;
`image-slot.js` for user-fillable figures.

## Poster — `templates/poster/`
`poster-a0.html`: A0 portrait, three-column, with a **light and dark** variant
(toggle top-right; print at 100%). Figure slots take `proteus-mpl` exports.

## Figures — `figures/proteus-mpl/`
`pip install proteus-mpl`; `proteus_mpl.use()` / `use("dark")` / `use("white")`.
Brand colour cycles (domain set and both cycles CVD-checked), the phase
diverging colormap, a sequential map, and the bundled brand fonts — every
figure in every paper carries the identity. Match the figure variant to its
surface (light figure ↔ light slide/frame, dark ↔ dark, white for journal
pages).

## Talks (LaTeX) — `talks/beamer/`
`\usetheme[mode=dark]{proteus}` or `mode=light` — a fully light or dark deck,
matching the HTML deck templates. The default is the light deck: projection
washes out dark surfaces, so the Beamer theme deliberately defaults light. Per-frame override with `darkframes` /
`lightframes`.

## Community — `community/`
GitHub social-preview and README banners, module identity badges, the coupler
diagram language, and a sticker sheet.

## Do / don't

**Do:** trace every value to a token · keep one hot moment per surface · use
mono for all metadata · match figure theme to surface theme.

**Don't:** introduce a new font or colour · reverse the phase gradient · style a
docs page differently from a marketing page · remap module colours · put the
glyph on a busy background without a scrim.
