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
