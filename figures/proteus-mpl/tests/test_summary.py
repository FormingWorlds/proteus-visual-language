"""Tests for the data summary that a validation plot carries and its comparison."""

import math

import matplotlib.pyplot as plt
import numpy as np
import pytest

from proteus_mpl import validation as v


def line_figure(y=(1.0, 0.0, 1.0)):
    fig, ax = plt.subplots(figsize=(3, 2))
    ax.plot([0.0, 1.0, 2.0], list(y))
    return fig


def test_summary_of_a_line_holds_count_and_ranges():
    fig = line_figure()
    try:
        summary = v.summarize(fig)
    finally:
        plt.close(fig)
    (line,) = summary["axes"][0]["lines"]
    n, xmin, xmax, xmean, ymin, ymax, ymean = line
    assert n == 3
    assert (xmin, xmax, xmean) == (0.0, 2.0, 1.0)
    assert (ymin, ymax) == (0.0, 1.0)
    assert ymean == pytest.approx(2.0 / 3.0, rel=1e-9)


def test_summary_skips_points_that_are_not_finite():
    fig, ax = plt.subplots()
    ax.plot([0.0, 1.0, 2.0, 3.0], [1.0, np.nan, 3.0, np.inf])
    try:
        (line,) = v.summarize(fig)["axes"][0]["lines"]
    finally:
        plt.close(fig)
    assert line[0] == 2
    assert line[4:6] == [1.0, 3.0]


def test_summary_counts_scatter_points_and_image_pixels():
    fig, (a, b) = plt.subplots(1, 2)
    a.scatter([0.0, 1.0], [2.0, 4.0])
    b.imshow(np.arange(6.0).reshape(2, 3))
    try:
        summary = v.summarize(fig)
    finally:
        plt.close(fig)
    (coll,) = summary["axes"][0]["collections"]
    assert coll[0] == 2 and coll[4:7] == [2.0, 4.0, 3.0]
    (image,) = summary["axes"][1]["images"]
    assert image[:2] == [2, 3] and image[2:] == [0.0, 5.0, 2.5]


def test_identical_summaries_compare_equal():
    fig = line_figure()
    try:
        s = v.summarize(fig)
    finally:
        plt.close(fig)
    assert v.compare_summaries(s, s) == []


def test_a_change_below_the_tolerance_passes_and_above_it_fails():
    base = {"axes": [{"lines": [[3, 0.0, 2.0, 1.0, 0.0, 1.0, 0.5]], "collections": [], "images": []}]}
    small = {"axes": [{"lines": [[3, 0.0, 2.0, 1.0, 0.0, 1.0, 0.5 + 0.1 * v.SUMMARY_RTOL]]}]}
    large = {"axes": [{"lines": [[3, 0.0, 2.0, 1.0, 0.0, 1.0, 0.5 + 10 * v.SUMMARY_RTOL]]}]}
    for d in (small, large):
        d["axes"][0].update(collections=[], images=[])
    assert v.compare_summaries(small, base) == []
    (diff,) = v.compare_summaries(large, base)
    assert "axes 0" in diff and "line 0" in diff


def test_a_mean_near_zero_is_compared_on_the_scale_of_its_range():
    base = {"axes": [{"lines": [[3, -1.0, 1.0, 0.0, -1.0, 1.0, 0.0]], "collections": [], "images": []}]}
    near = {"axes": [{"lines": [[3, -1.0, 1.0, 1e-12, -1.0, 1.0, 0.0]], "collections": [], "images": []}]}
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
    base = {"axes": [{"lines": [[3, 0.0, 2.0, 1.0, 0.0, 1.0, 0.5]], "collections": [], "images": []}]}
    new = {"axes": [{"lines": [list(base["axes"][0]["lines"][0])], "collections": [], "images": []}]}
    change(new)
    diffs = v.compare_summaries(new, base)
    assert diffs and word in diffs[0]


@pytest.mark.parametrize("kind", ["line", "map"])
def test_saved_files_carry_the_summary(tmp_path, kind):
    light, dark = v.save(line_figure, "case", tmp_path, kind, test_id="t", command="c")
    fig = line_figure()
    try:
        expected = v.summarize(fig)
    finally:
        plt.close(fig)
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
    assert line[6] == pytest.approx(sum(y) / 3.0, rel=1e-12)
