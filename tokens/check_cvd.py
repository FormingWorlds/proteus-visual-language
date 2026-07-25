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
members. That roster is a required minimum rather than an exact set: every name
on it has to be readable, so a renamed or removed token stops the check rather
than shrinking the comparison in silence, while a colour added to the palette
joins the comparison once it is listed there.

``REJECTED`` records candidate hues that were measured and turned down, with
the hex each figure belongs to, so the reasons stay reproducible instead of
resting on recollection. Each is reported against the six domains that predate
the accretion slot and against the cross-palette set, which is what separates a
candidate that fails outright from one that clears the domains and collides
elsewhere. It is reporting only and never fails the check.

Run without arguments to measure the committed tokens; the exit code is
non-zero when a pair falls below the floor for its set, when either domain
roster is not the set expected or the cross-palette one is missing a colour,
when a colour is written in a form this check cannot read, and when a domain
colour reaches the root element from a block outside the two the palette is
declared in. Pass ``--verbose`` to print every pair
rather than the tightest few, which is what the default prints. Paths resolve
relative to this file. Standard library only, so it runs anywhere
``tokens.css`` does. ``check_cvd_selftest.py`` covers the reading rules with
mutated copies of the palette.
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

# Domains the light block is expected to override. Only Stellar deepens on a
# light surface; the rest carry their dark value through. This is checked as an
# exact set for the same reason as the roster above: if the one override goes
# missing, every domain silently falls back to its dark value and the run
# measures the dark palette twice while reporting a light-surface pass.
EXPECTED_LIGHT_OVERRIDES = frozenset({"stellar"})

# The two blocks the palette is declared in, dark first. A domain colour set on
# the root element anywhere else is refused rather than read, because a selector
# such as :root:root outranks :root and would decide the shipped colour while
# this check measured the one underneath it.
PALETTE_BLOCKS = (":root", '[data-theme="light"]')

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
        If either block is absent, if the light block is written before the
        base one, if the ``:root`` block does not declare exactly
        ``EXPECTED_DOMAINS``, if the light block does not declare exactly
        ``EXPECTED_LIGHT_OVERRIDES``, if either block contains a nested rule, if
        either writes a domain colour in a form the hex reader cannot measure,
        or if a domain colour is declared anywhere else in the file with a value
        neither block gives that domain.
    """
    css = _strip_comments(css)
    dark_selector, light_selector = PALETTE_BLOCKS

    _require_block(css, dark_selector)
    dark_declared = _domain_declarations(css, dark_selector)
    dark = _domains_in_block(dark_declared)
    _reject_unreadable(dark_selector, dark_declared, dark)
    _require_roster(dark_selector, set(dark), EXPECTED_DOMAINS)

    _require_block(css, light_selector)
    _require_light_after_dark(css)
    light_declared = _domain_declarations(css, light_selector)
    overrides = _domains_in_block(light_declared)
    _reject_unreadable(light_selector, light_declared, overrides)
    _require_roster(light_selector, set(overrides), EXPECTED_LIGHT_OVERRIDES)

    light = dict(dark)
    light.update(overrides)
    _reject_unmeasured_domain_rules(css, dark, light)
    return dark, light


def _require_light_after_dark(css):
    """Fail when the light block is written before the base palette.

    ``:root`` and ``[data-theme="light"]`` both select the root element at the
    same specificity, so the one written last is the one that wins. With the
    light block first, every override in it loses to the base value underneath
    and the light surface renders in the dark palette, while this check would
    still report the overrides as shipped.

    Parameters
    ----------
    css : str
        Comment-stripped text of ``tokens.css``.

    Raises
    ------
    ValueError
        If the first light block precedes the first base block.
    """
    dark_selector, light_selector = PALETTE_BLOCKS
    dark_at = light_at = None
    for position, (prelude, _body, _nested) in enumerate(_top_level_rules(css)):
        if prelude.lstrip().startswith("@"):
            continue
        if dark_at is None and _selector_targets(prelude, dark_selector):
            dark_at = position
        if light_at is None and _selector_targets(prelude, light_selector):
            light_at = position
    if dark_at is not None and light_at is not None and light_at < dark_at:
        raise ValueError(
            f"the {light_selector} block is written before the {dark_selector} "
            "block; the two select the root element at the same specificity, "
            "so the block written last wins and the light overrides would "
            "never apply; put the light block after the base palette"
        )


def _require_block(css, selector):
    """Fail when no top-level rule targets this selector at all.

    Without this, a missing block is reported as every one of its domains being
    absent, which points at the declarations rather than at the block that
    should hold them.

    Parameters
    ----------
    css : str
        Comment-stripped text of ``tokens.css``.
    selector : str
        The selector that must appear.

    Raises
    ------
    ValueError
        If no outermost rule targets the selector.
    """
    if not _top_level_bodies(css, selector):
        raise ValueError(
            f"no top-level {selector} block; the palette is read from the "
            f"{PALETTE_BLOCKS[0]} block and the {PALETTE_BLOCKS[1]} block, and "
            "both have to be present at the top level of the file"
        )


def _require_roster(selector, found, expected):
    """Fail unless a block declares exactly the domains it is expected to.

    Parameters
    ----------
    selector : str
        The block being checked, named in the error message.
    found : set of str
        Domain names read out of the block.
    expected : frozenset of str
        The names that block must declare, no more and no fewer.

    Raises
    ------
    ValueError
        If the two sets differ, naming what is missing and what is unexpected.
    """
    if found == expected:
        return
    detail = []
    missing = sorted(expected - found)
    extra = sorted(found - expected)
    if missing:
        detail.append(f"missing {', '.join(missing)}")
    if extra:
        detail.append(f"unexpected {', '.join(extra)}")
    raise ValueError(
        f"the {selector} block does not declare the expected domain colours: "
        + "; ".join(detail)
    )


def _reject_unreadable(selector, declarations, readable):
    """Fail on a ``--pt-dom-*`` declaration the hex reader had to skip.

    A domain written as a ``var()`` reference, a three-digit hex, or a colour
    function is a live value on the page but invisible to this check. Skipping
    it silently is the worst outcome: on the light block the dark value fills
    the gap, so the run measures a palette nobody ships and reports it as
    passing.

    Parameters
    ----------
    selector : str
        The block the declarations came from, named in the error message.
    declarations : dict of str to str
        Domain name to its winning value in that block.
    readable : dict of str to str
        The subset of those the hex reader recovered.

    Raises
    ------
    ValueError
        If the block declares a domain the hex reader did not recover.
    """
    skipped = sorted(set(declarations) - set(readable))
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

    Comment markers inside a quoted value are content, not syntax. The walk
    tracks quoting so a string holding ``/*`` cannot open a comment that then
    swallows the live declarations after it.

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
    out = []
    quote = None
    index = 0
    length = len(css)
    while index < length:
        char = css[index]
        if quote is not None:
            out.append(char)
            if char == "\\" and index + 1 < length:
                out.append(css[index + 1])
                index += 2
                continue
            if char == quote:
                quote = None
            index += 1
            continue
        if char in ('"', "'"):
            quote = char
            out.append(char)
            index += 1
            continue
        if char == "/" and css.startswith("/*", index):
            end = css.find("*/", index + 2)
            index = length if end == -1 else end + 2
            out.append(" ")
            continue
        out.append(char)
        index += 1
    return "".join(out)


_ATTRIBUTE_SELECTOR = re.compile(
    r"""\[\s*([-\w]+)\s*"""
    r"""(?:([~|^$*]?=)\s*(?:"([^"]*)"|'([^']*)'|([^\]\s]*))\s*([iIsS])?\s*)?\]"""
)


def _normalise_selector(part):
    """Return one selector with its attribute values written in a single form.

    ``[data-theme="light"]``, ``[data-theme='light']`` and ``[data-theme=light]``
    select the same elements, so a comparison against a spelled-out selector has
    to see them as one string. Whitespace inside the brackets is dropped and the
    value is requoted with double quotes. A trailing ``i`` asks for a
    case-insensitive match, so the value is lower-cased alongside it and the
    flag drops out; ``s`` asks for the case-sensitive match that is already the
    default and drops out on its own.

    Parameters
    ----------
    part : str
        A single selector, already split out of any comma-separated list.

    Returns
    -------
    str
        The selector with every attribute test in canonical form and its
        surrounding whitespace collapsed.
    """

    def rewrite(match):
        name, operator = match.group(1), match.group(2)
        if operator is None:
            return f"[{name}]"
        value = next(g for g in match.group(3, 4, 5) if g is not None)
        flag = match.group(6)
        if flag and flag.lower() == "i":
            value = value.lower()
        return f'[{name}{operator}"{value}"]'

    return re.sub(r"\s+", " ", _ATTRIBUTE_SELECTOR.sub(rewrite, part)).strip()


def _mask_bracketed(selector):
    """Return the selector with bracketed and parenthesised spans neutralised.

    Commas and whitespace inside ``[...]`` or ``(...)`` belong to an attribute
    value or a functional pseudo-class, not to the selector list or a descendant
    combinator. Replacing that content with a filler character lets a plain
    ``split`` and a plain combinator search work on the outer structure alone.

    Parameters
    ----------
    selector : str
        One selector or a comma-separated list of them.

    Returns
    -------
    str
        The same length of text, with every character inside brackets or
        parentheses replaced by ``_``.
    """
    out = []
    depth = 0
    for char in selector:
        if char in "[(":
            depth += 1
            out.append(char)
        elif char in "])":
            depth = max(0, depth - 1)
            out.append(char)
        elif depth:
            out.append("_")
        else:
            out.append(char)
    return "".join(out)


def _split_selector_list(prelude):
    """Return the individual selectors of a comma-separated prelude.

    Parameters
    ----------
    prelude : str
        The text between the previous rule and this one's opening brace.

    Returns
    -------
    list of str
        One entry per selector, stripped, skipping empty entries. Commas inside
        an attribute value or a functional pseudo-class do not split.
    """
    masked = _mask_bracketed(prelude)
    parts = []
    start = 0
    for index, char in enumerate(masked):
        if char == ",":
            parts.append(prelude[start:index])
            start = index + 1
    parts.append(prelude[start:])
    return [part.strip() for part in parts if part.strip()]


def _selector_targets(prelude, selector):
    """Return whether a rule's prelude targets exactly this selector.

    A selector list is split on commas and each part compared whole, so
    ``:root, html`` counts as a ``:root`` rule while a compound such as
    ``[data-theme="light"] .hero`` stays out of the theme block.

    Parameters
    ----------
    prelude : str
        The text between the previous rule and this one's opening brace.
    selector : str
        The selector being looked for.

    Returns
    -------
    bool
        True when any part of the list is exactly ``selector``, comparing the
        two in their canonical attribute-value form.
    """
    wanted = _normalise_selector(selector)
    return any(_normalise_selector(part) == wanted for part in _split_selector_list(prelude))


_CUSTOM_PROPERTY_NAME = re.compile(r"^\s*--[\w-]+$")


def _top_level_rules(css):
    """Return every outermost rule in the text as prelude, body, and nesting.

    Walks the text with a brace counter rather than a regex, so the structure
    is read the way a browser reads it. Three kinds of brace are distinguished
    from a rule's own braces: one inside a quoted string, one inside
    parentheses such as a ``url()`` value, and one inside a custom property's
    value, where the syntax permits an arbitrary token stream. Miscounting any
    of them would shift every following rule to the wrong depth.

    Parameters
    ----------
    css : str
        Comment-stripped text of ``tokens.css``.

    Returns
    -------
    list of tuple
        One ``(prelude, body, nested)`` triple per outermost rule, where
        ``prelude`` is the selector text preceding the brace, ``body`` is the
        text between the braces, and ``nested`` says whether the rule contains
        a rule of its own.
    """
    rules = []
    depth = 0
    paren = 0
    quote = None
    in_value = False
    value_brace = 0
    prelude = ""
    prelude_start = 0
    body_start = 0
    segment_start = 0
    nested = False
    index = 0
    length = len(css)
    while index < length:
        char = css[index]
        if quote is not None:
            if char == "\\":
                index += 2
                continue
            if char == quote:
                quote = None
            index += 1
            continue
        if char in ('"', "'"):
            quote = char
        elif char == "(":
            paren += 1
        elif char == ")":
            paren = max(0, paren - 1)
        elif paren:
            pass
        elif char == ":":
            if (
                depth >= 1
                and not in_value
                and _CUSTOM_PROPERTY_NAME.match(css[segment_start:index])
            ):
                in_value = True
        elif char == "{":
            if in_value:
                value_brace += 1
            else:
                depth += 1
                if depth == 1:
                    prelude = css[prelude_start:index]
                    body_start = index + 1
                    nested = False
                elif depth == 2:
                    nested = True
                segment_start = index + 1
        elif char == "}":
            if in_value and value_brace:
                value_brace -= 1
            elif depth >= 2:
                depth -= 1
                in_value = False
                segment_start = index + 1
            else:
                if depth == 1:
                    rules.append((prelude, css[body_start:index], nested))
                depth = 0
                in_value = False
                value_brace = 0
                prelude_start = index + 1
                segment_start = index + 1
        elif char == ";":
            if in_value and value_brace == 0:
                in_value = False
            if depth == 0:
                prelude_start = index + 1
            segment_start = index + 1
        index += 1
    return rules


def _top_level_bodies(css, selector):
    """Return the body of every top-level block that targets this selector.

    A rule nested inside ``@media``, ``@supports`` or ``@container`` carries the
    same selector text as the unconditional one, and a value that applies only
    under a condition must never stand in for the value the palette ships
    everywhere, so only the outermost rules are read.

    Parameters
    ----------
    css : str
        Comment-stripped text of ``tokens.css``.
    selector : str
        The selector to collect, matched whole against each part of a
        comma-separated list.

    Returns
    -------
    list of str
        One string per matching block, holding that block's declarations.

    Raises
    ------
    ValueError
        If a matching block contains a nested rule. Nesting is refused rather
        than skipped: a bare ``&`` block applies unconditionally and outranks
        the declarations beside it, so dropping it would measure a colour the
        page does not use.
    """
    bodies = []
    for prelude, body, nested in _top_level_rules(css):
        if prelude.lstrip().startswith("@"):
            continue
        if not _selector_targets(prelude, selector):
            continue
        if nested:
            raise ValueError(
                f"the {selector} block contains a nested rule; this check "
                "reads flat declarations only, so write the block without "
                "nesting"
            )
        bodies.append(body)
    return bodies


def _rules_declaring_domains(css, conditional=False):
    """Yield every rule that declares a domain colour, at any nesting depth.

    At-rules are descended into rather than skipped. ``@media``, ``@supports``
    and ``@container`` all apply on the shipping surface, and the rule they wrap
    carries the same selector as an unconditional one, so a value inside them
    reaches the page while sitting outside the two blocks the palette is read
    from. Everything below an at-rule is reported as conditional, which is what
    stops a wrapped ``:root`` passing itself off as the palette block. The one
    at-rule left alone is ``@property``, whose body holds descriptors rather
    than rules; ``_property_registrations`` reads those instead.

    Parameters
    ----------
    css : str
        Comment-stripped text of ``tokens.css``.
    conditional : bool, optional
        Whether this text is already inside an at-rule.

    Yields
    ------
    tuple of (str, str, bool)
        The rule's selector with its whitespace collapsed, its body, and
        whether it sits under an at-rule.
    """
    for prelude, body, _nested in _top_level_rules(css):
        head = " ".join(prelude.split())
        if head.startswith("@"):
            if _PROPERTY_REGISTRATION.match(head) is None:
                yield from _rules_declaring_domains(body, True)
        elif _DOMAIN_DECLARATION.search(body):
            yield head, body, conditional


def _property_registrations(css):
    """Yield every ``@property`` rule that registers a domain colour.

    A registered custom property carries its own ``initial-value``, and that
    value, not the one the palette declares on the root, is what an element
    computes wherever the property does not reach it by inheritance. Declaring
    ``inherits: false`` is enough to put every element below the root in that
    position at once. The registration therefore decides what the page paints
    while naming the colour in a descriptor rather than in a ``--pt-dom-*``
    declaration, so it has to be read separately from the rules that declare
    one.

    Parameters
    ----------
    css : str
        Comment-stripped text of ``tokens.css``.

    Every ``initial-value`` in the body is reported, not just the first. A
    descriptor repeated in one block follows the same rule as a repeated
    declaration, so the last one is what the browser registers, and a block
    that opens on a shipped colour can still end on one the check never
    measured.

    Yields
    ------
    tuple of (str, str, list of str)
        The at-rule's prelude with its whitespace collapsed, the domain name it
        registers, and every ``initial-value`` its body declares, in order.
    """
    for prelude, body, _nested in _top_level_rules(css):
        head = " ".join(prelude.split())
        if not head.startswith("@"):
            continue
        registered = _PROPERTY_REGISTRATION.match(head)
        if registered is None:
            yield from _property_registrations(body)
            continue
        initials = [_declaration_value(raw) for raw in _INITIAL_VALUE.findall(body)]
        yield head, registered.group(1), initials


def _reject_unmeasured_domain_rules(css, dark, light):
    """Refuse a domain colour the check has not measured.

    Custom properties inherit, so a domain colour set anywhere from the root
    down reaches the elements below it, and a selector that reaches the root at
    a higher specificity than ``:root``, ``:root:root`` or ``html:root``,
    decides what the page ships outright. Neither a combinator nor an at-rule
    wrapper makes such a declaration harmless: ``:root body`` covers the whole
    visible page, and ``@media screen`` applies on the only surface that
    matters. A bare ``html`` is the one root-targeting form that loses instead
    of winning, since ``:root`` outranks a type selector; it is refused on the
    same terms all the same, because the rule is about the value rather than
    about which selector happens to win.

    What separates a safe declaration from an unsafe one is therefore its value,
    not its selector. Repeating a colour the palette already declares for that
    domain reaches the page having been measured, so the component retints that
    restore a base colour on a themed subtree stay allowed. Any other value is
    refused, because the separability guarantee covers the seven colours in the
    two palette blocks and nothing else.

    A selector list is judged part by part. Only the parts naming a palette
    block are read as the palette; the rest have to satisfy the value rule on
    their own, because a list such as ``:root, body`` also declares the colour
    on body, where a later ``:root`` block takes it back for the root element
    and leaves the whole visible page on the value the list gave it.

    An ``@property`` rule is held to the same value rule through its
    ``initial-value``, since that is what an element computes wherever the
    property does not reach it by inheritance, and a registration declaring
    ``inherits: false`` puts every element below the root there at once. A
    registration that gives no initial value at all is refused on the same
    terms, because the rule is about the value the page can end up with rather
    than about which declaration happens to win. Every ``initial-value`` in the
    block has to satisfy it, since a repeated descriptor resolves the same way
    a repeated declaration does and a block that opens on a shipped colour can
    still end on one the check never measured.

    Parameters
    ----------
    css : str
        Comment-stripped text of ``tokens.css``.
    dark : dict of str to str
        Domain name to hex, as read from the ``:root`` block.
    light : dict of str to str
        The same for the light surface set.

    Raises
    ------
    ValueError
        If a ``--pt-dom-*`` declaration outside the two palette blocks carries a
        value neither block declares for that domain, or if an ``@property``
        rule registers a domain colour without repeating one of those values as
        its ``initial-value``.
    """
    measured = {}
    for palette in (dark, light):
        for name, value in palette.items():
            measured.setdefault(name, set()).add(value.lower())

    for prelude, body, conditional in _rules_declaring_domains(css):
        if not conditional:
            carried = [
                part
                for part in _split_selector_list(prelude)
                if not any(
                    _selector_targets(part, known) for known in PALETTE_BLOCKS
                )
            ]
            if not carried:
                continue
            prelude = ", ".join(carried)
        for name, raw in _DOMAIN_DECLARATION.findall(body):
            value = _declaration_value(raw)
            if value.lower() in measured.get(name, ()):
                continue
            raise ValueError(
                f"the rule '{prelude}' declares --pt-dom-{name}: {value}, "
                f"which is not a colour this check measured for {name}; "
                f"outside the {PALETTE_BLOCKS[0]} block and the "
                f"{PALETTE_BLOCKS[1]} block, an @media or @supports wrapper "
                "included, a domain colour has to repeat the value one of "
                "those blocks declares for it, because the separability "
                "guarantee covers those colours and nothing else"
            )

    for prelude, name, initials in _property_registrations(css):
        if not initials:
            raise ValueError(
                f"the rule '{prelude}' registers --pt-dom-{name} without an "
                "initial-value, so an element the property does not reach by "
                "inheritance computes no colour at all; a registration has to "
                "carry an initial-value repeating the colour one of the "
                f"{PALETTE_BLOCKS[0]} and {PALETTE_BLOCKS[1]} blocks declares "
                "for that domain"
            )
        for initial in initials:
            if initial.lower() in measured.get(name, ()):
                continue
            raise ValueError(
                f"the rule '{prelude}' gives --pt-dom-{name} the initial-value "
                f"{initial}, which is not a colour this check measured for "
                f"{name}; a registered property computes its initial value "
                "wherever it does not reach an element by inheritance, and "
                "inherits: false puts every element below the root there at "
                "once, so the initial-value has to repeat the colour one of "
                "the palette blocks declares for that domain"
            )


_DOMAIN_DECLARATION = re.compile(r"--pt-dom-([a-z0-9-]+)\s*:\s*([^;}]*)")
# The at-rule keyword is matched without regard to case, the way CSS matches
# it, while the custom-property name stays case-sensitive, the way CSS treats
# that. Folding the whole pattern would let --PT-DOM-ATMOS, a different
# property altogether, answer for a domain.
_PROPERTY_REGISTRATION = re.compile(r"^@(?i:property)\s+--pt-dom-([a-zA-Z0-9-]+)$")
_INITIAL_VALUE = re.compile(r"(?:^|[;{\s])initial-value\s*:\s*([^;}]*)", re.I)
_NAMED_DECLARATION = re.compile(r"--pt-([a-z0-9-]+)\s*:\s*([^;}]*)")
_SIX_DIGIT_HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")
_IMPORTANT = re.compile(r"!\s*important\s*$", re.I)


def _declaration_value(raw):
    """Return a declared value with its priority flag and whitespace removed.

    ``!important`` raises a declaration's priority; it does not change the
    colour. Reading it as part of the value would report a hex the file plainly
    writes as unmeasurable.

    Parameters
    ----------
    raw : str
        The text between the colon and the end of the declaration.

    Returns
    -------
    str
        The value alone, stripped.
    """
    return _IMPORTANT.sub("", raw).strip()


def _domain_declarations(css, selector):
    """Return the winning ``--pt-dom-*`` value of each domain in one block.

    A declaration repeated within a block is a live CSS idiom: the later one
    wins and is what the page ships. Reading in source order and letting the
    last write stand keeps the check measuring the shipped value rather than
    the first one it happens to recognise. The value runs to the next ``;`` or
    to the closing brace, so a final declaration written without a trailing
    semicolon reads the same as any other.

    Parameters
    ----------
    css : str
        Comment-stripped text of ``tokens.css``.
    selector : str
        The selector whose blocks to read.

    Returns
    -------
    dict of str to str
        Domain name (the part after ``--pt-dom-``) to its winning value,
        verbatim and unvalidated.
    """
    winning = {}
    for block in _top_level_bodies(css, selector):
        for match in _DOMAIN_DECLARATION.finditer(block):
            winning[match.group(1)] = _declaration_value(match.group(2))
    return winning


def _domains_in_block(declarations):
    """Reduce declared domain values to the ones readable as a six-digit hex.

    Parameters
    ----------
    declarations : dict of str to str
        Domain name to its winning value, from ``_domain_declarations``.

    Returns
    -------
    dict of str to str
        Domain name to lower-cased hex, omitting every value that is not a
        plain six-digit hex literal.
    """
    return {
        name: value.lower()
        for name, value in declarations.items()
        if _SIX_DIGIT_HEX.match(value)
    }


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
        Name to lower-cased hex, in the order requested.

    Raises
    ------
    ValueError
        If any requested name is missing from the block or written in a form
        this check cannot read. Only the requested names are held, so a colour
        added to the palette is measured once it joins ``names``; what the
        requirement stops is a renamed or removed token shrinking the
        cross-palette report without a word, since the colour that drops out of
        the comparison is exactly the one a future domain then collides with.
    """
    names = tuple(names)
    css = _strip_comments(css)
    declared = {}
    for block in _top_level_bodies(css, PALETTE_BLOCKS[0]):
        for match in _NAMED_DECLARATION.finditer(block):
            declared[match.group(1)] = _declaration_value(match.group(2))
    readable = {
        n: declared[n].lower()
        for n in names
        if n in declared and _SIX_DIGIT_HEX.match(declared[n])
    }
    missing = [n for n in names if n not in readable]
    if missing:
        raise ValueError(
            "the :root block does not declare a readable six-digit hex for "
            + ", ".join("--pt-" + n for n in missing)
        )
    return readable


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
        # utf-8-sig, so a byte-order mark left by an editor is consumed rather
        # than read as part of the first selector.
        css = TOKENS_CSS.read_text(encoding="utf-8-sig")
        dark, light = parse_domain_colours(css)
    except (OSError, ValueError) as exc:
        print(f"could not read the domain colours: {exc}")
        return 1
    try:
        named = parse_named_colours(css, CROSS_PALETTE)
    except ValueError as exc:
        print(f"could not read the cross-palette colours: {exc}")
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
    for name, value in named.items():
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
    print("    vs the other six domains    vs the rest of the palette")
    for name, value in REJECTED.items():
        near, other, dichromacy = closest_in(value, incumbents)
        # A candidate that is itself a palette colour would otherwise be
        # measured against itself and report a flattering zero.
        rest = {k: v for k, v in others.items() if v.lower() != value.lower()}
        if rest:
            distance, other_name, other_dichromacy = closest_in(value, rest)
            cross = f"{distance:6.2f} --pt-{other_name:<10} {other_dichromacy[:6]}"
        else:
            cross = f"{'no palette colour to compare':<30}"
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
