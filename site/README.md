# site/ — the interactive brand guide

`index.html` is the PROTEUS brand guide: a scrollable/keyed set of plates
(cover, story, colour, type, logo, motifs, module colours, applications). It is
deployed to GitHub Pages by [`../.github/workflows/pages.yml`](../.github/workflows/pages.yml)
and served at:

> https://formingworlds.github.io/proteus-visual-language

`logo-lockups.html` is the logo lockup + colorway reference sheet.

Both read from the repo's shared files via relative paths
(`../tokens/tokens.css`, `../logo/glyph/…`, `../templates/deck/deck-stage.js`),
so Pages deploys the **whole repo** and a root redirect sends visitors here.

## PDF

The same guide is exported to [`../brand-guide.pdf`](../brand-guide.pdf) — one
page per plate — by the Pages workflow (headless Chrome `page.pdf()`, using the
deck's per-slide print CSS). To regenerate locally:

```bash
npx puppeteer print   # or: open index.html and File → Print → Save as PDF
```

Both formats are intentionally kept: the HTML for interactive browsing, the PDF
for circulation and offline reference.
