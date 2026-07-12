#!/usr/bin/env python3
"""Check hand-maintained copies of token values against tokens.css.

``tokens.css`` is the source of truth and ``check_sync.py`` keeps the derived
formats generated from it. Many artifacts additionally duplicate token values
by hand because they cannot read CSS: the docs drop-in stylesheet, the
proteus-mpl colour tables, cycles, and style sheets, the Beamer palette, the
hex values quoted in the docs pages and brand-guide plates, the logo SVGs,
and the ``[data-theme="light"]`` blocks inside ``tokens.css`` itself.

Three kinds of verification are applied:

- **Named copies** (extra.css, proteus-mpl, Beamer, mplstyle files, light
  blocks): every entry is compared against its token through an explicit
  mapping, and the mappings are checked in both directions, so a deleted or
  unmapped entry is an error, not a pass.
- **Row-aware docs**: a docs line that references exactly one ``--pt-*``
  token must quote that token's value on the same line.
- **Membership sweeps**: every remaining hex literal in the covered files
  must be the value of some token, up to explicit per-file allowlists for
  deliberate standalone values.

Membership alone cannot catch a stale hex that is still another token's
value (several tokens deliberately alias the brand core), which is why the
named and row-aware checks exist for everything that carries a name.

Run with no arguments for all checks, or ``--only mpl`` for just the
proteus-mpl package contents (used before the PyPI publish). Exits non-zero
on any discrepancy; extraction that stops matching fails loudly.
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_sync import ParseError, parse_css  # noqa: E402

REPO = Path(__file__).resolve().parent.parent

HEX6 = re.compile(r"#[0-9A-Fa-f]{6}\b")
HEX_SHORT = re.compile(r"#[0-9A-Fa-f]{3,4}\b(?![0-9A-Fa-f])")

# proteus_mpl name -> token name
MPL_COLORS = {
    "magma": "pt-magma",
    "mantle": "pt-mantle",
    "crimson": "pt-crimson",
    "ocean": "pt-ocean",
    "abyss": "pt-abyss",
    "azure": "pt-azure",
    "ice": "pt-ice",
    "void": "pt-void",
    "basalt": "pt-basalt",
    "paper": "pt-paper",
    "ink": "pt-ink",
    "fog": "pt-ink-3",
    "mist": "pt-text-d2",
}
MPL_DOMAINS = {
    "interior": "pt-dom-interior",
    "outgassing": "pt-dom-outgassing",
    "tidal": "pt-dom-tidal",
    "chemistry": "pt-dom-chem",
    "atmosphere": "pt-dom-atmos",
    "stellar": "pt-dom-stellar",
}
# Positional token expectations for the colour sequences; None marks a
# deliberate standalone stop (dark-cycle substitutes, diverging midpoints).
MPL_SEQUENCES = {
    "CYCLE": [
        "pt-dom-interior",
        "pt-dom-chem",
        "pt-dom-tidal",
        "pt-dom-atmos",
        "pt-dom-outgassing",
        "pt-ink",
        "pt-ink-3",
    ],
    "CYCLE_DARK": ["pt-magma", "pt-azure", "pt-ice", None, "pt-text-d", None],
    "_SEQ": ["pt-void", "pt-abyss", "pt-ocean", "pt-azure", "pt-ice", "pt-paper"],
    "_DIV": ["pt-crimson", None, None, None, "pt-ocean"],
    "_PHASE": [f"pt-p{i}" for i in range(1, 10)],
}
# Colour-valued rcparams in the packaged style sheets -> token name.
MPLSTYLE = {
    "proteus.mplstyle": {
        "figure.facecolor": "pt-paper",
        "savefig.facecolor": "pt-paper",
        "axes.facecolor": "pt-paper",
        "axes.edgecolor": "pt-ink",
        "axes.labelcolor": "pt-ink",
        "axes.titlecolor": "pt-ink",
        "grid.color": "pt-line-l",
        "xtick.color": "pt-ink-2",
        "ytick.color": "pt-ink-2",
        "text.color": "pt-ink",
    },
    "proteus_dark.mplstyle": {
        "figure.facecolor": "pt-void",
        "savefig.facecolor": "pt-void",
        "axes.facecolor": "pt-void",
        "axes.edgecolor": "pt-text-d",
        "axes.labelcolor": "pt-text-d",
        "axes.titlecolor": "pt-text-d",
        "grid.color": "pt-line-d",
        "xtick.color": "pt-text-d2",
        "ytick.color": "pt-text-d2",
        "text.color": "pt-text-d",
    },
}

# Beamer \definecolor name -> token name
BEAMER = {
    "ProteusVoid": "pt-void",
    "ProteusBasalt": "pt-basalt",
    "ProteusBasaltTwo": "pt-basalt-2",
    "ProteusMagma": "pt-magma",
    "ProteusMantle": "pt-mantle",
    "ProteusCrimson": "pt-crimson",
    "ProteusOcean": "pt-ocean",
    "ProteusAbyss": "pt-abyss",
    "ProteusAzure": "pt-azure",
    "ProteusIce": "pt-ice",
    "ProteusPaper": "pt-paper",
    "ProteusInk": "pt-ink",
    "ProteusInkSoft": "pt-ink-2",
    "ProteusTextDim": "pt-text-d2",
    "ProteusLineD": "pt-line-d",
    "ProteusLineL": "pt-line-l",
    "ProteusDomInterior": "pt-dom-interior",
    "ProteusDomOutgas": "pt-dom-outgassing",
    "ProteusDomTidal": "pt-dom-tidal",
    "ProteusDomChem": "pt-dom-chem",
    "ProteusDomAtmos": "pt-dom-atmos",
    "ProteusDomStellar": "pt-dom-stellar",
}

# The --pt-* properties the docs drop-in re-declares.
EXTRA_PT = {
    "pt-magma",
    "pt-mantle",
    "pt-crimson",
    "pt-ocean",
    "pt-abyss",
    "pt-azure",
    "pt-ice",
    "pt-void",
    "pt-basalt",
    "pt-line-d",
}

# Light remap: dark-named token -> the light counterpart it must equal.
LIGHT_PAIRS = {
    "pt-void": "pt-paper",
    "pt-basalt": "pt-paper-2",
    "pt-basalt-2": "pt-paper-3",
    "pt-line-d": "pt-line-l",
    "pt-text-d": "pt-ink",
    "pt-text-d2": "pt-ink-2",
    "pt-text-d3": "pt-ink-3",
    "pt-azure": "pt-ocean",
    "pt-ice": "pt-abyss",
}
# Remapped tokens with no counterpart token (theme-specific values by design).
LIGHT_FREE = {"pt-header-bg", "pt-shadow-2"}
# Tokens the dark-in-both-themes restore blocks must reset to base values.
RESTORE_EXPECTED = {
    "pt-text-d",
    "pt-text-d2",
    "pt-text-d3",
    "pt-line-d",
    "pt-azure",
    "pt-ice",
}

# Docs pages checked row-aware (a --pt-* reference pins the hexes on its line).
ROW_DOCS = [
    "docs/color.md",
    "docs/module-colors.md",
    "docs/logo.md",
    "docs/figure-conventions.md",
    "docs/README.md",
]

# path glob -> (allowlisted standalone values, minimum expected hex count)
MEMBERSHIP = [
    (
        "templates/docs/extra.css",
        {"#04060A", "#22303B", "#2A343D", "#B8C6D2", "#C6D0D9", "#E9EEF3"},
        30,
    ),
    ("templates/docs/docs.css", {"#04060A", "#C9A26B"}, 3),
    ("templates/web/site.css", {"#C93321"}, 1),
    ("site/index.html", set(), 20),
    ("site/logo-lockups.html", {"#4A555F", "#8FA0AE", "#C7D3DC"}, 40),
    ("docs/color.md", set(), 20),
    ("docs/module-colors.md", set(), 5),
    ("docs/figure-conventions.md", set(), 5),
    ("docs/logo.md", set(), 4),
    ("docs/README.md", set(), 2),
    ("community/community-kit.html", {"#4A525A", "#5A626A", "#AEB4BA", "#C8CDD2"}, 3),
    ("logo/glyph/*.svg", set(), 40),
    ("logo/favicon/*.svg", set(), 5),
]
# File suffixes where shorthand hex forms (#FFF) are treated as errors.
NO_SHORTHAND_SUFFIXES = {".md", ".html"}


def norm(value):
    """Normalise a colour value for comparison.

    Parameters
    ----------
    value : str
        A colour as written in an artifact (``#RRGGBB`` in any case, or a
        bare ``RRGGBB`` from a Beamer ``\\definecolor``).

    Returns
    -------
    str
        Uppercase ``#RRGGBB`` form; non-hex values are whitespace-collapsed
        unchanged.
    """
    value = " ".join(value.split())
    bare = value[1:] if value.startswith("#") else value
    if re.fullmatch(r"[0-9A-Fa-f]{6}", bare):
        return "#" + bare.upper()
    return value


def token_values(tokens):
    """Collect the plain hex values of the base tokens.

    Parameters
    ----------
    tokens : dict
        Base token mapping from ``tokens.css``.

    Returns
    -------
    set of str
        Uppercase ``#RRGGBB`` values, including hexes embedded in composite
        values such as the gradients.
    """
    values = set()
    for value in tokens.values():
        values |= {h.upper() for h in HEX6.findall(value)}
    return values


def split_decls(block, where):
    """Split a CSS block into custom-property declarations, loudly.

    Parameters
    ----------
    block : str
        Contents of a CSS block (comments already stripped, no nesting).
    where : str
        Label for error messages.

    Returns
    -------
    tuple of (list of (str, str), list of str)
        Parsed ``(name, value)`` pairs (``--`` prefix stripped, whitespace
        collapsed) and problem messages for unparseable segments. Ordinary
        property declarations are skipped silently; only content that is
        neither a declaration nor whitespace is a problem.
    """
    pairs, problems = [], []
    for segment in block.split(";"):
        segment = segment.strip()
        if not segment:
            continue
        decl = re.fullmatch(r"--([A-Za-z0-9-]+)\s*:\s*(.+)", segment, flags=re.S)
        if decl is not None:
            pairs.append((decl.group(1), " ".join(decl.group(2).split())))
        elif not re.fullmatch(r"[A-Za-z-]+\s*:\s*.+", segment, flags=re.S):
            problems.append(f"{where}: cannot parse declaration: {segment[:60]!r}")
    return pairs, problems


def check_extra_css(tokens):
    """Verify the ``--pt-*`` re-declarations in the docs drop-in stylesheet.

    Parameters
    ----------
    tokens : dict
        Base token mapping from ``tokens.css``.

    Returns
    -------
    list of str
        One message per mismatched, unknown, or missing declaration.
    """
    path = REPO / "templates" / "docs" / "extra.css"
    text = re.sub(r"/\*.*?\*/", "", path.read_text(encoding="utf-8"), flags=re.S)
    found = dict(re.findall(r"--(pt-[A-Za-z0-9-]+)\s*:\s*([^;]+);", text))
    problems = []
    for name in sorted(EXTRA_PT - found.keys()):
        problems.append(f"{path.name}: expected declaration '--{name}' is missing")
    for name, value in sorted(found.items()):
        if name not in tokens:
            problems.append(
                f"{path.name}: declares '--{name}', which is not a token in tokens.css"
            )
        elif norm(value) != norm(tokens[name]):
            problems.append(
                f"{path.name}: '--{name}' is {value.strip()}, tokens.css has {tokens[name]}"
            )
    return problems


def check_mpl(tokens):
    """Verify the colour data shipped in the proteus-mpl package.

    Covers the ``COLORS`` and ``DOMAINS`` tables (both directions), the
    colour sequences (positionally, with explicit standalone stops), and the
    colour-valued rcparams in both packaged ``.mplstyle`` files.

    Parameters
    ----------
    tokens : dict
        Base token mapping from ``tokens.css``.

    Returns
    -------
    list of str
        One message per mismatch, unmapped entry, or missing entry.
    """
    sys.path.insert(0, str(REPO / "figures" / "proteus-mpl" / "src"))
    import proteus_mpl

    problems = []
    for label, mapping, table in [
        ("COLORS", MPL_COLORS, proteus_mpl.COLORS),
        ("DOMAINS", MPL_DOMAINS, proteus_mpl.DOMAINS),
    ]:
        for key in sorted(mapping.keys() - table.keys()):
            problems.append(f"proteus_mpl.{label}: expected entry '{key}' is missing")
        for key, value in table.items():
            token = mapping.get(key)
            if token is None:
                problems.append(
                    f"proteus_mpl.{label}: '{key}' has no token mapping in check_copies.py; add one"
                )
            elif norm(value) != norm(tokens[token]):
                problems.append(
                    f"proteus_mpl.{label}['{key}'] is {value}, token '{token}' is {tokens[token]}"
                )
    for label, expected in MPL_SEQUENCES.items():
        actual = getattr(proteus_mpl, label)
        if len(actual) != len(expected):
            problems.append(
                f"proteus_mpl.{label} has {len(actual)} entries, expected {len(expected)}"
            )
            continue
        for i, (value, token) in enumerate(zip(actual, expected)):
            if token is not None and norm(value) != norm(tokens[token]):
                problems.append(
                    f"proteus_mpl.{label}[{i}] is {value}, token '{token}' is {tokens[token]}"
                )
    for filename, mapping in MPLSTYLE.items():
        path = REPO / "figures" / "proteus-mpl" / "src" / "proteus_mpl" / filename
        found = dict(
            re.findall(
                r"(?m)^([a-z.]+)\s*:\s*([0-9A-Fa-f]{6})\s*$",
                path.read_text(encoding="utf-8"),
            )
        )
        for key in sorted(mapping.keys() - found.keys()):
            problems.append(f"{filename}: expected colour rcparam '{key}' is missing")
        for key, value in sorted(found.items()):
            token = mapping.get(key)
            if token is None:
                problems.append(
                    f"{filename}: '{key}' has no token mapping in check_copies.py; add one"
                )
            elif norm(value) != norm(tokens[token]):
                problems.append(
                    f"{filename}: '{key}' is {value}, token '{token}' is {tokens[token]}"
                )
    return problems


def check_beamer(tokens):
    """Verify the ``\\definecolor`` palette in the Beamer theme.

    Parameters
    ----------
    tokens : dict
        Base token mapping from ``tokens.css``.

    Returns
    -------
    list of str
        One message per mismatched, unmapped, or missing colour definition.
    """
    path = REPO / "talks" / "beamer" / "beamerthemeproteus.sty"
    found = dict(
        re.findall(
            r"\\definecolor\s*\{([A-Za-z0-9]+)\}\s*\{HTML\}\s*\{([0-9A-Fa-f]{6})\}",
            path.read_text(encoding="utf-8"),
        )
    )
    problems = []
    for name in sorted(BEAMER.keys() - found.keys()):
        problems.append(f"{path.name}: expected colour '{name}' is missing")
    for name, value in sorted(found.items()):
        token = BEAMER.get(name)
        if token is None:
            problems.append(
                f"{path.name}: '{name}' has no token mapping in check_copies.py; add one"
            )
        elif norm(value) != norm(tokens[token]):
            problems.append(
                f"{path.name}: '{name}' is #{value.upper()}, token '{token}' is {tokens[token]}"
            )
    return problems


def check_docs_rows(tokens):
    """Verify docs lines that pair a ``--pt-*`` name with hex values.

    Parameters
    ----------
    tokens : dict
        Base token mapping from ``tokens.css``.

    Returns
    -------
    list of str
        One message per line whose quoted hex differs from the named token.
    """
    problems = []
    rows = 0
    for page in ROW_DOCS:
        for n, line in enumerate(
            (REPO / page).read_text(encoding="utf-8").splitlines(), 1
        ):
            names = re.findall(r"--(pt-[A-Za-z0-9-]+)", line)
            hexes = HEX6.findall(line)
            if len(set(names)) != 1 or not hexes:
                continue
            rows += 1
            name = names[0]
            if name not in tokens:
                problems.append(
                    f"{page}:{n}: references '--{name}', which is not a token in tokens.css"
                )
                continue
            for value in hexes:
                if norm(value) != norm(tokens[name]):
                    problems.append(
                        f"{page}:{n}: quotes {value} for '--{name}', tokens.css has {tokens[name]}"
                    )
    if rows < 10:
        problems.append(
            f"docs row check: only {rows} token/hex rows found across {len(ROW_DOCS)} pages; extraction broken?"
        )
    return problems


def check_membership(tokens):
    """Verify that hex literals in covered files are current token values.

    Parameters
    ----------
    tokens : dict
        Base token mapping from ``tokens.css``.

    Returns
    -------
    list of str
        One message per hex that is neither a token value nor allowlisted,
        per shorthand hex in files where the convention is 6-digit, and per
        file whose hex count falls below its expected minimum.
    """
    values = token_values(tokens)
    problems = []
    for pattern, allow, minimum in MEMBERSHIP:
        paths = sorted(REPO.glob(pattern))
        if not paths:
            problems.append(f"{pattern}: no files matched; extraction broken?")
            continue
        count = 0
        for path in paths:
            rel = path.relative_to(REPO)
            text = path.read_text(encoding="utf-8")
            for value in HEX6.findall(text):
                count += 1
                if value.upper() not in values and value.upper() not in {
                    a.upper() for a in allow
                }:
                    problems.append(
                        f"{rel}: {value} is not a token value (or allowlisted standalone)"
                    )
            if path.suffix in NO_SHORTHAND_SUFFIXES:
                stripped = HEX6.sub("", text)
                for value in HEX_SHORT.findall(stripped):
                    problems.append(
                        f"{rel}: shorthand hex {value}; write the 6-digit token value"
                    )
        if count < minimum:
            problems.append(
                f"{pattern}: found {count} hex values, expected at least {minimum}; extraction broken?"
            )
    return problems


def check_light_blocks(tokens):
    """Verify the light-theme remap and restore blocks in ``tokens.css``.

    The top-level ``[data-theme="light"]`` block must map each dark-named
    surface token onto its light counterpart; the scoped restore blocks
    (hero, code, API signatures) must reset the expected tokens to their
    base dark values.

    Parameters
    ----------
    tokens : dict
        Base token mapping from ``tokens.css``.

    Returns
    -------
    list of str
        One message per divergent, unclassified, or missing declaration,
        or per structural problem with the blocks themselves.
    """
    text = re.sub(
        r"/\*.*?\*/",
        "",
        (REPO / "tokens" / "tokens.css").read_text(encoding="utf-8"),
        flags=re.S,
    )
    problems = []
    remap_found = {}
    restore_found = {}
    for match in re.finditer(
        r"(?m)^([^{}]*\[data-theme=[\"']?light[\"']?\][^{}]*)\{", text
    ):
        selector = " ".join(match.group(1).split())
        end = text.find("}", match.end())
        if end == -1:
            problems.append(f"tokens.css: unclosed block for selector '{selector}'")
            continue
        block = text[match.end() : end]
        pairs, block_problems = split_decls(block, f"tokens.css '{selector}'")
        problems += block_problems
        is_remap = (
            re.fullmatch(r"\[data-theme=[\"']?light[\"']?\]", selector) is not None
        )
        for name, value in pairs:
            (remap_found if is_remap else restore_found)[name] = value
    if not remap_found:
        problems.append(
            'tokens.css: the [data-theme="light"] remap block was not found; extraction broken?'
        )
        return problems
    for name in sorted((LIGHT_PAIRS.keys() | LIGHT_FREE) - remap_found.keys()):
        problems.append(
            f"tokens.css light remap: expected declaration '--{name}' is missing"
        )
    for name, value in sorted(remap_found.items()):
        if name in LIGHT_FREE:
            continue
        counterpart = LIGHT_PAIRS.get(name)
        if counterpart is None:
            problems.append(
                f"tokens.css light remap: '--{name}' is not classified in check_copies.py; add it to LIGHT_PAIRS or LIGHT_FREE"
            )
        elif norm(value) != norm(tokens[counterpart]):
            problems.append(
                f"tokens.css light remap: '--{name}' is {value}, but its counterpart '{counterpart}' is {tokens[counterpart]}"
            )
    for name in sorted(RESTORE_EXPECTED - restore_found.keys()):
        problems.append(
            f"tokens.css restore blocks: expected declaration '--{name}' is missing"
        )
    for name, value in sorted(restore_found.items()):
        base = tokens.get(name)
        if base is None:
            problems.append(
                f"tokens.css restore blocks: '--{name}' is not a token in tokens.css"
            )
        elif norm(value) != norm(base):
            problems.append(
                f"tokens.css restore blocks: '--{name}' is {value}, base token is {base}"
            )
    return problems


CHECKS = {
    "extra-css": [check_extra_css],
    "mpl": [check_mpl],
    "beamer": [check_beamer],
    "docs": [check_docs_rows, check_membership],
    "light": [check_light_blocks],
}


def main(argv):
    """Run the requested copy checks and report the result.

    Parameters
    ----------
    argv : list of str
        Command-line arguments; ``argv[1:]`` must be empty (all checks) or
        ``["--only", <name>]`` with a name from the check table.

    Returns
    -------
    int
        ``0`` when every checked copy matches the tokens, ``1`` otherwise,
        ``2`` on bad usage.
    """
    if argv[1:] and (
        len(argv[1:]) != 2 or argv[1] != "--only" or argv[2] not in CHECKS
    ):
        print(f"usage: check_copies.py [--only {{{','.join(sorted(CHECKS))}}}]")
        return 2
    selected = [argv[2]] if argv[1:] else sorted(CHECKS)
    try:
        tokens = parse_css((REPO / "tokens" / "tokens.css").read_text(encoding="utf-8"))
    except (OSError, ParseError) as exc:
        print(f"tokens.css: {exc}")
        return 1
    problems = []
    for name in selected:
        for check in CHECKS[name]:
            try:
                problems += check(tokens)
            except OSError as exc:
                problems.append(f"{check.__name__}: {exc}")
    for problem in problems:
        print(problem)
    if problems:
        return 1
    scope = "all" if len(selected) == len(CHECKS) else ", ".join(selected)
    print(f"hand-maintained token copies match tokens.css (checks: {scope})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
