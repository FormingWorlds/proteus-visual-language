"""proteus_mpl — PROTEUS Thermocline matplotlib theme.

Usage:
    import proteus_mpl
    proteus_mpl.use()          # light variant, Paper background
    proteus_mpl.use("dark")    # dark variant, Void background (matches dark slides)
    proteus_mpl.use("white")   # light variant on pure white (journal pages)

Registers the bundled brand fonts, the `proteus`, `proteus_div`, and
`proteus_phase` colormaps (+ reversed `_r` versions), applies the style
sheet, and sets `proteus` as the default image colormap.

All brand colors are available by name in COLORS, the categorical cycles as
CYCLE (light/white) and CYCLE_DARK, and the stable module-domain colors as
DOMAINS. Solar gold is the star (MORS), verdant the habitable endpoint; both
are accents that extend the cycle for many-line figures.
"""

from pathlib import Path

_HERE = Path(__file__).parent

# ---------------------------------------------------------------- colors
COLORS = {
    # core
    "magma":   "#E23D28",
    "mantle":  "#8E1F12",
    "crimson": "#C2362B",
    "ocean":   "#1B6FA8",
    "abyss":   "#14406B",
    "azure":   "#4FA3D9",
    "ice":     "#A8D4E8",
    "void":    "#05070B",
    "basalt":  "#0E131B",
    "paper":   "#F2F5F7",
    "ink":     "#10151B",
    # accents — solar is the star (MORS), verdant the habitable endpoint
    "solar":      "#E0A32E",   # bright: dark surfaces and the data cycle
    "solar_deep": "#C8860F",   # deepened: gold fills/text on light (3.06:1 on white)
    "verdant":    "#57A05C",   # brand green, distinct from the semantic positive
    # neutrals
    "fog":     "#7A8894",
    "mist":    "#9FB0BE",
}

# Stable module-domain colors — identical across papers, talks, docs, diagrams.
# CVD-checked (Machado 2009 protan/deutan/tritan, full severity): min pairwise
# deltaE = 16.4. Keep legends or direct labels on multi-series plots regardless.
DOMAINS = {
    "interior":   "#E23D28",   # SPIDER, Aragog, Zalmoxis
    "outgassing": "#A03123",   # CALLIOPE, Atmodeller
    "tidal":      "#593E74",   # LovePy, Obliqua
    "chemistry":  "#1B6FA8",   # VULCAN, ZEPHYRUS
    "atmosphere": "#4FA3D9",   # AGNI, JANUS
    "stellar":    "#E0A32E",   # MORS — solar gold; prefer COLORS["solar_deep"]
                               # for gold fills or thin marks on light surfaces
}

# Categorical cycles. Both are neutral-first: a single-series plot draws in
# ink (light) / paper (dark), so magma stays a deliberate signal.
# LIGHT: ink + 7 hues + fog. Machado 2009 CVD min pairwise deltaE = 15.7.
# DARK: paper + 5 hues (Void leaves less room). min pairwise deltaE = 16.8.
# Never insert extra neutral greys between the hues: a grey next to a
# desaturated hue collapses the CVD separation to ~6. Past the cycle, encode
# additional series with line style, not more hues.
CYCLE = ["#10151B", "#E23D28", "#E0A32E", "#57A05C", "#1B6FA8", "#593E74",
         "#A03123", "#7A8894", "#4FA3D9"]
CYCLE_DARK = ["#F2F5F7", "#E23D28", "#E0A32E", "#57C08A", "#A8D4E8", "#9B7BBE"]

# ---------------------------------------------------------------- colormaps
_SEQ = ["#05070B", "#14406B", "#1B6FA8", "#4FA3D9", "#A8D4E8", "#F2F5F7"]          # void -> paper (cool)
_DIV = ["#C2362B", "#E08373", "#D8DEE3", "#7FAED2", "#1B6FA8"]                     # light-mid diverging (print-safe)
_PHASE = ["#E23D28", "#8E1F12", "#3A120C", "#05070B", "#0E2A45", "#14406B",
          "#1B6FA8", "#4FA3D9", "#A8D4E8"]                                          # brand ramp, dark-mid


def _register_cmaps():
    import matplotlib as mpl
    from matplotlib.colors import LinearSegmentedColormap

    for name, stops in [("proteus", _SEQ), ("proteus_div", _DIV), ("proteus_phase", _PHASE)]:
        if name in mpl.colormaps:
            continue
        cmap = LinearSegmentedColormap.from_list(name, stops)
        mpl.colormaps.register(cmap, name=name)
        mpl.colormaps.register(cmap.reversed(), name=name + "_r")


def _register_fonts():
    """Register the bundled fonts for this session (no system install needed).

    The package ships the OFL TTFs (Instrument Sans, Spline Sans Mono) in
    proteus_mpl/fonts/. Missing fonts degrade gracefully to matplotlib's
    default sans.
    """
    from matplotlib import font_manager
    fonts_dir = _HERE / "fonts"
    if not fonts_dir.is_dir():
        return
    for f in fonts_dir.glob("*.[to]tf"):
        try:
            font_manager.fontManager.addfont(str(f))
        except Exception:
            pass


def use(variant: str = "light"):
    """Apply the PROTEUS theme.

    Parameters
    ----------
    variant : {"light", "dark", "white"}, default "light"
        Surface treatment. "light" is the Paper background (papers, light
        slides), "dark" the Void background (dark slides, hero figures),
        "white" the light theme on a pure-white background for journals
        whose pages must not show a card edge.
    """
    import matplotlib as mpl
    import matplotlib.pyplot as plt

    _register_fonts()
    _register_cmaps()

    base = _HERE / "proteus.mplstyle"
    if variant in ("light", "white"):
        plt.style.use(str(base))
        mpl.rcParams["axes.prop_cycle"] = mpl.cycler(color=CYCLE)
        if variant == "white":
            for key in ("figure.facecolor", "savefig.facecolor", "axes.facecolor"):
                mpl.rcParams[key] = "#FFFFFF"
    elif variant == "dark":
        plt.style.use([str(base), str(_HERE / "proteus_dark.mplstyle")])
        mpl.rcParams["axes.prop_cycle"] = mpl.cycler(color=CYCLE_DARK)
    else:
        raise ValueError(f"variant must be 'light', 'dark', or 'white', got {variant!r}")

    mpl.rcParams["image.cmap"] = "proteus"
