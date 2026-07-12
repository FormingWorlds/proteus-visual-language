#!/usr/bin/env python3
"""Keep tokens.json and tokens.scss in sync with tokens.css.

``tokens.css`` is the source of truth for all design tokens. The derived
formats carry the base values: every custom property declared in a ``:root``
block of ``tokens.css`` is exported, in declaration order, to ``tokens.json``
and ``tokens.scss``. Theme remaps (the ``[data-theme="light"]`` blocks) are
intentionally excluded.

Run without arguments to verify that the committed derived files match what
this script generates from ``tokens.css``; the exit code is non-zero when
they do not. Run with ``--write`` to regenerate both derived files in place.
Paths resolve relative to this file.
"""

import difflib
import json
import re
import sys
from pathlib import Path

TOKENS_DIR = Path(__file__).resolve().parent

SCSS_HEADER = (
    "// PROTEUS Thermocline design tokens, generated from tokens.css\n"
    "// Do not edit by hand; tokens.css is the source of truth.\n"
    "\n"
)


class ParseError(ValueError):
    """Raised when tokens.css contains a construct the parser cannot handle."""


def parse_css(text):
    """Extract base token values from ``tokens.css``.

    Parameters
    ----------
    text : str
        Contents of ``tokens.css``.

    Returns
    -------
    dict
        Mapping of token name (without the ``--`` prefix) to its value, in
        declaration order, taken from ``:root`` blocks only. Values have
        runs of whitespace collapsed to single spaces.

    Raises
    ------
    ParseError
        If a ``:root`` block contains anything other than custom-property
        declarations, or no tokens are found at all. Constructs the parser
        does not understand fail loudly instead of silently dropping tokens.
    """
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    tokens = {}
    for match in re.finditer(r"(?im)^[^{}@]*:root\b[^{}]*\{", text):
        end = text.find("}", match.end())
        if end == -1:
            raise ParseError("unclosed :root block")
        block = text[match.end() : end]
        if "{" in block:
            raise ParseError("nested rule inside a :root block is not supported")
        for segment in block.split(";"):
            segment = segment.strip()
            if not segment:
                continue
            decl = re.fullmatch(r"--([A-Za-z0-9-]+)\s*:\s*(.+)", segment, flags=re.S)
            if decl is None:
                raise ParseError(
                    f"cannot parse declaration in :root block: {segment!r}"
                )
            tokens[decl.group(1)] = " ".join(decl.group(2).split())
    if not tokens:
        raise ParseError("no custom properties found in any :root block")
    return tokens


def render_json(tokens):
    """Render the canonical ``tokens.json`` text.

    Parameters
    ----------
    tokens : dict
        Token mapping parsed from ``tokens.css``.

    Returns
    -------
    str
        JSON object with two-space indentation, one token per line, in
        declaration order, ending with a newline.
    """
    return json.dumps(tokens, indent=2) + "\n"


def render_scss(tokens):
    """Render the canonical ``tokens.scss`` text.

    Parameters
    ----------
    tokens : dict
        Token mapping parsed from ``tokens.css``.

    Returns
    -------
    str
        SCSS variable declarations (``$name: value;``), one per line, in
        declaration order, preceded by a fixed header comment.
    """
    return SCSS_HEADER + "".join(
        f"${name}: {value};\n" for name, value in tokens.items()
    )


def main(argv):
    """Verify or regenerate the derived token files.

    Parameters
    ----------
    argv : list of str
        Command-line arguments; ``argv[1:]`` must be empty (check mode) or
        ``["--write"]`` (regenerate mode).

    Returns
    -------
    int
        ``0`` on success, ``1`` when the files are out of sync or unreadable,
        ``2`` on bad usage.
    """
    if argv[1:] not in ([], ["--write"]):
        print("usage: check_sync.py [--write]")
        return 2
    try:
        tokens = parse_css((TOKENS_DIR / "tokens.css").read_text(encoding="utf-8"))
    except (OSError, ParseError) as exc:
        print(f"tokens.css: {exc}")
        return 1
    rendered = {
        "tokens.json": render_json(tokens),
        "tokens.scss": render_scss(tokens),
    }
    if argv[1:] == ["--write"]:
        for name, text in rendered.items():
            (TOKENS_DIR / name).write_text(text, encoding="utf-8")
            print(f"wrote {name} ({len(tokens)} tokens)")
        return 0
    stale = 0
    for name, expected in rendered.items():
        try:
            actual = (TOKENS_DIR / name).read_text(encoding="utf-8")
        except OSError as exc:
            print(f"{name}: {exc}")
            stale += 1
            continue
        if actual != expected:
            stale += 1
            print(
                f"{name} is out of sync with tokens.css; "
                "run 'python3 tokens/check_sync.py --write' to regenerate"
            )
            diff = difflib.unified_diff(
                actual.splitlines(),
                expected.splitlines(),
                f"{name} (committed)",
                f"{name} (regenerated)",
                lineterm="",
            )
            for line in list(diff)[:40]:
                print(f"  {line}")
    if stale:
        return 1
    print(
        f"tokens.json and tokens.scss are in sync with tokens.css ({len(tokens)} tokens)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
