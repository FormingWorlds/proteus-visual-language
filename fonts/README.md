# Fonts

The PROTEUS visual language uses three open-source typefaces:

| Role | Family | Weights used | License |
|---|---|---|---|
| Display | **Sora** | 600 / 700 / 800 | SIL Open Font License 1.1 |
| Body / UI | **Instrument Sans** | 400 / 500 / 600 | SIL Open Font License 1.1 |
| Mono (code, labels, metadata) | **Spline Sans Mono** | 400 / 500 | SIL Open Font License 1.1 |

Every artifact loads them **self-hosted from this folder**; nothing requests
fonts from a third party. The web pages and the docs drop-in load
[`fonts.css`](fonts.css) (woff2 first, TTF fallback); matplotlib, Beamer, and
print workflows use the TTFs directly:

```
fonts/
├── sora/                 Sora-{SemiBold,Bold,ExtraBold}.{woff2,ttf}
├── instrument-sans/      InstrumentSans-{Regular,Medium,SemiBold}.{woff2,ttf}
├── spline-sans-mono/     SplineSansMono-{Regular,Medium}.{woff2,ttf}
├── OFL.txt               the SIL Open Font License (covers all three families)
└── fonts.css             @font-face rules pointing at the files above
```

To use the fonts in another web project, copy this folder and include
[`fonts.css`](fonts.css) before any stylesheet that uses the token font
stacks; the declared family names match
[`../tokens/tokens.css`](../tokens/tokens.css) exactly. Keep exactly the
weights listed above; the rest of the system assumes them.

Specimen pages:
- Sora — https://fonts.google.com/specimen/Sora
- Instrument Sans — https://fonts.google.com/specimen/Instrument+Sans
- Spline Sans Mono — https://fonts.google.com/specimen/Spline+Sans+Mono

The font licenses are the typefaces' own (OFL 1.1) and are **not** covered by
this repository's Apache-2.0 / CC BY-4.0 licensing.
