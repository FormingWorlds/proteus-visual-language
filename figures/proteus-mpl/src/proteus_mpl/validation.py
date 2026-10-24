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
import json
import os
import re
from contextlib import suppress
from pathlib import Path
from xml.sax.saxutils import escape

import numpy as np

MAX_BYTES = 60_000
# Tolerance of the data summary, relative to the range of each committed coordinate
SUMMARY_RTOL = 1e-6
SUMMARY_VERSION = 1
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
        that was open before the call or is returned for both themes, a file
        above `MAX_BYTES`, or light and dark figures that hold different data.
        Nothing is written then.
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
    anything is written, and raises ValueError when the light and dark figures hold
    different data. Returns the list of ``(file name, bytes)`` pairs, light then dark,
    and the data summary of the light figure (`summarize`), which both files carry in
    their description after the test id and the command.
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
    files, figures, summary, diffs = [], [], None, []
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
                    stamp = "; ".join(filter(None, (stamp, f"summary: {json.dumps(summary)}")))
                    stamp = _NOT_XML.sub("", stamp)
                else:
                    diffs += compare_summaries(summarize(fig), summary)
                files.append((f"{name}{tail}.{KINDS[kind]}", _render(fig, kind, stamp)))
            finally:
                for num in set(plt.get_fignums()) - open_before:
                    plt.close(num)

    for fname, data in files:
        if len(data) > MAX_BYTES:
            raise ValueError(f"{fname}: {len(data)} B, above the {MAX_BYTES} B cap; {_HINTS[kind]}")
    if diffs:
        raise ValueError(
            f"{name}: the light and dark figures hold different data ({diffs[0]}); draw the "
            "same data under both themes"
        )
    return files, summary


def _stats(*coords):
    """Point count and, per coordinate, min, max, mean and ramp over the points finite in all.

    The ramp is the mean of the values weighted by a line from -1 at the first point to
    1 at the last, so a reversed series changes it. Means are taken on values divided by
    their largest magnitude, which keeps them finite.
    """
    arrays = [np.ravel(np.ma.filled(np.ma.asarray(c, dtype=float), np.nan)) for c in coords]
    keep = np.logical_and.reduce([np.isfinite(a) for a in arrays])
    n = int(keep.sum())
    if not n:
        return [0] + [None] * 4 * len(arrays)
    ramp = np.linspace(-1.0, 1.0, n) if n > 1 else np.zeros(1)
    out = [n]
    for a in arrays:
        a = a[keep]
        s = float(np.max(np.abs(a))) or 1.0
        out += [float(a.min()), float(a.max()), float(np.mean(a / s)) * s,
                float(np.mean(ramp * (a / s))) * s]
    return out


def _points(c):
    """Data points of a collection: its offsets, else the mesh coordinates or path vertices.

    The offsets are the default, not data, when they are one (0, 0) in an identity transform.
    """
    from matplotlib.transforms import IdentityTransform

    offsets = np.ma.asarray(c.get_offsets(), dtype=float).reshape(-1, 2)
    default = isinstance(c.get_offset_transform(), IdentityTransform)
    if len(offsets) != 1 or offsets.any() or not default:
        return offsets
    if hasattr(c, "get_coordinates"):
        return np.asarray(c.get_coordinates(), dtype=float).reshape(-1, 2)
    paths = [path.vertices for path in c.get_paths()]
    return np.concatenate(paths).reshape(-1, 2) if paths else np.empty((0, 2))


def _values(c):
    """Statistic rows of the data a collection carries besides its points.

    The colour values, the masked U and V of a quiver and the u and v of barbs.
    """
    rows = [_stats(a)] if (a := c.get_array()) is not None else []
    if hasattr(c, "Umask"):
        rows += [_stats(np.ma.masked_array(c.U, c.Umask)), _stats(np.ma.masked_array(c.V, c.Umask))]
    elif hasattr(c, "u") and hasattr(c, "v"):
        rows += [_stats(c.u), _stats(c.v)]
    return rows


def _all_axes(axes):
    """The axes and, depth first, their inset and parasite axes; secondary and 3D axes are left out."""
    for ax in axes:
        if type(ax).__name__ == "SecondaryAxis" or ax.name == "3d":
            continue
        yield ax
        yield from _all_axes([*ax.child_axes, *getattr(ax, "parasites", [])])


def summarize(fig):
    """Data summary of a figure, the part of a plot that does not depend on its renderer.

    Per axes, inset and parasite axes included: each line as ``[n, x stats, y stats]``
    over its points finite in both coordinates, in the axis units, so categorical and
    date axes are numbers; each collection the same over its points (`_points`); its
    other data (`_values`) as ``[n, value stats]``; the corners of all patches except
    annotation arrows (bars, histograms) as one ``[n, x stats, y stats]``; each image as
    ``[ny, nx, origin is upper, value stats]`` and its extent as ``[2, x stats, y stats]``.
    The stats of a coordinate are min, max, mean and ramp (`_stats`). Not part of it:
    3D and secondary axes, axis labels, scales, limits, text, colours, artist
    transforms, annotation arrows, the shapes of offset markers and the interior cell
    edges of images. The artists a plot type makes depend on the matplotlib version.
    """
    from matplotlib.patches import FancyArrowPatch

    axes = []
    for ax in _all_axes(fig.axes):
        patches = [p for p in ax.patches if not isinstance(p, FancyArrowPatch)]
        corners = [p.get_patch_transform().transform(p.get_path().vertices) for p in patches]
        images = ax.get_images()
        axes.append(
            {
                "lines": [_stats(*line.get_xydata().T) for line in ax.get_lines()],
                "collections": [_stats(*_points(c).T) for c in ax.collections],
                "values": [row for c in ax.collections for row in _values(c)],
                "patches": [_stats(*np.concatenate(corners).T)] if corners else [],
                "images": [
                    [*np.shape(im.get_array()), 0, 0][:2] + [int(im.origin == "upper")]
                    + _stats(im.get_array())[1:]
                    for im in images
                ],
                "extents": [
                    _stats(*np.reshape(im.get_extent(), (2, 2)))
                    for im in images
                    if im.get_array() is not None
                ],
            }
        )
    return {"v": SUMMARY_VERSION, "axes": axes}


_DESCRIPTION = re.compile(rb"<dc:description>(.*?)</dc:description>", re.DOTALL)


def read_summary(path):
    """Return the data summary a validation plot file carries, or None when it has none.

    Raises ValueError when the text after the last ``summary: `` is not JSON.
    """
    match = _DESCRIPTION.search(Path(path).read_bytes())
    if not match:
        return None
    _, sep, tail = match.group(1).decode("utf-8", "replace").rpartition("summary: ")
    return json.loads(tail) if sep else None


_HEADS = {"lines": 1, "collections": 1, "values": 1, "patches": 1, "images": 3, "extents": 1}
_LABELS = {"lines": "line", "collections": "collection", "values": "value set",
           "patches": "patch set", "images": "image", "extents": "image extent"}
_STATS = ("min", "max", "mean", "ramp")


def compare_summaries(new, old, rtol=SUMMARY_RTOL):
    """List the differences between two data summaries; an empty list when they agree.

    Formats and counts must match. Each statistic of a coordinate must agree within
    `rtol` times the range of the committed coordinate, or a tenth of its largest
    magnitude when that is larger.
    """
    if new.get("v") != old.get("v"):
        return [f"summary format {new.get('v')}, committed {old.get('v')}"]
    if len(new["axes"]) != len(old["axes"]):
        return [f"axes count {len(new['axes'])}, committed {len(old['axes'])}"]
    diffs = []
    for i, (a, b) in enumerate(zip(new["axes"], old["axes"])):
        for key, head in _HEADS.items():
            label, rows, committed = _LABELS[key], a.get(key, []), b.get(key, [])
            if len(rows) != len(committed):
                diffs.append(f"axes {i}: {label} count {len(rows)}, committed {len(committed)}")
                continue
            for j, (x, y) in enumerate(zip(rows, committed)):
                where, count = f"axes {i} {label} {j}", "shape" if head > 1 else "point count"
                if len(x) != len(y) or (len(y) - head) % 4:
                    diffs.append(f"{where}: {len(x)} entries, committed {len(y)}")
                elif x[:head] != y[:head]:
                    diffs.append(f"{where}: {count} {x[:head]}, committed {y[:head]}")
                else:
                    diffs += _compare_stats(where, x[head:], y[head:], rtol)
    return diffs


def _compare_stats(where, got, want, rtol):
    """Differences between the statistics of the coordinates of one entry.

    Values are halved before they are subtracted, so a range near the largest float
    does not overflow.
    """
    diffs = []
    for c, k in zip("xy" if len(want) > 4 else "v", range(0, len(want), 4)):
        lo, hi = want[k], want[k + 1]
        half = 0.0 if lo is None else max(hi / 2 - lo / 2, 0.05 * max(abs(lo), abs(hi)))
        for stat, g, w in zip(_STATS, got[k : k + 4], want[k : k + 4]):
            if g != w and (None in (g, w) or not abs(g / 2 - w / 2) <= rtol * half):
                diffs.append(f"{where} {c} {stat}: {g!r}, committed {w!r}")
    return diffs
