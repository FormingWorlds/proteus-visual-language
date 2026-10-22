"""Validation plots: one light and one dark file per case, byte-stable and size-capped.

Usage:
    from proteus_mpl.validation import save
    save(make_figure, "stefan_boltzmann", "docs/assets/validation")

`make_figure` is called once under ``use("light")`` and once under
``use("dark")``. A line plot (``kind="line"``) is written as SVG with no date,
a fixed creator and a fixed hash salt; a map or heatmap (``kind="map"``) is
written as AVIF at quality 80 with fixed encoder settings. With the same
matplotlib and Pillow versions the same figure gives the same bytes. Every file
must stay at or below `MAX_BYTES`.
"""

import io
import os
import re
from contextlib import suppress
from pathlib import Path
from xml.sax.saxutils import escape

MAX_BYTES = 60_000
SVG_HASHSALT = "proteus-validation"
AVIF_QUALITY = 80
AVIF_OPTIONS = {"speed": 6, "max_threads": 1, "codec": "aom", "subsampling": "4:2:0"}
MAP_DPI = 150
KINDS = {"line": "svg", "map": "avif"}

_VARIANTS = (("light", ""), ("dark", "_dark"))
_STEM = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
_NOT_XML = re.compile("[^\t\n\r\x20-\ud7ff\ue000-\ufffd\U00010000-\U0010ffff]")
_HINTS = {
    "line": "plot fewer points or a smaller figure, save a dense field with "
    "kind='map', or draw a small dense element with rasterized=True",
    "map": "use a smaller figure or a smoother field",
}
_XMP = (
    '<x:xmpmeta xmlns:x="adobe:ns:meta/">'
    '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
    '<rdf:Description xmlns:dc="http://purl.org/dc/elements/1.1/">'
    "<dc:description>{}</dc:description>"
    "</rdf:Description></rdf:RDF></x:xmpmeta>"
)


def check_args(name, kind):
    """Raise ValueError for an unknown `kind` or a `name` that is not a plain file stem."""
    if not isinstance(kind, str) or kind not in KINDS:
        raise ValueError(f"kind must be 'line' or 'map', got {kind!r}")
    if not isinstance(name, str) or not _STEM.fullmatch(name):
        raise ValueError(f"name must be a plain file stem such as 'case_1', got {name!r}")
    if name.lower().endswith("_dark"):
        raise ValueError(f"name must not end in '_dark', the dark file's suffix, got {name!r}")


def _render(fig, kind, stamp):
    """Encode one figure as SVG (line) or AVIF (map) and return the bytes."""
    buf = io.BytesIO()
    if kind == "line":
        metadata = {"Date": None, "Creator": "proteus-mpl", "Description": stamp or None}
        fig.savefig(buf, format="svg", metadata=metadata)
        return buf.getvalue()

    from PIL import Image

    fig.savefig(buf, format="png", dpi=MAP_DPI)
    out = io.BytesIO()
    xmp = _XMP.format(escape(stamp)).encode() if stamp else None
    Image.open(buf).convert("RGB").save(out, "AVIF", quality=AVIF_QUALITY, xmp=xmp, **AVIF_OPTIONS)
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
        letter or digit and not ending in ``_dark``.
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
        For an unknown `kind`, a `name` that is not a plain file stem, a figure
        that was open before the call or is returned for both themes, or a file
        above `MAX_BYTES`. Nothing is written then.
    OSError
        From a failed write. The previous files are moved back into place and
        the first error is raised; a folder the call created stays.
    TypeError
        When `fig_factory` is not callable or returns no Figure.
    """
    check_args(name, kind)
    if not callable(fig_factory):
        raise TypeError(f"fig_factory must be callable, got {type(fig_factory).__name__}")

    import matplotlib.pyplot as plt
    from matplotlib.figure import Figure

    from . import use

    stamp = "; ".join(
        filter(None, (test_id and f"test: {test_id}", command and f"command: {command}"))
    )
    stamp = _NOT_XML.sub("", stamp)
    files, figures = [], []
    for variant, tail in _VARIANTS:
        open_before = set(plt.get_fignums())
        with plt.rc_context({"svg.hashsalt": SVG_HASHSALT}):
            use(variant)
            try:
                fig = fig_factory()
                if not isinstance(fig, Figure):
                    raise TypeError(
                        f"fig_factory returned {type(fig).__name__}, not a matplotlib Figure"
                    )
                if getattr(fig, "number", None) in open_before:
                    raise ValueError(
                        f"fig_factory returned figure {fig.number}, which was open before the "
                        "call; create a new figure inside the factory"
                    )
                if any(fig is seen for seen in figures):
                    raise ValueError(
                        "fig_factory returned the same figure for both themes; create a new "
                        "figure inside the factory"
                    )
                figures.append(fig)
                files.append((f"{name}{tail}.{KINDS[kind]}", _render(fig, kind, stamp)))
            finally:
                for num in set(plt.get_fignums()) - open_before:
                    plt.close(num)

    for fname, data in files:
        if len(data) > MAX_BYTES:
            raise ValueError(f"{fname}: {len(data)} B, above the {MAX_BYTES} B cap; {_HINTS[kind]}")

    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    targets = [outdir / fname for fname, _ in files]
    parts = [outdir / f"{fname}.part" for fname, _ in files]
    backups = [outdir / f"{fname}.bak" for fname, _ in files]
    moved, placed = [], []
    try:
        for part, (_, data) in zip(parts, files):
            part.write_bytes(data)
        for target, backup in zip(targets, backups):
            if os.path.lexists(target):
                os.replace(target, backup)
                moved.append((backup, target))
        for part, target in zip(parts, targets):
            os.replace(part, target)
            placed.append(target)
    except BaseException:
        # Put the previous files back; a failing cleanup step must not hide the first error.
        for path in [*parts, *placed]:
            with suppress(OSError):
                path.unlink(missing_ok=True)
        for backup, target in moved:
            with suppress(OSError):
                os.replace(backup, target)
        raise
    for backup, _ in moved:
        with suppress(OSError):
            backup.unlink()
    return targets
