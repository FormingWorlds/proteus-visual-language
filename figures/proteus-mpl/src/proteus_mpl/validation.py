"""Validation plots: one light and one dark file per case, byte-stable and size-capped.

Usage:
    from proteus_mpl.validation import save
    save(make_figure, "stefan_boltzmann", "docs/assets/validation")

`make_figure` is called once under ``use("light")`` and once under
``use("dark")``. A line plot (``kind="line"``) is written as SVG with no date
and a fixed hash salt, so the same figure gives the same bytes; a map or
heatmap (``kind="map"``) is written as AVIF at quality 80. Every file must stay
at or below `MAX_BYTES`.
"""

import io
import os
import re
from pathlib import Path
from xml.sax.saxutils import escape

MAX_BYTES = 40_000
SVG_HASHSALT = "proteus-validation"
AVIF_QUALITY = 80
MAP_DPI = 150
KINDS = {"line": "svg", "map": "avif"}

_VARIANTS = (("light", ""), ("dark", "_dark"))
_STEM = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
_XMP = (
    '<x:xmpmeta xmlns:x="adobe:ns:meta/">'
    '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
    '<rdf:Description xmlns:dc="http://purl.org/dc/elements/1.1/">'
    "<dc:description>{}</dc:description>"
    "</rdf:Description></rdf:RDF></x:xmpmeta>"
)


def _stamp(test_id, command):
    """Return the metadata text ``test: <id>; command: <cmd>`` from the given parts."""
    parts = []
    if test_id:
        parts.append(f"test: {test_id}")
    if command:
        parts.append(f"command: {command}")
    return "; ".join(parts)


def _render(fig, kind, stamp):
    """Encode one figure as SVG (line) or AVIF (map) and return the bytes."""
    import matplotlib

    buf = io.BytesIO()
    if kind == "line":
        metadata = {"Date": None}
        if stamp:
            metadata["Description"] = stamp
        with matplotlib.rc_context({"svg.hashsalt": SVG_HASHSALT}):
            fig.savefig(buf, format="svg", metadata=metadata)
        return buf.getvalue()

    from PIL import Image

    fig.savefig(buf, format="png", dpi=MAP_DPI)
    out = io.BytesIO()
    extra = {"xmp": _XMP.format(escape(stamp)).encode()} if stamp else {}
    with Image.open(buf) as image:
        image.convert("RGB").save(out, "AVIF", quality=AVIF_QUALITY, **extra)
    return out.getvalue()


def save(fig_factory, name, outdir, kind="line", *, test_id=None, command=None):
    """Write the light and the dark file of one validation plot.

    Parameters
    ----------
    fig_factory : callable
        Called with no arguments, once per variant; returns a
        `matplotlib.figure.Figure`. It is called inside the theme, so it must
        create the figure itself rather than return one made earlier.
    name : str
        File stem: letters, digits, ``.``, ``_`` and ``-``, starting with a
        letter or digit.
    outdir : str or path-like
        Folder for the files; created when missing.
    kind : {"line", "map"}, default "line"
        ``"line"`` writes ``<name>.svg`` and ``<name>_dark.svg``; ``"map"``
        writes ``<name>.avif`` and ``<name>_dark.avif``.
    test_id : str, optional
        Test id written into the file metadata.
    command : str, optional
        Command that makes the plot again, written into the file metadata.

    Returns
    -------
    list of pathlib.Path
        The light file, then the dark file.

    Raises
    ------
    ValueError
        For an unknown `kind`, a `name` that is not a plain file stem, or a
        file above `MAX_BYTES`. Nothing is written when one file is too large.
    TypeError
        When `fig_factory` is not callable or returns no Figure.
    """
    if kind not in KINDS:
        raise ValueError(f"kind must be 'line' or 'map', got {kind!r}")
    if not isinstance(name, str) or not _STEM.fullmatch(name):
        raise ValueError(f"name must be a plain file stem such as 'case_1', got {name!r}")
    if not callable(fig_factory):
        raise TypeError(f"fig_factory must be callable, got {type(fig_factory).__name__}")

    import matplotlib
    import matplotlib.pyplot as plt
    from matplotlib.figure import Figure

    from . import use

    stamp = _stamp(test_id, command)
    files = []
    for variant, tail in _VARIANTS:
        with matplotlib.rc_context():
            use(variant)
            fig = fig_factory()
            if not isinstance(fig, Figure):
                raise TypeError(
                    f"fig_factory returned {type(fig).__name__}, not a matplotlib Figure"
                )
            try:
                files.append((f"{name}{tail}.{KINDS[kind]}", _render(fig, kind, stamp)))
            finally:
                plt.close(fig)

    for fname, data in files:
        if len(data) > MAX_BYTES:
            raise ValueError(
                f"{fname}: {len(data)} B, above the {MAX_BYTES} B cap; plot fewer "
                "points or a smaller figure, or save a dense field with kind='map'"
            )

    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    paths = []
    for fname, data in files:
        target = outdir / fname
        part = target.with_name(fname + ".part")
        part.write_bytes(data)
        os.replace(part, target)
        paths.append(target)
    return paths
