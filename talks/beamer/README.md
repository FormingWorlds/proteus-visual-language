# PROTEUS beamer theme (Thermocline v1.1)

LaTeX talk theme matching the HTML deck templates. Runs as a **fully light**
or **fully dark** deck (`mode=light|dark`), with phase band, module domain
colors, and per-frame surface overrides.

## Requirements

XeLaTeX or LuaLaTeX (loads fonts via fontspec; refuses pdfLaTeX).
Compile with `latexmk -xelatex talk.tex`.

## Setup

Copy this folder next to your `.tex` file, then add the static-weight OFL
TTFs (download from Google Fonts) into `fonts/`:

```
fonts/InstrumentSans-Regular.ttf   fonts/InstrumentSans-SemiBold.ttf
fonts/Sora-Bold.ttf                fonts/Sora-ExtraBold.ttf
fonts/SplineSansMono-Regular.ttf   fonts/SplineSansMono-Medium.ttf
```

and the logo exports into `assets/`:

```
assets/glyph_phase_dark.png        assets/glyph_phase_light.png
```

(Both ship in the identity kit: `assets/logo/`.)

## Quick start

```latex
\documentclass[11pt, aspectratio=169]{beamer}
\usetheme{proteus}                    % LIGHT deck (default) — every frame light
% \usetheme[mode=dark]{proteus}       % DARK deck — every frame dark
% \usetheme[mode=light, titlesurface=dark]{proteus}  % light deck, dark title

\title[Volatile delivery]{Volatile delivery across the \magma{magma-ocean} epoch}
\subtitle{Exoplanets · Generation 3}     % azure mono eyebrow
\conference{Exoplanets · Cambridge 2026} % top-left label on the title slide
\author{Tim Lichtenberg}
\institute{on behalf of the PROTEUS collaboration · University of Groningen}
\date{12 July 2026}

\begin{document}
\begin{frame}[plain]\titlepage\end{frame}

\section{Results}                        % section page follows the deck mode

\begin{frame}{Three coupled reservoirs}{Model setup}   % title + eyebrow
  \begin{itemize}
    \item \textbf{Interior (SPIDER)} — magma ocean evolution in S–P space.
    \item \textbf{Atmosphere (AGNI)} — radiative-convective equilibrium.
    \item Reserve \magma{magma} for the one thing the room should look at.
  \end{itemize}
\end{frame}

% Drop a single opposite-surface frame in without changing the deck mode:
\begin{darkframes}
\begin{frame}{Hero figure}   % pair with proteus_mpl.use("dark")
  \centering
  \includegraphics[width=0.62\textwidth]{figure_dark.pdf}
\end{frame}
\end{darkframes}

\proteusClosingFrame{Thank you.}{proteus-framework.org · proteus\_dev@formingworlds.space}
\end{document}
```

## Conventions the theme enforces

- **Light or dark deck:** `\usetheme[mode=dark]{proteus}` themes every frame
  (content, title, section, closing) dark; `mode=light` (default) themes them
  light. Override a single frame with `\begin{darkframes}` / `\begin{lightframes}`,
  and force the title surface independently with `titlesurface=dark|light`.
- Sora never renders italic: `\emph{}` maps to bold Magma. Use sparingly.
- Match figure variants to the frame: `proteus_mpl.use()` ↔ light frames,
  `use("dark")` ↔ dark frames.
- The phase band appears on title and closing frames only (matching the HTML
  deck templates' default; enable per-frame elsewhere with
  `\proteusPhaseBand{\paperwidth}{1.6mm}`).
- Module domain colors are available by name: `ProteusDomInterior`,
  `ProteusDomOutgas`, `ProteusDomTidal`, `ProteusDomChem`,
  `ProteusDomAtmos`, `ProteusDomStellar`.
