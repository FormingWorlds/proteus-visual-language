"""Tests for the data summary that a validation plot carries and its comparison."""

import json
import math

import matplotlib.pyplot as plt
import numpy as np
import pytest

from proteus_mpl import validation as v


def summary_of(fig):
    """Data summary of a figure, which is then closed."""
    try:
        return v.summarize(fig)
    finally:
        plt.close(fig)


def line_figure(y=(1.0, 0.0, 1.0)):
    fig, ax = plt.subplots(figsize=(3, 2))
    ax.plot([0.0, 1.0, 2.0], list(y))
    return fig


def test_summary_of_a_line_holds_count_and_ranges():
    fig = line_figure()
    summary = summary_of(fig)
    (line,) = summary["axes"][0]["lines"]
    n, xmin, xmax, xmean, _, ymin, ymax, ymean, _ = line
    assert n == 3
    assert (xmin, xmax, xmean) == (0.0, 2.0, 1.0)
    assert (ymin, ymax) == (0.0, 1.0)
    assert ymean == pytest.approx(2.0 / 3.0, rel=1e-9)


def test_summary_skips_points_that_are_not_finite():
    fig, ax = plt.subplots()
    ax.plot([0.0, 1.0, 2.0, 3.0], [1.0, np.nan, 3.0, np.inf])
    (line,) = summary_of(fig)["axes"][0]["lines"]
    assert line[0] == 2
    assert line[5:7] == [1.0, 3.0]


def test_summary_counts_scatter_points_and_image_pixels():
    fig, (a, b) = plt.subplots(1, 2)
    a.scatter([0.0, 1.0], [2.0, 4.0])
    b.imshow(np.arange(6.0).reshape(2, 3))
    summary = summary_of(fig)
    (coll,) = summary["axes"][0]["collections"]
    assert coll[0] == 2 and coll[5:8] == [2.0, 4.0, 3.0]
    (image,) = summary["axes"][1]["images"]
    assert image[:2] == [2, 3] and image[2:5] == [0.0, 5.0, 2.5]


def one_axes(*lines):
    """Summary of one axes holding the given lines."""
    return {"v": 1, "axes": [{"lines": [list(x) for x in lines]}]}


def test_identical_summaries_compare_equal():
    fig = line_figure()
    s = summary_of(fig)
    assert v.compare_summaries(s, s) == []


def test_a_change_below_the_tolerance_passes_and_above_it_fails():
    base = one_axes([3, 0.0, 2.0, 1.0, 0.0, 0.0, 1.0, 0.5, 0.0])
    small = one_axes([3, 0.0, 2.0, 1.0, 0.0, 0.0, 1.0, 0.5 + 0.1 * v.SUMMARY_RTOL, 0.0])
    large = one_axes([3, 0.0, 2.0, 1.0, 0.0, 0.0, 1.0, 0.5 + 10 * v.SUMMARY_RTOL, 0.0])
    assert v.compare_summaries(small, base) == []
    (diff,) = v.compare_summaries(large, base)
    assert "axes 0" in diff and "line 0" in diff


def test_a_mean_near_zero_is_compared_on_the_scale_of_its_range():
    base = one_axes([3, -1.0, 1.0, 0.0, 0.0, -1.0, 1.0, 0.0, 0.0])
    near = one_axes([3, -1.0, 1.0, 1e-12, 0.0, -1.0, 1.0, 0.0, 0.0])
    assert v.compare_summaries(near, base) == []


@pytest.mark.parametrize(
    "change, word",
    [
        (lambda s: s["axes"][0]["lines"][0].__setitem__(0, 4), "point count"),
        (lambda s: s["axes"][0]["lines"].append(list(s["axes"][0]["lines"][0])), "line count"),
        (lambda s: s["axes"].append({"lines": [], "collections": [], "images": []}), "axes count"),
    ],
)
def test_a_changed_count_fails(change, word):
    base = one_axes([3, 0.0, 2.0, 1.0, 0.0, 0.0, 1.0, 0.5, 0.0])
    new = one_axes(base["axes"][0]["lines"][0])
    change(new)
    diffs = v.compare_summaries(new, base)
    assert diffs and word in diffs[0]


@pytest.mark.parametrize("kind", ["line", "map"])
def test_saved_files_carry_the_summary(tmp_path, kind):
    light, dark = v.save(line_figure, "case", tmp_path, kind, test_id="t", command="c")
    fig = line_figure()
    expected = summary_of(fig)
    assert v.read_summary(light) == expected
    assert v.read_summary(dark) == expected


def test_a_file_without_summary_reads_as_none(tmp_path):
    light, _ = v.save(line_figure, "case", tmp_path)
    text = light.read_text()
    start = text.index("summary: ")
    end = text.index("</dc:description>", start)
    light.write_text(text[:start] + text[end:])
    assert v.read_summary(light) is None


def test_summary_values_survive_the_file_to_full_precision(tmp_path):
    y = (math.pi, math.e, 1.0 / 3.0)
    (light, _) = v.save(lambda: line_figure(y), "case", tmp_path)
    (line,) = v.read_summary(light)["axes"][0]["lines"]
    assert line[7] == pytest.approx(sum(y) / 3.0, rel=1e-12)


def test_a_file_without_description_reads_as_none(tmp_path):
    path = tmp_path / "plain.svg"
    path.write_text('<svg xmlns="http://www.w3.org/2000/svg"/>')
    assert v.read_summary(path) is None


def two_figures(draw, a, b):
    """Summaries of the same drawing call with data `a` and with data `b`."""
    out = []
    for data in (a, b):
        fig, ax = plt.subplots()
        draw(ax, data)
        out.append(summary_of(fig))
    return out


def test_categorical_and_datetime_axes_are_summarized():
    import datetime

    fig, (a, b) = plt.subplots(1, 2)
    a.plot(["a", "b", "c"], [1.0, 2.0, 3.0])
    b.plot([datetime.datetime(2020, 1, 1), datetime.datetime(2021, 1, 1)], [1.0, 2.0])
    s = summary_of(fig)
    assert s["axes"][0]["lines"][0][0] == 3
    assert s["axes"][1]["lines"][0][0] == 2


@pytest.mark.parametrize(
    "draw",
    [
        lambda ax, k: ax.pcolormesh(k * np.arange(6.0).reshape(2, 3)),
        lambda ax, k: ax.fill_between([0.0, 1.0, 2.0], [0.0, k, 0.0], [1.0, 2.0, 1.0]),
        lambda ax, k: ax.bar([0.0, 1.0], [3.0, 3.0 + k]),
        lambda ax, k: ax.errorbar([0.0, 1.0], [1.0, 2.0], yerr=[0.1, 0.1 * k]),
        lambda ax, k: ax.contourf(k * np.arange(9.0).reshape(3, 3) + np.eye(3)),
    ],
    ids=["pcolormesh", "fill_between", "bar", "errorbar", "contourf"],
)
def test_changed_data_of_other_artists_is_found(draw):
    new, old = two_figures(draw, 2.0, 1.0)
    assert v.compare_summaries(new, old)


def test_a_reversed_series_is_found():
    y = np.linspace(0.0, 1.0, 50) ** 2
    new, old = two_figures(lambda ax, d: ax.plot(np.linspace(0.0, 1.0, 50), d), y[::-1], y)
    assert v.compare_summaries(new, old)


def test_the_tolerance_follows_the_range_of_an_offset_coordinate():
    x = 1e6 + np.linspace(0.0, 1.0, 5)
    new, old = two_figures(lambda ax, d: ax.plot(d, [0.0, 1.0, 2.0, 3.0, 4.0]), x + 0.9, x)
    assert v.compare_summaries(new, old)


@pytest.mark.parametrize(
    "y, shift, stale",
    [
        ([0.0, 1e-3, 2e-3], 1e-9, False),
        ([0.0, 1e-3, 2e-3], 4e-9, True),
        ([10.0, 11.0, 12.0], 1e-6, False),
        ([10.0, 11.0, 12.0], 8e-6, True),
        ([1e6, 1e6 + 1.0, 1e6 + 2.0], 0.05, False),
        ([1e6, 1e6 + 1.0, 1e6 + 2.0], 0.2, True),
    ],
)
def test_a_shift_is_compared_to_1e_6_of_the_range_or_a_tenth_of_the_magnitude(y, shift, stale):
    y = np.array(y)
    new, old = two_figures(lambda ax, d: ax.plot([0.0, 1.0, 2.0], d), y + shift, y)
    assert bool(v.compare_summaries(new, old)) is stale


def test_a_masked_scatter_point_is_left_out():
    fig, ax = plt.subplots()
    ax.scatter(np.ma.masked_array([0.0, 1e20, 2.0], [0, 1, 0]), [1.0, 2.0, 3.0])
    (points,) = summary_of(fig)["axes"][0]["collections"]
    assert points[0] == 2 and points[2] == 2.0


def test_a_large_mean_does_not_overflow():
    fig, ax = plt.subplots()
    ax.plot([0.0, 1.0], [1e308, 1.5e308])
    (line,) = summary_of(fig)["axes"][0]["lines"]
    assert all(math.isfinite(x) for x in line[1:])


def test_the_summary_names_its_format():
    fig, ax = plt.subplots()
    ax.plot([0.0, 1.0])
    assert summary_of(fig)["v"] == v.SUMMARY_VERSION


def test_a_test_id_with_the_summary_label_reads_back(tmp_path):
    light, _ = v.save(line_figure, "case", tmp_path, test_id="t.py::test_x[summary: a<b&c]")
    fig = line_figure()
    assert v.read_summary(light) == summary_of(fig)


def test_an_unreadable_summary_raises_value_error(tmp_path):
    path = tmp_path / "case.svg"
    path.write_text("<svg><dc:description>Executive summary: foo</dc:description></svg>")
    with pytest.raises(ValueError):
        v.read_summary(path)


def test_compare_finds_changed_images_missing_values_and_short_rows():
    row = [2, 0.0, 1.0, 0.5, 0.0, 0.0, 1.0, 0.5, 0.0]
    base = {"v": 1, "axes": [{"lines": [row], "images": [[2, 2, 0.0, 3.0, 1.5, 0.0]]}]}
    image = json.loads(json.dumps(base))
    image["axes"][0]["images"][0][3] = 4.0
    missing = json.loads(json.dumps(base))
    missing["axes"][0]["lines"][0][2] = None
    short = json.loads(json.dumps(base))
    short["axes"][0]["lines"][0] = row[:5]
    for new in (image, missing, short):
        assert v.compare_summaries(new, base)


def test_the_stale_message_names_the_quantity():
    new, old = two_figures(lambda ax, d: ax.plot([0.0, 1.0, 2.0], d), [0.0, 1.0, 3.0], [0.0, 1.0, 2.0])
    assert any("y max" in d for d in v.compare_summaries(new, old))


def test_a_line_without_finite_points_has_no_statistics():
    fig, ax = plt.subplots()
    ax.plot([np.nan, np.nan], [1.0, 2.0])
    assert summary_of(fig)["axes"][0]["lines"] == [[0] + [None] * 8]


def test_summaries_of_two_formats_differ():
    assert v.compare_summaries({"v": 2, "axes": []}, {"v": 1, "axes": []}) == ["summary format 2, committed 1"]
