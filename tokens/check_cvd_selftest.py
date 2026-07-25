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
``tokens/`` directory and records what ``check_cvd.py`` did with it. Two things
are asserted, not one: whether the check failed, and whether its output says why.
A case that fails for the wrong reason is as much a gap as one that does not
fail at all, because the guard the case is named for can then be deleted with
the case still reporting green.

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

LIGHT_SELECTOR = '[data-theme="light"]'

# Anchors pulled from the committed file rather than hard-coded, so a future
# recolour does not silently turn a mutation into a no-op. Each is required to
# appear exactly once, which is what makes a single-shot replace() well defined.
ACCRETION = re.search(r"--pt-dom-accretion\s*:\s*#[0-9A-Fa-f]{6}\s*;", ORIGINAL).group(0)
ATMOS = re.search(r"--pt-dom-atmos\s*:\s*#[0-9A-Fa-f]{6}\s*;", ORIGINAL).group(0)
INTERIOR = re.search(r"--pt-dom-interior\s*:\s*(#[0-9A-Fa-f]{6})", ORIGINAL).group(1)
VERDANT = re.search(r"--pt-verdant\s*:\s*#[0-9A-Fa-f]{6}\s*;", ORIGINAL).group(0)

# The light-theme rule, and the one domain override inside it.
LIGHT_OPENING = LIGHT_SELECTOR + " {"
LIGHT_RULE = re.search(re.escape(LIGHT_OPENING) + r"[^}]*\}", ORIGINAL, re.S).group(0)
LIGHT_STELLAR = re.search(
    r"--pt-dom-stellar\s*:\s*#[0-9A-Fa-f]{6}\s*;", LIGHT_RULE
).group(0)

for _anchor in (ACCRETION, ATMOS, VERDANT, LIGHT_OPENING, LIGHT_STELLAR):
    assert ORIGINAL.count(_anchor) == 1, f"anchor is not unique in tokens.css: {_anchor!r}"

# Probe colours for the atmosphere slot, each chosen to collide under one
# dichromacy and stay clear of the floor under the other two, so removing a
# single simulation matrix turns its case green. Their separations are measured
# against the committed palette; a recolour that makes one stop colliding turns
# the case green as well, which is the direction that gets noticed.
PROTAN_COLLISION = "#A75BA8"
DEUTER_COLLISION = "#8D3FA9"
TRITAN_COLLISION = "#9F104A"
# Breaches the dark floor at 11.70 while the light set holds its own minimum of
# 11.44, so this is the case the dark floor alone decides.
DARK_ONLY_COLLISION = "#DC415F"


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

    Raises
    ------
    AssertionError
        If either anchor is no longer present, which would leave the mutation a
        no-op and the case passing for no reason.
    """
    if selector is not None:
        assert LIGHT_OPENING in css, f"anchor no longer present: {LIGHT_OPENING!r}"
        css = css.replace(LIGHT_OPENING, selector + " {", 1)
    if stellar is not None:
        assert LIGHT_STELLAR in css, f"anchor no longer present: {LIGHT_STELLAR!r}"
        css = css.replace(LIGHT_STELLAR, stellar, 1)
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


def append(rule):
    """Build a mutation that adds one rule after the committed palette.

    Parameters
    ----------
    rule : str
        The rule text to append.

    Returns
    -------
    callable
        A function taking the CSS text and returning the mutated text.
    """
    return lambda css: css + "\n" + rule + "\n"


SEPARABLE = "domain colours stay separable"
# One measured pair per dichromacy, quoted exactly as the default report prints
# it. Everything else here tests what the check reads; these test what it
# computes, so a simulation matrix cannot be rewritten into a different colour
# space and still report the palette as sound. They are the same three figures
# the docs quote, so a recolour updates both together.
MEASURED = (
    SEPARABLE,
    "16.36  interior/outgassing under protanopia",
    "11.44  interior/stellar under deuteranopia",
    "15.69  atmos vs --pt-verdant under tritanopia",
)
BELOW_FLOOR = "fall below their floor"
UNREADABLE = "in a form this check cannot measure"
WRONG_ROSTER = "does not declare the expected domain colours"
NESTED = "contains a nested rule"
UNREAD_BLOCK = "in a block this check does not read"

# Each case is a name, the outcome it claims, what its output has to contain,
# and the mutation. That third field is one fragment or a tuple of them, all
# required, and it is what stops a case passing on an unrelated failure.
CASES = [
    # Valid CSS the check has to keep reading.
    ("unmutated palette", "pass", MEASURED, lambda c: c),
    (
        "compound light-theme descendant rule stays out of the light set",
        "pass",
        SEPARABLE,
        append('[data-theme="light"] .hero { --pt-dom-atmos: %s; }' % INTERIOR),
    ),
    (
        "domain retinted for a subtree below the root",
        "pass",
        SEPARABLE,
        append(":root > .panel { --pt-dom-atmos: %s; }" % INTERIOR),
    ),
    (
        "light block written as a selector list keeps its override",
        "pass",
        SEPARABLE,
        lambda c: light_block(c, selector=LIGHT_SELECTOR + ", .pt-light"),
    ),
    (
        "last declaration in a block without a trailing semicolon",
        "pass",
        SEPARABLE,
        lambda c: light_block(c, stellar=LIGHT_STELLAR.rstrip("; ")),
    ),
    (
        "theme selector written with single quotes",
        "pass",
        SEPARABLE,
        lambda c: c.replace(LIGHT_OPENING, "[data-theme='light'] {", 1),
    ),
    (
        "theme selector written without quotes",
        "pass",
        SEPARABLE,
        lambda c: c.replace(LIGHT_OPENING, "[data-theme=light] {", 1),
    ),
    (
        "byte-order mark ahead of the first rule",
        "pass",
        SEPARABLE,
        lambda c: "﻿" + c,
    ),
    (
        "shipped colour carrying a priority flag",
        "pass",
        SEPARABLE,
        replace(ATMOS, ATMOS.rstrip("; ") + " !important;"),
    ),
    (
        "closing brace inside a quoted value",
        "pass",
        SEPARABLE,
        replace(ATMOS, '--pt-brace: "}"; ' + ATMOS),
    ),
    (
        "braces inside a custom property value",
        "pass",
        SEPARABLE,
        replace(ATMOS, ATMOS + " --pt-block: { color: red };"),
    ),
    (
        "unquoted brace inside a url() on a plain property",
        "pass",
        SEPARABLE,
        replace(ATMOS, ATMOS + " background: url(a{b.png);"),
    ),
    # A conditional or layered value must not stand in for the shipped one.
    (
        "shipped value replaced, good value left inside a media query",
        "fail",
        BELOW_FLOOR,
        lambda c: replace(ATMOS, "--pt-dom-atmos: %s;" % INTERIOR)(c)
        + "\n@media print { :root { %s } }\n" % ATMOS,
    ),
    (
        "shipped value replaced, good value left inside a cascade layer",
        "fail",
        BELOW_FLOOR,
        lambda c: replace(ATMOS, "--pt-dom-atmos: %s;" % INTERIOR)(c)
        + "\n@layer tokens { :root { %s } }\n" % ATMOS,
    ),
    # Forms the check cannot measure must fail rather than be skipped.
    (
        "domain behind a var() reference",
        "fail",
        UNREADABLE,
        replace(ACCRETION, "--pt-dom-accretion: var(--pt-mantle);"),
    ),
    (
        "light override behind a var() reference",
        "fail",
        UNREADABLE,
        lambda c: light_block(c, stellar="--pt-dom-stellar: var(--pt-solar-deep);"),
    ),
    (
        "light override as a three-digit hex",
        "fail",
        UNREADABLE,
        lambda c: light_block(c, stellar="--pt-dom-stellar: #C86;"),
    ),
    (
        "unreadable domain alongside a complete dark roster",
        "fail",
        UNREADABLE,
        replace(ATMOS, ATMOS + " --pt-dom-crust: var(--pt-mantle);"),
    ),
    (
        "unreadable domain alongside the expected light override",
        "fail",
        UNREADABLE,
        lambda c: light_block(
            c, stellar=LIGHT_STELLAR + " --pt-dom-crust: var(--pt-mantle);"
        ),
    ),
    # The roster is held on both blocks and across the rest of the palette.
    (
        "domain commented out of the dark set",
        "fail",
        "missing accretion",
        replace(ACCRETION, "/* %s */" % ACCRETION),
    ),
    (
        "extra domain declared in the dark set",
        "fail",
        "unexpected crust",
        replace(ATMOS, ATMOS + " --pt-dom-crust: #123456;"),
    ),
    (
        "stray domain declared in the light block",
        "fail",
        "unexpected nonsense",
        lambda c: light_block(
            c, stellar=LIGHT_STELLAR + " --pt-dom-nonsense: #123456;"
        ),
    ),
    (
        "light override dropped from the light block",
        "fail",
        "missing stellar",
        lambda c: light_block(c, stellar=""),
    ),
    (
        "light block renamed to a class the check does not read",
        "fail",
        UNREAD_BLOCK,
        lambda c: light_block(c, selector=".pt-light"),
    ),
    (
        "light block removed outright",
        "fail",
        "no top-level %s block" % LIGHT_SELECTOR,
        lambda c: c.replace(LIGHT_RULE, "", 1),
    ),
    (
        "cross-palette colour removed",
        "fail",
        "does not declare a readable six-digit hex",
        replace(VERDANT, "/* %s */" % VERDANT),
    ),
    # Within a block the last declaration wins, so the check has to read it.
    (
        "readable value shadowed by a later var()",
        "fail",
        UNREADABLE,
        replace(ATMOS, ATMOS + " --pt-dom-atmos: var(--pt-magma);"),
    ),
    (
        "readable value shadowed by a later colliding hex",
        "fail",
        BELOW_FLOOR,
        replace(ATMOS, ATMOS + " --pt-dom-atmos: %s;" % INTERIOR),
    ),
    (
        "light override shadowed by a later var()",
        "fail",
        UNREADABLE,
        lambda c: light_block(
            c, stellar=LIGHT_STELLAR + " --pt-dom-stellar: var(--pt-solar);"
        ),
    ),
    # A bare & block applies unconditionally, so it cannot be skipped. The
    # nested rule here repeats the shipped colour: skipping it rather than
    # refusing it would leave the palette measuring clean and this case green.
    (
        "nested rule inside the dark block",
        "fail",
        NESTED,
        replace(ATMOS, ATMOS + " & { %s }" % ATMOS),
    ),
    # A selector list is one of the blocks, whichever end :root sits at.
    (
        "collision appended via a selector list led by :root",
        "fail",
        BELOW_FLOOR,
        append(":root, html { --pt-dom-atmos: %s; }" % INTERIOR),
    ),
    (
        "collision appended via a selector list ending in :root",
        "fail",
        BELOW_FLOOR,
        append("html, :root { --pt-dom-atmos: %s; }" % INTERIOR),
    ),
    # Selectors that reach the root at a higher specificity than :root decide
    # the shipped colour, so they cannot be left unread.
    (
        "domain overridden by a doubled root selector",
        "fail",
        UNREAD_BLOCK,
        append(":root:root { --pt-dom-atmos: %s; }" % INTERIOR),
    ),
    (
        "domain overridden by a qualified root selector",
        "fail",
        UNREAD_BLOCK,
        append("html:root { --pt-dom-atmos: %s; }" % INTERIOR),
    ),
    (
        "domain overridden on the html element",
        "fail",
        UNREAD_BLOCK,
        append("html { --pt-dom-atmos: %s; }" % INTERIOR),
    ),
    # A comment marker inside a string is content, so it must not blank out the
    # declarations that follow it.
    (
        "collision hidden behind comment markers in string values",
        "fail",
        BELOW_FLOOR,
        replace(
            ATMOS,
            '--pt-open: "/*"; --pt-dom-atmos: %s; --pt-close: "*/";' % INTERIOR,
        ),
    ),
    # The floors, on each surface set.
    (
        "accretion moved onto a rejected candidate",
        "fail",
        BELOW_FLOOR,
        replace(ACCRETION, "--pt-dom-accretion: #4F7A3A;"),
    ),
    (
        "collision that exists only on the light set",
        "fail",
        BELOW_FLOOR,
        lambda c: light_block(c, stellar="--pt-dom-stellar: #D6432C;"),
    ),
    (
        "collision that exists only on the dark set",
        "fail",
        BELOW_FLOOR,
        replace(ATMOS, "--pt-dom-atmos: %s;" % DARK_ONLY_COLLISION),
    ),
    # One case per dichromacy, each collapsing only under its own simulation.
    (
        "collision seen only under protanopia",
        "fail",
        BELOW_FLOOR,
        replace(ATMOS, "--pt-dom-atmos: %s;" % PROTAN_COLLISION),
    ),
    (
        "collision seen only under deuteranopia",
        "fail",
        BELOW_FLOOR,
        replace(ATMOS, "--pt-dom-atmos: %s;" % DEUTER_COLLISION),
    ),
    (
        "collision seen only under tritanopia",
        "fail",
        BELOW_FLOOR,
        replace(ATMOS, "--pt-dom-atmos: %s;" % TRITAN_COLLISION),
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
    output : str
        Everything it printed, on both streams.
    detail : str
        Last non-empty line of that output, for the report.
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
    output = proc.stdout + proc.stderr
    lines = [ln for ln in output.splitlines() if ln.strip()]
    return proc.returncode != 0, output, lines[-1] if lines else ""


def main():
    """Run every case and report the ones that behaved unexpectedly.

    Returns
    -------
    int
        ``0`` when every case behaved as it claims, ``1`` otherwise.
    """
    width = max(len(name) for name, _, _, _ in CASES)
    wrong = []
    for name, expect, fragment, mutate in CASES:
        wanted = (fragment,) if isinstance(fragment, str) else fragment
        caught, output, detail = run_case(mutate)
        missing = [text for text in wanted if text not in output]
        if caught != (expect == "fail"):
            verdict = "exit"
        elif missing:
            verdict = "reason"
            fragment = missing[0]
        else:
            verdict = ""
        print(
            "%-*s  %-4s  %-6s  %s"
            % (width, name, expect, verdict or "ok", detail[:78] if caught else "")
        )
        if verdict:
            wrong.append((name, verdict, fragment))
    print()
    if wrong:
        print("%d case(s) behaved unexpectedly:" % len(wrong))
        for name, verdict, fragment in wrong:
            reason = (
                "exited the wrong way"
                if verdict == "exit"
                else "did not report %r" % fragment
            )
            print("  - %s: %s" % (name, reason))
        return 1
    print("all %d cases behaved as claimed" % len(CASES))
    return 0


if __name__ == "__main__":
    sys.exit(main())
