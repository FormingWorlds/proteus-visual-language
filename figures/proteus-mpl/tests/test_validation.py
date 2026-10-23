"""Tests for proteus_mpl.validation.save."""

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pytest

from proteus_mpl import validation
from proteus_mpl.validation import MAX_BYTES, save


def line_figure():
    """A small line plot with two series, labels and a legend."""
    fig, ax = plt.subplots(figsize=(4, 3))
    x = np.linspace(0.0, 10.0, 50)
    ax.plot(x, np.sin(x), label="model")
    ax.plot(x[::5], np.sin(x[::5]), "o", label="reference")
    ax.set_xlabel("Time [Myr]")
    ax.set_ylabel("T [K]")
    ax.legend()
    return fig


def map_figure():
    """A 200 x 200 smooth field drawn with pcolormesh."""
    fig, ax = plt.subplots(figsize=(4, 3))
    y, x = np.mgrid[0:1:200j, 0:1:200j]
    ax.pcolormesh(np.sin(6 * x) * np.cos(4 * y))
    return fig


def vector_mesh_figure():
    """A 200 x 200 random pcolormesh: far above the cap as SVG and as AVIF."""
    fig, ax = plt.subplots(figsize=(6, 4.5))
    ax.pcolormesh(np.random.default_rng(0).random((200, 200)))
    return fig


def rasterized_mesh_figure():
    """The smooth field as a rasterized element inside an SVG."""
    fig, ax = plt.subplots(figsize=(3, 2))
    y, x = np.mgrid[0:1:200j, 0:1:200j]
    ax.pcolormesh(x + y, rasterized=True)
    return fig


@pytest.mark.parametrize(
    "kind, factory, suffix",
    [("line", line_figure, "svg"), ("map", map_figure, "avif")],
)
def test_two_saves_give_the_same_bytes(tmp_path, kind, factory, suffix):
    first = save(factory, "case", tmp_path / "a", kind=kind)
    second = save(factory, "case", tmp_path / "b", kind=kind)
    assert [p.name for p in first] == [f"case.{suffix}", f"case_dark.{suffix}"]
    for a, b in zip(first, second):
        assert a.read_bytes() == b.read_bytes()


@pytest.mark.parametrize("kind, factory", [("line", line_figure), ("map", map_figure)])
def test_light_and_dark_files_differ(tmp_path, kind, factory):
    light, dark = save(factory, "case", tmp_path, kind=kind)
    assert light.read_bytes() != dark.read_bytes()


def four_series_figure():
    """A 6 x 4.5 in line plot: 3 lines of 200 points, 20 markers, labels and a legend."""
    fig, ax = plt.subplots(figsize=(6, 4.5))
    x = np.linspace(0.0, 10.0, 200)
    for k in range(3):
        ax.plot(x, np.sin(x + k), label=f"case {k}")
    ax.plot(x[::10], np.sin(x[::10]) + 0.05, "o", label="reference")
    ax.set_xlabel("Time [Myr]")
    ax.set_ylabel("Surface temperature [K]")
    ax.legend()
    return fig


def test_four_series_line_plot_fits_the_cap(tmp_path):
    for path in save(four_series_figure, "case", tmp_path):
        assert path.stat().st_size <= MAX_BYTES


def test_svg_carries_no_date(tmp_path):
    light, _ = save(line_figure, "case", tmp_path)
    assert b"<dc:date>" not in light.read_bytes()


def test_caller_rcparams_and_figures_unchanged(tmp_path):
    with matplotlib.rc_context({"lines.linewidth": 7.25, "axes.facecolor": "#123456"}):
        before = dict(matplotlib.rcParams)
        open_before = plt.get_fignums()
        save(line_figure, "case", tmp_path)
        save(map_figure, "map", tmp_path, kind="map")
        assert dict(matplotlib.rcParams) == before
        assert plt.get_fignums() == open_before


def test_vector_mesh_above_cap_is_refused(tmp_path):
    with pytest.raises(ValueError, match=r"case\.svg: \d+ B, above the 60000 B cap") as err:
        save(vector_mesh_figure, "case", tmp_path)
    size = int(str(err.value).split(": ")[1].split(" B")[0])
    assert size > 1_000_000
    assert list(tmp_path.iterdir()) == []


def test_cap_refuses_a_file_one_byte_above(tmp_path, monkeypatch):
    light, _ = save(line_figure, "case", tmp_path / "ok")
    size = light.stat().st_size
    monkeypatch.setattr(validation, "MAX_BYTES", size)
    save(line_figure, "case", tmp_path / "at")
    monkeypatch.setattr(validation, "MAX_BYTES", size - 1)
    with pytest.raises(ValueError, match=f"case.svg: {size} B, above the {size - 1} B cap"):
        save(line_figure, "case", tmp_path / "above")


def test_failed_save_keeps_earlier_files(tmp_path):
    save(line_figure, "case", tmp_path)
    kept = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    with pytest.raises(ValueError):
        save(vector_mesh_figure, "case", tmp_path)
    assert {p.name: p.read_bytes() for p in tmp_path.iterdir()} == kept


def test_rasterized_element_in_svg_under_cap_passes(tmp_path):
    light, dark = save(rasterized_mesh_figure, "case", tmp_path)
    for path in (light, dark):
        data = path.read_bytes()
        assert b"<image" in data
        assert len(data) <= MAX_BYTES


@pytest.mark.parametrize("kind, factory", [("line", line_figure), ("map", map_figure)])
def test_stamp_is_written_and_stays_deterministic(tmp_path, kind, factory):
    stamp = {"test_id": "tests/test_x.py::test_y", "command": "pytest tests/test_x.py::test_y"}
    first = save(factory, "case", tmp_path / "a", kind=kind, **stamp)
    second = save(factory, "case", tmp_path / "b", kind=kind, **stamp)
    for a, b in zip(first, second):
        data = a.read_bytes()
        assert b"test: tests/test_x.py::test_y" in data
        assert b"command: pytest tests/test_x.py::test_y" in data
        assert data == b.read_bytes()


def test_avif_stamp_is_the_xmp_description(tmp_path):
    from PIL import Image

    light, _ = save(map_figure, "case", tmp_path, kind="map", test_id="t::x", command="c")
    xmp = Image.open(light).info["xmp"]
    assert b"<dc:description>test: t::x; command: c</dc:description>" in xmp


def test_stamp_escapes_markup(tmp_path):
    light, _ = save(line_figure, "case", tmp_path, kind="map", test_id="t[a<b&c]")
    assert b"t[a&lt;b&amp;c]" in light.read_bytes()


def test_outdir_is_created(tmp_path):
    out = tmp_path / "docs" / "assets" / "validation"
    save(line_figure, "case", out)
    assert sorted(p.name for p in out.iterdir()) == ["case.svg", "case_dark.svg"]


@pytest.mark.parametrize(
    "kwargs, error, match",
    [
        ({"kind": "bar"}, ValueError, "kind must be 'line' or 'map'"),
        ({"name": "a/b"}, ValueError, "plain file stem"),
        ({"name": ""}, ValueError, "plain file stem"),
        ({"name": ".."}, ValueError, "plain file stem"),
        ({"name": "case_dark"}, ValueError, "must not end in '_dark'"),
        ({"name": "case_DARK"}, ValueError, "must not end in '_dark'"),
        ({"name": "_x"}, ValueError, "plain file stem"),
        ({"name": "-x"}, ValueError, "plain file stem"),
        ({"name": 3}, ValueError, "plain file stem"),
        ({"name": None}, ValueError, "plain file stem"),
        ({"fig_factory": None}, TypeError, "fig_factory must be callable"),
        ({"fig_factory": lambda: None}, TypeError, "returned NoneType"),
    ],
)
def test_invalid_arguments_are_refused(tmp_path, kwargs, error, match):
    args = {"fig_factory": line_figure, "name": "case", "outdir": tmp_path}
    args.update(kwargs)
    with pytest.raises(error, match=match):
        save(**args)
    assert list(tmp_path.iterdir()) == []


def test_map_is_the_matplotlib_png_encoded_at_quality_80(tmp_path):
    import io

    from PIL import Image

    import proteus_mpl

    light, _ = save(map_figure, "case", tmp_path, kind="map")
    with matplotlib.rc_context():
        proteus_mpl.use("light")
        fig = map_figure()
        png = io.BytesIO()
        fig.savefig(png, format="png", dpi=150)
        plt.close(fig)
    expected = io.BytesIO()
    Image.open(png).convert("RGB").save(
        expected, "AVIF", quality=80, speed=6, max_threads=1, codec="aom", subsampling="4:2:0"
    )
    assert light.read_bytes() == expected.getvalue()


def test_svg_creator_carries_no_matplotlib_version(tmp_path):
    light, _ = save(line_figure, "case", tmp_path)
    data = light.read_bytes()
    assert b"<dc:title>proteus-mpl</dc:title>" in data
    assert matplotlib.__version__.encode() not in data


def test_dark_files_are_drawn_on_void(tmp_path):
    from PIL import Image

    light, dark = save(line_figure, "case", tmp_path)
    assert b"#05070b" in dark.read_bytes().lower()
    assert b"#05070b" not in light.read_bytes().lower()
    light, dark = save(map_figure, "map", tmp_path, kind="map")
    assert max(Image.open(dark).convert("RGB").getpixel((0, 0))) < 20
    assert min(Image.open(light).convert("RGB").getpixel((0, 0))) > 230


def test_map_above_cap_is_refused_with_a_map_hint(tmp_path):
    with pytest.raises(ValueError, match=r"case\.avif: \d+ B, above the 60000 B cap") as err:
        save(vector_mesh_figure, "case", tmp_path, kind="map")
    assert "kind='map'" not in str(err.value)
    assert "smoother field" in str(err.value)
    assert list(tmp_path.iterdir()) == []


def test_line_cap_hint_names_map_before_rasterized(tmp_path):
    with pytest.raises(ValueError) as err:
        save(vector_mesh_figure, "case", tmp_path)
    message = str(err.value)
    assert message.endswith(validation._HINTS["line"])
    assert message.index("plot fewer points") < message.index("kind='map'")
    assert message.index("kind='map'") < message.index("rasterized=True")


@pytest.mark.parametrize("returns_axes", [False, True])
def test_failing_factory_leaves_no_open_figure(tmp_path, returns_axes):
    def factory():
        _fig, ax = plt.subplots()
        if returns_axes:
            return ax
        raise RuntimeError("factory failed")

    before = plt.get_fignums()
    with pytest.raises((RuntimeError, TypeError)):
        save(factory, "case", tmp_path)
    assert plt.get_fignums() == before


@pytest.mark.parametrize("name", ["case-1", "v1.5", "dark"])
def test_hyphen_and_dot_in_name_are_allowed(tmp_path, name):
    paths = save(line_figure, name, tmp_path)
    assert [p.name for p in paths] == [f"{name}.svg", f"{name}_dark.svg"]


def test_stamp_joins_test_and_command_with_a_semicolon(tmp_path):
    light, _ = save(line_figure, "case", tmp_path, test_id="t::x", command="pytest t::x")
    assert b"test: t::x; command: pytest t::x" in light.read_bytes()


def test_figure_open_before_save_stays_open(tmp_path):
    fig = plt.figure()
    try:
        save(line_figure, "case", tmp_path)
        assert fig.number in plt.get_fignums()
    finally:
        plt.close(fig)


def test_map_is_encoded_from_rgb_with_the_fixed_encoder_settings(tmp_path, monkeypatch):
    from PIL import Image

    calls = []
    original = Image.Image.save

    def spy(self, fp, format=None, **params):
        calls.append((self.mode, format, params))
        return original(self, fp, format, **params)

    monkeypatch.setattr(Image.Image, "save", spy)
    save(map_figure, "case", tmp_path, kind="map")
    avif = [call for call in calls if call[1] == "AVIF"]
    assert len(avif) == 2
    for mode, _, params in avif:
        assert mode == "RGB"
        assert params["quality"] == 80
        assert {k: params[k] for k in validation.AVIF_OPTIONS} == {
            "speed": 6,
            "max_threads": 1,
            "codec": "aom",
            "subsampling": "4:2:0",
        }


def test_outdir_may_be_a_string(tmp_path):
    paths = save(line_figure, "case", str(tmp_path / "out"))
    assert [p.name for p in paths] == ["case.svg", "case_dark.svg"]


def dark_only_mesh_figure():
    """A line plot under the light theme, a dense vector mesh under the dark theme."""
    dark = matplotlib.colors.to_hex(matplotlib.rcParams["figure.facecolor"]) == "#05070b"
    return vector_mesh_figure() if dark else line_figure()


def test_dark_file_alone_over_cap_is_refused(tmp_path):
    with pytest.raises(ValueError, match=r"case_dark\.svg: \d+ B, above the 60000 B cap"):
        save(dark_only_mesh_figure, "case", tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_svg_text_is_drawn_as_paths(tmp_path):
    for path in save(line_figure, "case", tmp_path):
        data = path.read_bytes()
        assert b"<text" not in data
        assert b"<path" in data


SECOND_PROCESS = """
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, sys.argv[2])
from proteus_mpl.validation import save

def figure():
    fig, ax = plt.subplots(figsize=(3, 2))
    ax.plot([0, 1, 2], [1, 0, 1], label="a")
    ax.legend()
    return fig

save(figure, "case", sys.argv[1])
"""


def test_svg_bytes_match_across_processes(tmp_path):
    import os
    import subprocess
    import sys
    from pathlib import Path

    src = str(Path(validation.__file__).parents[1])
    outs = []
    for seed in ("1", "2"):
        out = tmp_path / seed
        env = dict(os.environ, PYTHONHASHSEED=seed)
        subprocess.run(
            [sys.executable, "-c", SECOND_PROCESS, str(out), src], env=env, check=True, timeout=120
        )
        outs.append([p.read_bytes() for p in sorted(out.iterdir())])
    assert len(outs[0]) == 2
    assert outs[0] == outs[1]


def test_factory_returning_an_open_figure_is_refused(tmp_path):
    caller = plt.figure("case")
    try:
        with pytest.raises(ValueError, match="was open before"):
            save(lambda: plt.figure("case"), "case", tmp_path)
        assert caller.number in plt.get_fignums()
        assert list(tmp_path.iterdir()) == []
    finally:
        plt.close(caller)


@pytest.mark.parametrize("kind", ["line", "map"])
def test_stamp_drops_characters_xml_cannot_hold(tmp_path, kind):
    import xml.etree.ElementTree as ET

    from PIL import Image

    factory = line_figure if kind == "line" else map_figure
    light, _ = save(factory, "case", tmp_path, kind=kind, test_id="t\x00\x0b\x1b\ufffe\ud800x")
    xml = light.read_bytes() if kind == "line" else Image.open(light).info["xmp"]
    ET.fromstring(xml)
    assert b"test: tx" in xml


@pytest.mark.parametrize("pyplot", [True, False])
def test_factory_returning_one_figure_for_both_themes_is_refused(tmp_path, pyplot):
    from matplotlib.figure import Figure

    cache = []

    def factory():
        if not cache:
            cache.append(plt.figure() if pyplot else Figure())
        return cache[0]

    with pytest.raises(ValueError, match="same figure for both themes"):
        save(factory, "case", tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_failed_second_part_write_keeps_the_previous_pair(tmp_path, monkeypatch):
    from pathlib import Path

    before = {p.name: p.read_bytes() for p in save(line_figure, "case", tmp_path)}
    real = Path.write_bytes

    def write_bytes(self, data):
        if self.name == "case_dark.svg.part":
            raise OSError("disk full")
        return real(self, data)

    monkeypatch.setattr(Path, "write_bytes", write_bytes)
    with pytest.raises(OSError, match="disk full"):
        save(map_figure_as_line, "case", tmp_path)
    assert {p.name: p.read_bytes() for p in tmp_path.iterdir()} == before


def map_figure_as_line():
    """A different small line plot, so a rewrite would change the bytes."""
    fig, ax = plt.subplots(figsize=(4, 3))
    ax.plot([0, 1, 2], [2, 0, 2])
    return fig


def failing_placement(monkeypatch, nth, exc=OSError):
    """Make the nth move of a .part file into place fail with exc."""
    real = validation.os.replace
    calls = []

    def replace(src, dst):
        if str(src).endswith(".part"):
            calls.append(dst)
            if len(calls) == nth:
                raise exc("disk full")
        return real(src, dst)

    monkeypatch.setattr(validation.os, "replace", replace)


def listing(folder):
    """Map each entry of folder to its bytes, or None for a subfolder."""
    return {p.name: None if p.is_dir() else p.read_bytes() for p in folder.iterdir()}


def listing_of(paths):
    return {p.name: p.read_bytes() for p in paths}


def test_targets_exist_during_every_placement(tmp_path, monkeypatch):
    save(line_figure, "case", tmp_path)
    real = validation.os.replace
    seen = []

    def replace(src, dst):
        seen.append(sorted(p.name for p in tmp_path.iterdir() if p.suffix == ".svg"))
        return real(src, dst)

    monkeypatch.setattr(validation.os, "replace", replace)
    save(map_figure_as_line, "case", tmp_path)
    assert seen and all(names == ["case.svg", "case_dark.svg"] for names in seen)


def test_folder_at_a_target_name_is_refused(tmp_path):
    (tmp_path / "case.svg").mkdir()
    (tmp_path / "case.svg" / "keep.txt").write_text("keep")
    with pytest.raises(IsADirectoryError, match=r"case\.svg"):
        save(line_figure, "case", tmp_path)
    assert sorted(p.name for p in tmp_path.iterdir()) == ["case.svg"]
    assert (tmp_path / "case.svg" / "keep.txt").read_text() == "keep"


def test_symlink_to_a_folder_at_a_target_name_is_replaced(tmp_path):
    (tmp_path / "elsewhere").mkdir()
    (tmp_path / "case.svg").symlink_to(tmp_path / "elsewhere")
    save(line_figure, "case", tmp_path)
    assert not (tmp_path / "case.svg").is_symlink()
    assert (tmp_path / "case.svg").read_bytes().startswith(b"<?xml")


@pytest.mark.parametrize("exc", [OSError, KeyboardInterrupt])
def test_failed_first_placement_keeps_the_previous_pair(tmp_path, monkeypatch, exc):
    save(line_figure, "case", tmp_path)
    before = listing(tmp_path)
    failing_placement(monkeypatch, 1, exc)
    with pytest.raises(exc, match="disk full"):
        save(map_figure_as_line, "case", tmp_path)
    assert listing(tmp_path) == before


@pytest.mark.parametrize("exc", [OSError, KeyboardInterrupt])
def test_failed_second_placement_leaves_new_light_beside_old_dark(tmp_path, monkeypatch, exc):
    save(line_figure, "case", tmp_path)
    before = listing(tmp_path)
    new = listing_of(save(map_figure_as_line, "case", tmp_path / "new"))
    failing_placement(monkeypatch, 2, exc)
    with pytest.raises(exc, match="disk full"):
        save(map_figure_as_line, "case", tmp_path)
    after = listing(tmp_path)
    assert after.pop("new") is None
    assert after == {"case.svg": new["case.svg"], "case_dark.svg": before["case_dark.svg"]}


def test_failed_placement_in_a_new_folder_leaves_no_part(tmp_path, monkeypatch):
    failing_placement(monkeypatch, 1)
    with pytest.raises(OSError, match="disk full"):
        save(line_figure, "case", tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_success_leaves_no_part(tmp_path):
    save(line_figure, "case", tmp_path)
    save(map_figure_as_line, "case", tmp_path)
    assert sorted(p.name for p in tmp_path.iterdir()) == ["case.svg", "case_dark.svg"]


def test_failed_first_placement_keeps_symlinks(tmp_path, monkeypatch):
    import os

    store, out = tmp_path / "store", tmp_path / "out"
    first = save(line_figure, "case", store)
    out.mkdir()
    for p in first:
        (out / p.name).symlink_to(p)
    failing_placement(monkeypatch, 1)
    with pytest.raises(OSError, match="disk full"):
        save(map_figure_as_line, "case", out)
    for p in first:
        assert os.readlink(out / p.name) == str(p)
    assert sorted(p.name for p in out.iterdir()) == ["case.svg", "case_dark.svg"]


def test_folder_at_the_dark_name_is_refused_before_any_write(tmp_path):
    save(line_figure, "case", tmp_path)
    (tmp_path / "case_dark.svg").unlink()
    (tmp_path / "case_dark.svg").mkdir()
    before = listing(tmp_path)
    with pytest.raises(IsADirectoryError, match=r"case_dark\.svg: a folder"):
        save(map_figure_as_line, "case", tmp_path)
    assert listing(tmp_path) == before
