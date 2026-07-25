#!/usr/bin/env python3
"""Confirm ``check_cvd.py`` catches the ways a palette can go wrong.

``check_cvd.py`` reads its colours out of ``tokens.css`` by hand, so most of
what it can get wrong is a parsing question rather than an arithmetic one: a
declaration written in a form it cannot read, a value that looks like the
shipped one but is reached only under a condition, a domain that quietly
disappears. A check that silently measures four colours instead of seven will
report a wider minimum and pass, which is the failure that matters, because it
looks exactly like success.

Each case here writes a mutated ``tokens.css`` into a temporary copy of the
``tokens/`` directory and records whether ``check_cvd.py`` still exits zero.
The control cases must survive: they are valid CSS the check has to keep
reading. Every other case must be caught. Nothing in the working tree is
touched.

Run without arguments; the exit code is non-zero when any case behaves
differently from what it claims. Standard library only, like the checks it
covers.
"""

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TOKENS_DIR = REPO / "tokens"
ORIGINAL = (TOKENS_DIR / "tokens.css").read_text(encoding="utf-8")

# Anchors pulled from the committed file rather than hard-coded, so a future
# recolour does not silently turn a mutation into a no-op.
ACCRETION = re.search(r"--pt-dom-accretion\s*:\s*#[0-9A-Fa-f]{6}\s*;", ORIGINAL).group(0)
ATMOS = re.search(r"--pt-dom-atmos\s*:\s*#[0-9A-Fa-f]{6}\s*;", ORIGINAL).group(0)
INTERIOR = re.search(r"--pt-dom-interior\s*:\s*(#[0-9A-Fa-f]{6})", ORIGINAL).group(1)
VERDANT = re.search(r"--pt-verdant\s*:\s*#[0-9A-Fa-f]{6}\s*;", ORIGINAL).group(0)


def light_block(css, selector=None, stellar=None):
    """Rewrite the light-theme rule's selector, its stellar line, or both.

    Parameters
    ----------
    css : str
        Text of ``tokens.css`` to mutate.
    selector : str, optional
        Replacement for the ``[data-theme="light"]`` selector.
    stellar : str, optional
        Replacement for the deepened-stellar declaration inside that block.

    Returns
    -------
    str
        The mutated text.
    """
    if selector is not None:
        css = css.replace('[data-theme="light"] {', selector + " {", 1)
    if stellar is not None:
        css = re.sub(r"--pt-dom-stellar\s*:\s*#C8860F\s*;", stellar, css, count=1)
    return css


def replace(old, new):
    """Build a mutation that swaps one exact declaration for another.

    Parameters
    ----------
    old : str
        Declaration text that must be present in ``tokens.css``.
    new : str
        What to put in its place.

    Returns
    -------
    callable
        A function taking the CSS text and returning the mutated text.
    """

    def mutate(css):
        assert old in css, f"anchor no longer present in tokens.css: {old!r}"
        return css.replace(old, new, 1)

    return mutate


CASES = [
    # Valid CSS the check has to keep reading.
    ("unmutated palette", "pass", lambda c: c),
    (
        "compound light-theme descendant rule stays out of the light set",
        "pass",
        lambda c: c + '\n[data-theme="light"] .hero { --pt-dom-atmos: %s; }\n' % INTERIOR,
    ),
    (
        "light block written as a selector list keeps its override",
        "pass",
        lambda c: light_block(c, selector='[data-theme="light"], .pt-light'),
    ),
    (
        "last declaration in a block without a trailing semicolon",
        "pass",
        lambda c: light_block(c, stellar="--pt-dom-stellar: #C8860F"),
    ),
    # A conditional or layered value must not stand in for the shipped one.
    (
        "shipped value replaced, good value left inside a media query",
        "fail",
        lambda c: replace(ATMOS, "--pt-dom-atmos: %s;" % INTERIOR)(c)
        + "\n@media print { :root { %s } }\n" % ATMOS,
    ),
    (
        "shipped value replaced, good value left inside a cascade layer",
        "fail",
        lambda c: replace(ATMOS, "--pt-dom-atmos: %s;" % INTERIOR)(c)
        + "\n@layer tokens { :root { %s } }\n" % ATMOS,
    ),
    # Forms the check cannot measure must fail rather than be skipped.
    (
        "domain behind a var() reference",
        "fail",
        replace(ACCRETION, "--pt-dom-accretion: var(--pt-mantle);"),
    ),
    (
        "light override behind a var() reference",
        "fail",
        lambda c: light_block(c, stellar="--pt-dom-stellar: var(--pt-solar-deep);"),
    ),
    (
        "light override as a three-digit hex",
        "fail",
        lambda c: light_block(c, stellar="--pt-dom-stellar: #C86;"),
    ),
    # The roster is held on both blocks and across the rest of the palette.
    (
        "domain commented out of the dark set",
        "fail",
        replace(ACCRETION, "/* %s */" % ACCRETION),
    ),
    (
        "stray domain declared in the light block",
        "fail",
        lambda c: light_block(
            c, stellar="--pt-dom-stellar: #C8860F; --pt-dom-nonsense: #123456;"
        ),
    ),
    (
        "light override lost by aliasing the theme rule onto a class",
        "fail",
        lambda c: light_block(c, selector=".pt-light"),
    ),
    (
        "cross-palette colour removed",
        "fail",
        replace(VERDANT, "/* %s */" % VERDANT),
    ),
    # Within a block the last declaration wins, so the check has to read it.
    (
        "readable value shadowed by a later var()",
        "fail",
        replace(ATMOS, ATMOS + " --pt-dom-atmos: var(--pt-magma);"),
    ),
    (
        "readable value shadowed by a later colliding hex",
        "fail",
        replace(ATMOS, ATMOS + " --pt-dom-atmos: %s;" % INTERIOR),
    ),
    (
        "light override shadowed by a later var()",
        "fail",
        lambda c: light_block(
            c, stellar="--pt-dom-stellar: #C8860F; --pt-dom-stellar: var(--pt-solar);"
        ),
    ),
    # A bare & block applies unconditionally, so it cannot be skipped.
    (
        "nested rule inside the dark block overrides a domain",
        "fail",
        replace(ATMOS, ATMOS + " & { --pt-dom-atmos: %s; }" % INTERIOR),
    ),
    # A selector list is one of the blocks, whichever end :root sits at.
    (
        "collision appended via a selector list led by :root",
        "fail",
        lambda c: c + "\n:root, html { --pt-dom-atmos: %s; }\n" % INTERIOR,
    ),
    (
        "collision appended via a selector list ending in :root",
        "fail",
        lambda c: c + "\nhtml, :root { --pt-dom-atmos: %s; }\n" % INTERIOR,
    ),
    # The floors themselves, on each surface set.
    (
        "accretion moved onto a rejected candidate",
        "fail",
        replace(ACCRETION, "--pt-dom-accretion: #4F7A3A;"),
    ),
    (
        "collision that exists only on the light set",
        "fail",
        lambda c: light_block(c, stellar="--pt-dom-stellar: #D6432C;"),
    ),
]


def run_case(mutate):
    """Run ``check_cvd.py`` against one mutated copy of the tokens directory.

    Parameters
    ----------
    mutate : callable
        Takes the committed CSS text and returns the text to test.

    Returns
    -------
    caught : bool
        True when the check exited non-zero.
    detail : str
        Last non-empty line of its output, for the report.
    """
    with tempfile.TemporaryDirectory() as tmp:
        # check_cvd.py resolves tokens.css as <repo>/tokens/tokens.css relative
        # to its own location, so the copy has to keep that layout.
        copied = Path(tmp) / "tokens"
        shutil.copytree(TOKENS_DIR, copied)
        (copied / "tokens.css").write_text(mutate(ORIGINAL), encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, str(copied / "check_cvd.py")],
            capture_output=True,
            text=True,
        )
    lines = [ln for ln in (proc.stdout + proc.stderr).splitlines() if ln.strip()]
    return proc.returncode != 0, lines[-1] if lines else ""


def main():
    """Run every case and report the ones that behaved unexpectedly.

    Returns
    -------
    int
        ``0`` when every case behaved as it claims, ``1`` otherwise.
    """
    width = max(len(name) for name, _, _ in CASES)
    wrong = []
    for name, expect, mutate in CASES:
        caught, detail = run_case(mutate)
        as_claimed = caught == (expect == "fail")
        print(
            "%-*s  %-4s  %-5s  %s"
            % (width, name, expect, "ok" if as_claimed else "WRONG",
               detail[:78] if caught else "")
        )
        if not as_claimed:
            wrong.append(name)
    print()
    if wrong:
        print("%d case(s) behaved unexpectedly:" % len(wrong))
        for name in wrong:
            print("  -", name)
        return 1
    print("all %d cases behaved as claimed" % len(CASES))
    return 0


if __name__ == "__main__":
    sys.exit(main())
