# site/ — the interactive brand guide

`index.html` is the PROTEUS brand guide: a scrollable/keyed set of plates
(cover, story, colour, type, logo, motifs, module colours, applications,
governance). It is
deployed to GitHub Pages by [`../.github/workflows/pages.yml`](../.github/workflows/pages.yml)
and served at:

> https://formingworlds.github.io/proteus-visual-language

`logo-lockups.html` is the logo lockup + colorway reference sheet.

Both read from the repo's shared files via relative paths
(`../tokens/tokens.css`, `../logo/glyph/…`, `../templates/deck/deck-stage.js`),
so Pages deploys the **whole repo** and a root redirect sends visitors here.

## PDF

The Pages workflow exports the same guide to `brand-guide.pdf` (headless
Chrome `page.pdf()`, one page per plate via the deck's print CSS) and serves
it at
[brand-guide.pdf](https://formingworlds.github.io/proteus-visual-language/brand-guide.pdf).
To regenerate locally, run the export step from
[`../.github/workflows/pages.yml`](../.github/workflows/pages.yml) in the repo
root (`npm i puppeteer`, then the `node -e` snippet, which writes
`brand-guide.pdf`), or open `index.html` and print to PDF.

Both formats are intentionally kept: the HTML for interactive browsing, the PDF
for circulation and offline reference.
