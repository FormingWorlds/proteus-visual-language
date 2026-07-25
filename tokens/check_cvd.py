#!/usr/bin/env python3
"""Verify the module domain colours stay separable under colour blindness.

The domain colours are the one place in the palette where colour carries
meaning on its own: a reader identifies a module by its colour across the
website, the docs badges, and every paper figure. They therefore have to stay
apart from each other for readers with anomalous colour vision, not merely for
trichromats.

The check simulates full-severity protanopia, deuteranopia, and tritanopia with
the Machado, Oliveira & Fernandes (2009) matrices, applied in linear RGB, and
measures every pair with the CIE76 colour difference (``dE*ab``) in CIE Lab
under a D65 white point. Naming the metric matters: CIEDE2000 returns
substantially smaller numbers for the same pairs, so a figure quoted without
its formula cannot be reproduced.

Two sets are measured, because the light theme redefines one domain. The dark
set is the ``:root`` block of ``tokens.css``; the light set is that block with
the ``[data-theme="light"]`` overrides applied, which deepens stellar to
``#C8860F``.

The floors apply within the domain set alone. A second section measures the
domain colours against the palette colours that carry their own meaning
(``--pt-verdant``, the semantic colours, the deep and light ends of the phase
ramp) and prints the tightest pairs without enforcing anything. Those colours
are drawn from the same red-to-blue axis, so several land close under one
dichromacy; the report exists so the closeness is a known quantity when a
figure mixes module identity with status or ramp colour, and so a future domain
colour is chosen against the whole palette rather than against six of its
members.

``REJECTED`` records candidate hues that were measured and turned down, with
the hex each figure belongs to, so the reasons stay reproducible instead of
resting on recollection. Each is reported against the six domains that predate
the accretion slot and against the cross-palette set, which is what separates a
candidate that fails outright from one that clears the domains and collides
elsewhere. It is reporting only and never fails the check.

Run without arguments to measure the committed tokens; the exit code is
non-zero when a pair falls below the floor for its set. Pass ``--verbose`` to
print every pair rather than the tightest few. Paths resolve relative to this
file. Standard library only, so it runs anywhere ``tokens.css`` does.
"""

import itertools
import math
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TOKENS_CSS = REPO / "tokens" / "tokens.css"

# Floors are regression thresholds, set just under the measured minimum of the
# committed palette, not aspirational targets. The dark set clears the >= 12
# guidance in docs/figure-conventions.md with room to spare. The light set does
# not: deepening stellar for contrast on paper moves it toward interior, and
# that pair is the tightest in the palette under deuteranopia. Raising the light
# floor to 12 means recolouring stellar or interior, which would change module
# identity across the whole ecosystem, so the shortfall is recorded here and in
# docs/module-colors.md rather than papered over.
FLOOR_DARK = 16.0
FLOOR_LIGHT = 11.0

# The domains the check expects to find. Without this the measurement shrinks
# silently: a palette missing a colour has fewer pairs to compare, so its
# minimum rises and the floor still clears. Anything that stops a declaration
# from parsing (a removed line, a name change, a value moved behind var(), a
# three-digit hex) then reads as a pass. Adding a domain means adding it here
# too, which is the point: a new module colour has to be measured against the
# set before it ships.
EXPECTED_DOMAINS = frozenset(
    {
        "interior",
        "outgassing",
        "tidal",
        "chem",
        "atmos",
        "stellar",
        "accretion",
    }
)

# Machado, Oliveira & Fernandes (2009), "A Physiologically-based Model for
# Simulation of Color Vision Deficiency", IEEE TVCG 15(6), severity 1.0.
# Applied to linear-light RGB, not gamma-encoded sRGB.
CVD_MATRICES = {
    "protanopia": (
        (0.152286, 1.052583, -0.204868),
        (0.114503, 0.786281, 0.099216),
        (-0.003882, -0.048116, 1.051998),
    ),
    "deuteranopia": (
        (0.367322, 0.860646, -0.227968),
        (0.280085, 0.672501, 0.047413),
        (-0.011820, 0.042940, 0.968881),
    ),
    "tritanopia": (
        (1.255528, -0.076749, -0.178779),
        (-0.078411, 0.930809, 0.147602),
        (0.004733, 0.691367, 0.303900),
    ),
}

# sRGB (D65) to CIE XYZ.
RGB_TO_XYZ = (
    (0.4124564, 0.3575761, 0.1804375),
    (0.2126729, 0.7151522, 0.0721750),
    (0.0193339, 0.1191920, 0.9503041),
)
D65 = (0.95047, 1.0, 1.08883)

# Hues considered for the accretion slot and turned down, each with the hex the
# figure was measured on. Most land below the dark-set floor: the palette runs a
# dense red-to-blue ramp, so a saturated warm or green candidate collapses onto
# interior or outgassing under protanopia or deuteranopia, and a teal collapses
# onto chemistry under tritanopia. The olive-green is the exception and the
# reason this list is reported against two sets: it clears the six domains
# comfortably and then lands on top of --pt-verdant under deuteranopia, which a
# domain-only check cannot see.
REJECTED = {
    "burnt sienna": "#96552E",
    "ochre brown": "#8C6A3F",
    "umber": "#7A5C3A",
    "olive": "#6E8F2E",
    "moss green": "#3F7A2E",
    "sage": "#4F7A3A",
    "teal": "#2F7D74",
    "olive-green": "#7A9966",
    "verdant (the brand green)": "#57A05C",
}

# Palette colours outside the domain set that carry a meaning of their own and
# can therefore share a figure or a legend with module data. Named rather than
# swept from the whole file: surfaces, text, and hairlines are a contrast
# question, not a confusion one. A name whose hex equals a domain colour is
# skipped at run time, because the domain colours are drawn from the brand core
# deliberately; --pt-magma and --pt-dom-interior being one hex is identity.
CROSS_PALETTE = (
    "magma",
    "mantle",
    "crimson",
    "ocean",
    "abyss",
    "azure",
    "ice",
    "solar",
    "solar-deep",
    "verdant",
    "positive",
    "warning",
    "danger",
    "info",
)


def parse_domain_colours(css):
    """Extract the dark and light domain palettes from ``tokens.css``.

    Parameters
    ----------
    css : str
        Full text of ``tokens.css``.

    Returns
    -------
    dark : dict of str to str
        Domain name to hex, from the ``:root`` block.
    light : dict of str to str
        The same, with the ``[data-theme="light"]`` overrides applied.

    Raises
    ------
    ValueError
        If the ``:root`` block does not declare exactly ``EXPECTED_DOMAINS``, if
        the light block declares a domain outside that set, or if either block
        writes a domain colour in a form the hex reader cannot measure.
    """
    css = _strip_comments(css)
    dark = _domains_in_block(css, ":root")
    _reject_unreadable(css, ":root", dark)
    if set(dark) != EXPECTED_DOMAINS:
        missing = sorted(EXPECTED_DOMAINS - set(dark))
        extra = sorted(set(dark) - EXPECTED_DOMAINS)
        detail = []
        if missing:
            detail.append(f"missing {', '.join(missing)}")
        if extra:
            detail.append(f"unexpected {', '.join(extra)}")
        raise ValueError(
            "the :root block does not declare the expected domain colours: "
            + "; ".join(detail)
        )
    overrides = _domains_in_block(css, '[data-theme="light"]')
    _reject_unreadable(css, '[data-theme="light"]', overrides)
    stray = sorted(set(overrides) - EXPECTED_DOMAINS)
    if stray:
        raise ValueError(
            'the [data-theme="light"] block declares domain colours outside the '
            "expected set: " + ", ".join(stray)
        )
    light = dict(dark)
    light.update(overrides)
    return dark, light


def _reject_unreadable(css, selector, readable):
    """Fail on a ``--pt-dom-*`` declaration the hex reader had to skip.

    A domain written as a ``var()`` reference, a three-digit hex, or a colour
    function is a live value on the page but invisible to this check. Skipping
    it silently is the worst outcome: on the light block the dark value fills
    the gap, so the run measures a palette nobody ships and reports it as
    passing.

    Parameters
    ----------
    css : str
        Comment-stripped text of ``tokens.css``.
    selector : str
        The block to inspect.
    readable : dict of str to str
        The domains the hex reader recovered from that block.

    Raises
    ------
    ValueError
        If the block declares a domain the hex reader did not recover.
    """
    declared = set()
    for block in _top_level_bodies(css, selector):
        declared.update(re.findall(r"--pt-dom-([a-z-]+)\s*:", block))
    skipped = sorted(declared - set(readable))
    if skipped:
        raise ValueError(
            f"the {selector} block writes "
            + ", ".join("--pt-dom-" + name for name in skipped)
            + " in a form this check cannot measure; use a six-digit hex literal"
        )


def _strip_comments(css):
    """Return the CSS with ``/* ... */`` comments removed.

    A commented-out declaration is not in the cascade, so it must not be
    measured; without this a disabled domain colour still parses and reports
    as live.

    Parameters
    ----------
    css : str
        Full text of ``tokens.css``.

    Returns
    -------
    str
        The same text with every comment replaced by a single space, so a
        comment between two declarations cannot join them.
    """
    return re.sub(r"/\*.*?\*/", " ", css, flags=re.S)


def _top_level_bodies(css, selector):
    """Return the body of every top-level block whose selector matches exactly.

    Walks the text with a brace counter rather than a regex, for two reasons.
    A rule nested inside ``@media``, ``@supports``, ``@layer`` or ``@container``
    carries the same selector text as the unconditional one, and a conditional
    value must never stand in for the value the palette actually ships. And an
    exact selector match keeps a compound rule such as
    ``[data-theme="light"] .hero`` out of the theme block.

    Declarations nested one level deeper are dropped for the same reason, so a
    block written with CSS nesting contributes only its own cascade.

    Parameters
    ----------
    css : str
        Comment-stripped text of ``tokens.css``.
    selector : str
        The exact selector text preceding the opening brace.

    Returns
    -------
    list of str
        One string per matching block, holding that block's own declarations.
    """
    bodies = []
    depth = 0
    prelude_start = 0
    matched = False
    segments = []
    segment_start = 0
    quote = None
    index = 0
    while index < len(css):
        char = css[index]
        if quote is not None:
            if char == "\\":
                index += 2
                continue
            if char == quote:
                quote = None
        elif char in ('"', "'"):
            quote = char
        elif char == "{":
            depth += 1
            if depth == 1:
                matched = css[prelude_start:index].strip() == selector
                segments = []
                segment_start = index + 1
            elif depth == 2 and matched:
                segments.append(css[segment_start:index])
        elif char == "}":
            if depth >= 2:
                depth -= 1
                if depth == 1 and matched:
                    segment_start = index + 1
            else:
                if depth == 1 and matched:
                    segments.append(css[segment_start:index])
                    bodies.append(" ".join(segments))
                matched = False
                depth = 0
                prelude_start = index + 1
        elif char == ";" and depth == 0:
            prelude_start = index + 1
        index += 1
    return bodies


def _domains_in_block(css, selector):
    """Return the ``--pt-dom-*`` declarations inside one top-level block.

    Parameters
    ----------
    css : str
        Comment-stripped text of ``tokens.css``.
    selector : str
        The exact selector text preceding the opening brace.

    Returns
    -------
    dict of str to str
        Domain name (the part after ``--pt-dom-``) to lower-cased hex.
    """
    found = {}
    for block in _top_level_bodies(css, selector):
        for name, hex_value in re.findall(
            r"--pt-dom-([a-z-]+)\s*:\s*(#[0-9A-Fa-f]{6})\s*;", block
        ):
            found[name] = hex_value.lower()
    return found


def parse_named_colours(css, names):
    """Extract specific ``--pt-*`` colour tokens from the ``:root`` block.

    Parameters
    ----------
    css : str
        Full text of ``tokens.css``.
    names : iterable of str
        Token names without the ``--pt-`` prefix, for example ``verdant``.

    Returns
    -------
    dict of str to str
        Name to lower-cased hex, in the order requested, omitting any name the
        block does not declare.
    """
    css = _strip_comments(css)
    declared = {}
    for block in _top_level_bodies(css, ":root"):
        declared.update(
            re.findall(r"--pt-([a-z0-9-]+)\s*:\s*(#[0-9A-Fa-f]{6})\s*;", block)
        )
    return {n: declared[n].lower() for n in names if n in declared}


def hex_to_rgb(value):
    """Convert ``#rrggbb`` to a 0-1 sRGB triple."""
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) / 255 for i in (0, 2, 4))


def srgb_to_linear(channel):
    """Undo the sRGB transfer function for one 0-1 channel."""
    if channel <= 0.04045:
        return channel / 12.92
    return ((channel + 0.055) / 1.055) ** 2.4


def linear_to_srgb(channel):
    """Apply the sRGB transfer function to one channel, clamped to 0-1."""
    channel = min(1.0, max(0.0, channel))
    if channel <= 0.0031308:
        return 12.92 * channel
    return 1.055 * channel ** (1 / 2.4) - 0.055


def simulate(matrix, rgb):
    """Simulate one dichromacy on an sRGB triple.

    Parameters
    ----------
    matrix : tuple of tuple of float
        A 3x3 Machado matrix at severity 1.0.
    rgb : tuple of float
        Gamma-encoded sRGB in 0-1.

    Returns
    -------
    tuple of float
        The simulated colour, gamma-encoded sRGB in 0-1.
    """
    linear = [srgb_to_linear(c) for c in rgb]
    out = [sum(matrix[i][j] * linear[j] for j in range(3)) for i in range(3)]
    return tuple(linear_to_srgb(c) for c in out)


def rgb_to_lab(rgb):
    """Convert a 0-1 sRGB triple to CIE Lab under D65."""
    linear = [srgb_to_linear(c) for c in rgb]
    xyz = [sum(RGB_TO_XYZ[i][j] * linear[j] for j in range(3)) for i in range(3)]

    def f(t):
        if t > 216 / 24389:
            return t ** (1 / 3)
        return (841 / 108) * t + 4 / 29

    fx, fy, fz = (f(c / w) for c, w in zip(xyz, D65))
    return (116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz))


def delta_e76(rgb_a, rgb_b):
    """CIE76 colour difference between two 0-1 sRGB triples."""
    lab_a, lab_b = rgb_to_lab(rgb_a), rgb_to_lab(rgb_b)
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(lab_a, lab_b)))


def pair_distances(palette):
    """Measure every domain pair under every dichromacy.

    Parameters
    ----------
    palette : dict of str to str
        Domain name to hex.

    Returns
    -------
    list of tuple
        ``(distance, name_a, name_b, dichromacy)``, ascending by distance.
    """
    rgb = {name: hex_to_rgb(value) for name, value in palette.items()}
    rows = []
    for a, b in itertools.combinations(sorted(rgb), 2):
        for label, matrix in CVD_MATRICES.items():
            rows.append(
                (
                    delta_e76(simulate(matrix, rgb[a]), simulate(matrix, rgb[b])),
                    a,
                    b,
                    label,
                )
            )
    rows.sort()
    return rows


def closest_in(value, palette):
    """Return the tightest pairing of one hex against a palette it need not join.

    Parameters
    ----------
    value : str
        The hex to measure.
    palette : dict of str to str
        Name to hex. Must not be empty.

    Returns
    -------
    tuple
        ``(distance, name, dichromacy)`` for the tightest pairing.

    Raises
    ------
    ValueError
        If ``palette`` is empty, which has no tightest pairing to return.
    """
    if not palette:
        raise ValueError("closest_in needs a non-empty palette")
    rgb = hex_to_rgb(value)
    best = None
    for name, other in palette.items():
        other_rgb = hex_to_rgb(other)
        for label, matrix in CVD_MATRICES.items():
            distance = delta_e76(simulate(matrix, rgb), simulate(matrix, other_rgb))
            if best is None or distance < best[0]:
                best = (distance, name, label)
    return best


def cross_palette_pairs(domains, others):
    """Measure each domain colour against every other named palette colour.

    Colours whose hex matches a domain colour exactly are dropped: those are
    deliberate aliases, not collisions.

    Parameters
    ----------
    domains : dict of str to str
        Domain name to hex.
    others : dict of str to str
        Palette colour name to hex.

    Returns
    -------
    list of tuple
        ``(distance, other_name, domain_name, dichromacy)``, ascending.
    """
    domain_hexes = {value.lower() for value in domains.values()}
    rows = []
    for name, value in others.items():
        if value.lower() in domain_hexes:
            continue
        rgb = hex_to_rgb(value)
        for domain, domain_hex in domains.items():
            domain_rgb = hex_to_rgb(domain_hex)
            for label, matrix in CVD_MATRICES.items():
                rows.append(
                    (
                        delta_e76(simulate(matrix, rgb), simulate(matrix, domain_rgb)),
                        name,
                        domain,
                        label,
                    )
                )
    rows.sort()
    return rows


def report_cross(domains, others, verbose):
    """Print how close the domain colours run to the rest of the palette.

    Reporting only: no floor applies across sets, because several of these
    colours share a hue axis with the domains by design.

    Parameters
    ----------
    domains : dict of str to str
        Domain name to hex.
    others : dict of str to str
        Palette colour name to hex.
    verbose : bool
        Print every pair rather than the tightest eight.
    """
    print("domain colours against the rest of the palette (reported, not enforced)")
    if not others:
        print("    every named palette colour is a domain colour, nothing to compare")
        return
    rows = cross_palette_pairs(domains, others)
    shown = rows if verbose else rows[:8]
    for distance, other, domain, dichromacy in shown:
        print(f"    {distance:6.2f}  --pt-{other}/{domain} under {dichromacy}")
    if not verbose:
        print(f"    ... {len(rows) - len(shown)} wider pairs not shown")
    print("  tightest of these per domain")
    for domain in domains:
        distance, other, dichromacy = closest_in(domains[domain], others)
        print(f"    {distance:6.2f}  {domain} vs --pt-{other} under {dichromacy}")
    print(
        "  a figure that mixes module identity with status or ramp colour needs "
        "a legend, whatever the hues do"
    )


def report_set(label, palette, floor, verbose):
    """Print one palette's pair table and return whether it clears its floor.

    Parameters
    ----------
    label : str
        Human-readable name of the surface set.
    palette : dict of str to str
        Domain name to hex.
    floor : float
        Minimum acceptable CIE76 distance for this set.
    verbose : bool
        Print every pair rather than the tightest five.

    Returns
    -------
    bool
        ``True`` when every pair clears ``floor``.
    """
    rows = pair_distances(palette)
    shown = rows if verbose else rows[:5]
    print(f"{label} ({len(palette)} domains, floor {floor:.1f})")
    for distance, a, b, dichromacy in shown:
        print(f"    {distance:6.2f}  {a}/{b} under {dichromacy}")
    if not verbose:
        print(f"    ... {len(rows) - len(shown)} wider pairs not shown")
    worst = rows[0]
    if worst[0] < floor:
        print(
            f"  FAIL: {worst[1]}/{worst[2]} is {worst[0]:.2f} under "
            f"{worst[3]}, below the {floor:.1f} floor"
        )
        return False
    print(f"  minimum {worst[0]:.2f}, clears the {floor:.1f} floor")
    return True


def main(argv):
    """Measure the committed domain colours under all three dichromacies.

    Parameters
    ----------
    argv : list of str
        Command-line arguments; only ``--verbose`` is accepted.

    Returns
    -------
    int
        ``0`` when both surface sets clear their floor, ``1`` on a shortfall
        or a read error, ``2`` on misuse.
    """
    verbose = False
    for arg in argv[1:]:
        if arg in ("-v", "--verbose"):
            verbose = True
        else:
            print("usage: check_cvd.py [--verbose]")
            return 2
    try:
        css = TOKENS_CSS.read_text(encoding="utf-8")
        dark, light = parse_domain_colours(css)
    except (OSError, ValueError) as exc:
        print(f"could not read the domain colours: {exc}")
        return 1
    # Drop any named colour that is a domain colour on either surface. Solar
    # deep is the light-surface stellar, so measuring it against dark stellar
    # would report a domain against itself.
    # Two names can also share one hex: --pt-danger repeats --pt-crimson. That
    # is one colour on the page, so measuring both would print each pair twice
    # and crowd out a genuinely tight pair in the listing. Keep whichever name
    # comes first in CROSS_PALETTE.
    domain_hexes = {v.lower() for v in dark.values()}
    domain_hexes |= {v.lower() for v in light.values()}
    others = {}
    seen = set(domain_hexes)
    for name, value in parse_named_colours(css, CROSS_PALETTE).items():
        if value.lower() in seen:
            continue
        seen.add(value.lower())
        others[name] = value

    print("CIE76 dE*ab on Machado 2009 full-severity simulations, linear RGB\n")
    ok_dark = report_set("dark surface", dark, FLOOR_DARK, verbose)
    print()
    ok_light = report_set("light surface", light, FLOOR_LIGHT, verbose)
    print()
    report_cross(dark, others, verbose)

    # Candidates competed for the accretion slot, so they are measured against
    # the six domains that predate it, not against the colour that won. The
    # second column is the test a domain-only check misses: a candidate can
    # clear all six and still land on a palette colour it will share a legend
    # with.
    incumbents = {k: v for k, v in dark.items() if k != "accretion"}
    print("\nrejected candidates for the accretion slot")
    print("    vs the other six domains        vs the rest of the palette")
    for name, value in REJECTED.items():
        near, other, dichromacy = closest_in(value, incumbents)
        # A candidate that is itself a palette colour would otherwise be
        # measured against itself and report a flattering zero.
        rest = {k: v for k, v in others.items() if v.lower() != value.lower()}
        if rest:
            distance, other_name, other_dichromacy = closest_in(value, rest)
            cross = f"{distance:6.2f} --pt-{other_name:<10} {other_dichromacy[:6]}"
        else:
            cross = "     no palette colour to compare  "
        print(
            f"    {near:6.2f} {other:<10} {dichromacy[:6]}    {cross}    {name} {value}"
        )

    if not (ok_dark and ok_light):
        print(
            "\ndomain colours fall below their floor; pick a replacement by "
            "maximising the minimum pairwise distance across all three "
            "dichromacies, on both surface sets"
        )
        return 1
    print("\ndomain colours stay separable under all three dichromacies")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
