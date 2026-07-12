# Typography

Three families, no others. All artifacts load them self-hosted from
[`../fonts/`](../fonts/README.md); no third-party font requests.

| Role | Family | Weights | Notes |
|---|---|---|---|
| Display | **Sora** | 600 / 700 / 800 | Tight tracking (−0.02 to −0.025em). No italics by design — emphasis maps to bold magma. |
| Body / UI | **Instrument Sans** | 400 / 500 / 600 | Paragraphs, labels, tables, controls. |
| Mono | **Spline Sans Mono** | 400 / 500 | Code, axis labels, eyebrows, captions, versions, metadata — the PROTEUS signature. |

**Not** Space Grotesk, **not** JetBrains Mono.

## Scale

12 / 13 / 14 / 16 / 18 / 20 / 24 / 32 / 44 / 60 / 84 / 120 px (tokens
`--pt-fs-*`). Slides never below 24 px; print never below 12 pt.

## Signature moves

- **Eyebrows:** Spline Sans Mono, uppercase, tracked +0.18em, in Azure (dark) or
  Ocean (light). Use above titles and as section labels.
- **Metadata & numbers:** always mono. Versions, dates, DOIs, axis labels,
  slide numbers.
- **Display headings:** Sora, tight, large. Let type carry the page.
- **Emphasis:** `emph` = bold magma, used sparingly (one per view).

Full type stacks are in [`../tokens/tokens.css`](../tokens/tokens.css):
`--pt-font-display`, `--pt-font-body`, `--pt-font-mono`.
