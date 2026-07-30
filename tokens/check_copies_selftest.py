#!/usr/bin/env python3
"""Pin how ``check_copies.py`` reads the docs drop-in stylesheet.

``check_extra_css`` is the one reader in ``check_copies.py`` that has to
understand CSS structure rather than match a name against a table: it tells
``:root`` apart from the ``default`` scheme block so a light value is measured
against its light counterpart instead of the base token it departs from on
purpose. A reader like that fails quietly when it fails, passing a file it has
misread, so each case here asserts both the exit code and the reason printed
with it and a case cannot pass on an unrelated failure.

Every case runs against a scratch copy of ``tokens/`` and ``templates/``; the
working tree is never touched. Run with no arguments; the exit code is
non-zero when any case does not behave as pinned.
"""

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
STYLESHEET = Path("templates") / "docs" / "extra.css"

# Valid CSS the reader has to keep reading: (name, edit).
ACCEPTED = [
    (
        "the committed stylesheet",
        lambda css: css,
    ),
    (
        "light selector written without quotes",
        lambda css: css.replace(
            '[data-md-color-scheme="default"] {', "[data-md-color-scheme=default] {", 1
        ),
    ),
    (
        "light selector written with single quotes",
        lambda css: css.replace(
            '[data-md-color-scheme="default"] {',
            "[data-md-color-scheme='default'] {",
            1,
        ),
    ),
    (
        "light selector with the case-insensitive flag against a differently cased value",
        lambda css: css.replace(
            '[data-md-color-scheme="default"] {',
            '[ data-md-color-scheme = "DEFAULT" i ] {',
            1,
        ),
    ),
    (
        "a final declaration with no semicolon",
        lambda css: css.replace("  --pt-info: #1B6FA8;\n}", "  --pt-info: #1B6FA8\n}", 1),
    ),
    (
        "a rule that only reads tokens through var()",
        lambda css: css + "\n.pt-selftest { color: var(--pt-magma); }\n",
    ),
]

# CSS the reader has to refuse: (name, edit, expected fragment of the reason).
REFUSED = [
    (
        "a base value that is not the token's",
        lambda css: css.replace("--pt-dom-accretion: #A38F7A;", "--pt-dom-accretion: #A38F7B;"),
        "tokens.css has #A38F7A",
    ),
    (
        "a light value that is not its counterpart's",
        lambda css: css.replace("--pt-dom-stellar: #C8860F;", "--pt-dom-stellar: #E0A32E;"),
        "counterpart 'pt-solar-deep'",
    ),
    (
        "a base declaration removed",
        lambda css: css.replace("  --pt-p5: #0E2A45;\n", ""),
        "expected declaration '--pt-p5' is missing",
    ),
    (
        "a token the palette does not define",
        lambda css: css.replace(
            "  --pt-info: #1B6FA8;", "  --pt-info: #1B6FA8;\n  --pt-bogus: #123456;"
        ),
        "not a token in tokens.css",
    ),
    (
        "a token declared in the slate block",
        lambda css: css.replace(
            '[data-md-color-scheme="slate"] {',
            '[data-md-color-scheme="slate"] {\n  --pt-dom-atmos: #4FA3D9;',
            1,
        ),
        "is declared under",
    ),
    (
        "a token declared under a compound selector",
        lambda css: css.replace(
            '[data-md-color-scheme="default"] .md-header {',
            '[data-md-color-scheme="default"] .md-header {\n  --pt-magma: #E23D28;',
            1,
        ),
        "is declared under",
    ),
    (
        "a selector list that also targets another element",
        lambda css: css.replace(":root {", ":root, body {", 1),
        "is declared under",
    ),
    (
        "a palette block wrapped in a media query",
        lambda css: css.replace(
            ":root {",
            "@media (prefers-color-scheme: dark) {\n  .pt-decoy { color: red; }\n"
            "  :root { --pt-magma: #123456; }\n}\n\n:root {",
            1,
        ),
        "cannot parse declaration",
    ),
    (
        "a declaration with no semicolon carrying an unknown token",
        lambda css: css.replace(
            "  --pt-info: #1B6FA8;", "  --pt-info: #1B6FA8;\n  --pt-rogue: #ABCDEF"
        ),
        "'--pt-rogue', which is not a token",
    ),
    (
        "a comment marker written inside a quoted value",
        lambda css: css.replace(
            "  --pt-positive: #2E8B57;",
            '  --pt-decoy: "x/*y"; --pt-positive: #2E8B57; */',
        ),
        "cannot parse declaration",
    ),
    (
        "a brace written inside a quoted value",
        lambda css: css.replace(
            "  --pt-positive: #2E8B57;", '  --pt-weird: "}"; --pt-positive: #2E8B57;'
        ),
        "not a token in tokens.css",
    ),
    (
        "a light re-declaration of a token :root never declares",
        lambda css: css.replace(
            "--pt-dom-stellar: #C8860F;",
            "--pt-dom-stellar: #C8860F;\n  --pt-text-d: #E9EEF2;",
        ),
        "never declared in :root",
    ),
    (
        "a light re-declaration with no counterpart named in LIGHT_PAIRS",
        lambda css: css.replace(
            "--pt-dom-stellar: #C8860F;",
            "--pt-dom-stellar: #C8860F;\n  --pt-dom-chem: #1B6FA8;",
        ),
        "add it to LIGHT_PAIRS",
    ),
    (
        "the light block written above the palette",
        None,
        "written before :root",
    ),
]


def move_light_block_first(css):
    """Return the stylesheet with the light scheme block moved above ``:root``.

    Parameters
    ----------
    css : str
        Text of the stylesheet.

    Returns
    -------
    str
        The same declarations with the ``default`` scheme block relocated
        ahead of the base palette, which reverses which one wins in a browser.
    """
    match = re.search(r'\[data-md-color-scheme="default"\]\s*\{', css)
    end = css.index("}", match.end()) + 1
    block = css[match.start() : end]
    return (css[: match.start()] + css[end:]).replace(":root {", block + "\n\n:root {", 1)


def run_case(edit):
    """Apply one edit in a scratch copy of the repo and run the check there.

    Parameters
    ----------
    edit : callable
        Takes the stylesheet text and returns the text to test.

    Returns
    -------
    tuple of (int, str)
        Exit code of ``check_copies.py --only extra-css`` and its combined
        output.
    """
    with tempfile.TemporaryDirectory() as scratch:
        root = Path(scratch)
        shutil.copytree(REPO / "tokens", root / "tokens")
        (root / "templates" / "docs").mkdir(parents=True)
        target = root / STYLESHEET
        target.write_text(edit((REPO / STYLESHEET).read_text(encoding="utf-8")), encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(root / "tokens" / "check_copies.py"), "--only", "extra-css"],
            capture_output=True,
            text=True,
        )
        return result.returncode, result.stdout + result.stderr


def main():
    """Run every case and report the ones that did not behave as pinned.

    Returns
    -------
    int
        ``0`` when every case behaves as pinned, ``1`` otherwise.
    """
    failures = []
    for name, edit in ACCEPTED:
        code, output = run_case(edit)
        if code != 0:
            failures.append(f"accepted case refused: {name}\n    {output.strip()[:200]}")
    for name, edit, fragment in REFUSED:
        code, output = run_case(move_light_block_first if edit is None else edit)
        if code == 0:
            failures.append(f"refused case accepted: {name}")
        elif fragment not in output:
            failures.append(
                f"refused case gave the wrong reason: {name}\n"
                f"    expected {fragment!r} in: {output.strip()[:200]}"
            )
    total = len(ACCEPTED) + len(REFUSED)
    if failures:
        for failure in failures:
            print(failure)
        print(f"{len(failures)} of {total} cases did not behave as pinned")
        return 1
    print(f"the docs drop-in reader behaves as pinned ({total} cases)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
