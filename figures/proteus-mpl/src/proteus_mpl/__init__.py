"""proteus_mpl — PROTEUS Thermocline matplotlib theme.

Usage:
    import proteus_mpl
    proteus_mpl.use()          # light variant, Paper background
    proteus_mpl.use("dark")    # dark variant, Void background (matches dark slides)

Registers the brand fonts (if bundled in fonts/), the `proteus`,
`proteus_div`, and `proteus_phase` colormaps (+ reversed `_r` versions),
applies the style sheet, and sets `proteus` as the default image colormap.

All brand colors are available by name in COLORS, the categorical cycles as
CYCLE (light) and CYCLE_DARK, and the stable module-domain colors as DOMAINS.
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
    "stellar":    "#A8D4E8",   # MORS
}

# Categorical cycles. Light cycle = the six domain colors + ink + fog;
# dark drops the deep colors that vanish on Void and substitutes light tones.
CYCLE = ["#E23D28", "#1B6FA8", "#593E74", "#4FA3D9", "#A03123", "#10151B", "#7A8894"]
CYCLE_DARK = ["#E23D28", "#4FA3D9", "#A8D4E8", "#9B7BBE", "#E9EEF2", "#8FA0AE"]

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
    """Register bundled fonts for this session (no system install needed).

    Drop the OFL TTFs into proteus_mpl/fonts/ :
      Sora (variable or static weights), InstrumentSans, SplineSansMono.
    Missing fonts degrade gracefully to matplotlib's default sans.
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
    """Apply the PROTEUS theme. variant: 'light' (Paper) or 'dark' (Void)."""
    import matplotlib as mpl
    import matplotlib.pyplot as plt

    _register_fonts()
    _register_cmaps()

    base = _HERE / "proteus.mplstyle"
    if variant == "light":
        plt.style.use(str(base))
        mpl.rcParams["axes.prop_cycle"] = mpl.cycler(color=CYCLE)
    elif variant == "dark":
        plt.style.use([str(base), str(_HERE / "proteus_dark.mplstyle")])
        mpl.rcParams["axes.prop_cycle"] = mpl.cycler(color=CYCLE_DARK)
    else:
        raise ValueError(f"variant must be 'light' or 'dark', got {variant!r}")

    mpl.rcParams["image.cmap"] = "proteus"
