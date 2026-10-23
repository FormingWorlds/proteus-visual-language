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

import html
import io
import json
import os
import re
from contextlib import suppress
from pathlib import Path
from xml.sax.saxutils import escape

import numpy as np

MAX_BYTES = 60_000
# Relative tolerance of the data summary, on the scale of each coordinate's range
SUMMARY_RTOL = 1e-6
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
    TypeError
        When `fig_factory` is not callable or returns no Figure. Nothing is
        written then.
    IsADirectoryError
        When a target name is a folder. Nothing is written then.
    OSError
        From a failed write. Both files are written as ``.part`` files first
        and then renamed into place one at a time; on any failure the ``.part``
        files are removed and the first error is raised. A failure between the
        two renames leaves the new light file beside the dark file of an
        earlier save. A folder the call created stays.
    """
    files, _ = render(fig_factory, name, kind, test_id=test_id, command=command)

    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    targets = [outdir / fname for fname, _ in files]
    parts = [outdir / f"{fname}.part" for fname, _ in files]
    for target in targets:
        if target.is_dir() and not target.is_symlink():
            raise IsADirectoryError(f"{target}: a folder, not a plot file")
    try:
        for part, (_, data) in zip(parts, files):
            part.write_bytes(data)
        for part, target in zip(parts, targets):
            os.replace(part, target)
    except BaseException:
        for part in parts:
            with suppress(OSError):
                part.unlink(missing_ok=True)
        raise
    return targets


def render(fig_factory, name, kind="line", *, test_id=None, command=None):
    """Make the light and the dark file of one validation plot in memory.

    Takes the arguments of `save` except `outdir` and raises as it does, before
    anything is written. Returns the list of ``(file name, bytes)`` pairs, light
    then dark, and the data summary of the light figure (`summarize`), which
    both files carry in their description after the test id and the command.
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
    files, figures, summary = [], [], None
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
                if summary is None:
                    summary = summarize(fig)
                full = "; ".join(filter(None, (stamp, f"summary: {json.dumps(summary)}")))
                full = _NOT_XML.sub("", full)
                files.append((f"{name}{tail}.{KINDS[kind]}", _render(fig, kind, full)))
            finally:
                for num in set(plt.get_fignums()) - open_before:
                    plt.close(num)

    for fname, data in files:
        if len(data) > MAX_BYTES:
            raise ValueError(f"{fname}: {len(data)} B, above the {MAX_BYTES} B cap; {_HINTS[kind]}")
    return files, summary


def _stats(*coords):
    """Point count and, per coordinate, min, max and mean over the points finite in all."""
    arrays = [np.ravel(np.ma.filled(np.ma.asarray(c, dtype=float), np.nan)) for c in coords]
    keep = np.logical_and.reduce([np.isfinite(a) for a in arrays])
    out = [int(keep.sum())]
    for a in arrays:
        a = a[keep]
        out += [float(a.min()), float(a.max()), float(a.mean())] if a.size else [None] * 3
    return out


def summarize(fig):
    """Data summary of a figure, the part of a plot that does not depend on its renderer.

    Per axes: each line as ``[n, xmin, xmax, xmean, ymin, ymax, ymean]`` over its
    points finite in both coordinates; each collection (scatter points) the same
    over its offsets; each image as ``[ny, nx, vmin, vmax, vmean]``.
    """
    axes = []
    for ax in fig.axes:
        images = []
        for image in ax.get_images():
            arr = np.ma.asarray(image.get_array())
            images.append(list(arr.shape[:2]) + _stats(arr)[1:])
        axes.append(
            {
                "lines": [_stats(line.get_xdata(), line.get_ydata()) for line in ax.get_lines()],
                "collections": [
                    _stats(*np.asarray(c.get_offsets(), dtype=float).reshape(-1, 2).T)
                    for c in ax.collections
                ],
                "images": images,
            }
        )
    return {"axes": axes}


_DESCRIPTION = re.compile(rb"<dc:description>(.*?)</dc:description>", re.DOTALL)


def read_summary(path):
    """Return the data summary a validation plot file carries, or None when it has none."""
    match = _DESCRIPTION.search(Path(path).read_bytes())
    if not match:
        return None
    text = html.unescape(match.group(1).decode("utf-8", "replace"))
    _, sep, tail = text.partition("summary: ")
    return json.loads(tail) if sep else None


def compare_summaries(new, old, rtol=SUMMARY_RTOL):
    """List the differences between two data summaries; an empty list when they agree.

    Counts must match; each min, max and mean must agree within `rtol` times the
    larger magnitude of the committed min and max of that coordinate.
    """
    if len(new["axes"]) != len(old["axes"]):
        return [f"axes count {len(new['axes'])}, committed {len(old['axes'])}"]
    diffs = []
    for i, (a, b) in enumerate(zip(new["axes"], old["axes"])):
        for key, label, head in (("lines", "line", 1), ("collections", "collection", 1),
                                 ("images", "image", 2)):
            if len(a[key]) != len(b[key]):
                diffs.append(f"axes {i}: {label} count {len(a[key])}, committed {len(b[key])}")
                continue
            for j, (x, y) in enumerate(zip(a[key], b[key])):
                where = f"axes {i} {label} {j}"
                if x[:head] != y[:head]:
                    diffs.append(f"{where}: point count {x[:head]}, committed {y[:head]}")
                    continue
                for k in range(head, len(y), 3):
                    lo, hi = y[k], y[k + 1]
                    scale = 0.0 if lo is None else max(abs(lo), abs(hi))
                    for got, want in zip(x[k : k + 3], y[k : k + 3]):
                        if (got is None) != (want is None) or (
                            want is not None and abs(got - want) > rtol * scale
                        ):
                            diffs.append(f"{where}: {got!r}, committed {want!r}")
    return diffs
