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

``REJECTED`` records candidate hues that were measured and turned down, with
the hex each figure belongs to, so the reasons stay reproducible instead of
resting on recollection. It is reporting only and never fails the check.

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
# figure was measured on. Every one lands below the dark-set floor, which is why
# the slot went to a low-chroma warm neutral: the palette already runs a dense
# red-to-blue ramp, so a saturated warm or green candidate collapses onto
# interior or outgassing under protanopia or deuteranopia, and a teal collapses
# onto chemistry under tritanopia.
REJECTED = {
    "burnt sienna": "#96552E",
    "ochre brown": "#8C6A3F",
    "umber": "#7A5C3A",
    "olive": "#6E8F2E",
    "moss green": "#3F7A2E",
    "sage": "#4F7A3A",
    "teal": "#2F7D74",
    "verdant (the brand green)": "#57A05C",
}


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
        If the ``:root`` block is missing or declares no domain tokens.
    """
    dark = _domains_in_block(css, ":root")
    if not dark:
        raise ValueError("no --pt-dom-* tokens found in the :root block")
    light = dict(dark)
    light.update(_domains_in_block(css, '[data-theme="light"]'))
    return dark, light


def _domains_in_block(css, selector):
    """Return the ``--pt-dom-*`` declarations inside one top-level block.

    Matches the selector exactly, so a compound rule such as
    ``[data-theme="light"] .hero`` is not mistaken for the theme block.

    Parameters
    ----------
    css : str
        Full text of ``tokens.css``.
    selector : str
        The exact selector text preceding the opening brace.

    Returns
    -------
    dict of str to str
        Domain name (the part after ``--pt-dom-``) to lower-cased hex.
    """
    pattern = re.compile(
        r"(?:^|\})\s*" + re.escape(selector) + r"\s*\{(.*?)\}", re.S | re.M
    )
    found = {}
    for block in pattern.findall(css):
        for name, hex_value in re.findall(
            r"--pt-dom-([a-z-]+)\s*:\s*(#[0-9A-Fa-f]{6})\s*;", block
        ):
            found[name] = hex_value.lower()
    return found


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


def nearest_neighbour(palette, name):
    """Return the tightest pairing of one colour against the rest of a palette.

    Parameters
    ----------
    palette : dict of str to str
        Domain name to hex; must contain ``name``.
    name : str
        The colour to measure against every other entry.

    Returns
    -------
    tuple
        ``(distance, other_name, dichromacy)`` for the tightest pairing.
    """
    rows = [r for r in pair_distances(palette) if name in (r[1], r[2])]
    distance, a, b, label = rows[0]
    return distance, (b if a == name else a), label


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
        dark, light = parse_domain_colours(TOKENS_CSS.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"could not read the domain colours: {exc}")
        return 1

    print("CIE76 dE*ab on Machado 2009 full-severity simulations, linear RGB\n")
    ok_dark = report_set("dark surface", dark, FLOOR_DARK, verbose)
    print()
    ok_light = report_set("light surface", light, FLOOR_LIGHT, verbose)

    # Candidates competed for the accretion slot, so they are measured against
    # the six domains that predate it, not against the colour that won.
    incumbents = {k: v for k, v in dark.items() if k != "accretion"}
    print("\nrejected candidates for the accretion slot, against the other six")
    for name, value in REJECTED.items():
        trial = dict(incumbents)
        trial["candidate"] = value
        distance, other, dichromacy = nearest_neighbour(trial, "candidate")
        print(
            f"    {distance:6.2f}  {name} {value} vs {other} under {dichromacy}"
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
