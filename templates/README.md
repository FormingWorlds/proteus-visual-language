# Templates

Production-ready building blocks. Each subfolder is the real stylesheet/markup
used by the PROTEUS site, docs, decks, and poster — copy what you need.

```
templates/
├── web/      site.css + theme.js — website chrome (header, footer, buttons,
│             tables, phase-rule) and the OS-aware light/dark toggle.
├── docs/     extra.css — the zensical/mkdocs override (drop into any module's
│             docs build); docs.css + docs.js — the standalone docs shell.
├── deck/     deck-templates.html — light + dark slide templates, driven by
│             deck-stage.js; image-slot.js for user-fillable images.
└── poster/   poster-a0.html — A0 conference poster (print at 100%).
```

All of them pull their values from [`../tokens/tokens.css`](../tokens/tokens.css)
and expect the fonts (see [`../fonts/README.md`](../fonts/README.md)) and logo
assets from [`../logo/`](../logo/).

## Notes

- **Docs:** `extra.css` is the homogeneity mechanism — the same file dropped
  into every module's zensical build makes every docs site one product. Add the
  logo + favicon from `logo/` and you're done. Dark (default, OS-aware) and
  light schemes are both included.
- **Web:** the full site (home, modules, demos, validation, publications,
  license, people) is demonstrated in the design project; here we ship the
  shared chrome those pages are built from.
- **Decks:** open `deck/deck-templates.html`, arrow-key through the slides; the
  set covers title, section, bullets, figure, table, statement, and closing in
  both light and dark.
