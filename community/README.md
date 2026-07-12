# Community kit

Reference canvas for the community-facing assets, in one HTML page
([`community-kit.html`](community-kit.html)) with five frames:

1. **GitHub social preview** (1280 × 640) for repository social cards.
2. **README header banner** (1920 × 420) to drop into module READMEs.
3. **Module mini-identities**: the phase glyph tinted per domain colour,
   with name badges for every module.
4. **Diagram language**: the coupler figure conventions used in talks and
   papers (node shapes, arrow styles, domain colours).
5. **Sticker sheet**: print-ready circle (⌀ 50 mm), hex (50 mm), die-cut
   glyph (45 mm), and wordmark (90 × 32 mm) shapes.

The page reads the shared tokens and fonts via relative paths, so open it
from a full checkout. To export a frame at its native pixel size, screenshot
the frame element (frames 01 and 02 state their pixel size in the label),
or print to PDF for the sticker sheet. The neutral grays on the sticker
sheet mimic a cut-mat background and are deliberately not brand tokens.
