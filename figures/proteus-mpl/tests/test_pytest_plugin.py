"""Tests for the validation_plot fixture and the --validation-plots option."""

import pytest

CASE = """
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def factory():
    fig, ax = plt.subplots(figsize=(3, 2))
    ax.plot([0, 1, 2], [1, 0, 1])
    return fig


def test_case(validation_plot):
    written = validation_plot(factory, "case")
    print("WRITTEN", [p.name for p in written])


def test_factory_not_called_without_option(validation_plot, request):
    def boom():
        raise RuntimeError("factory called")

    if request.config.getoption("validation_plots") is None:
        assert validation_plot(boom, "boom") == []
"""


@pytest.fixture
def case(pytester):
    pytester.makepyfile(test_case=CASE)
    return pytester


def files(root):
    return sorted(str(p.relative_to(root)) for p in root.rglob("*.svg"))


def test_without_option_writes_nothing(case):
    result = case.runpytest("-s")
    result.assert_outcomes(passed=2)
    result.stdout.fnmatch_lines(["*WRITTEN []*"])
    assert files(case.path) == []


def test_option_alone_writes_to_default_dir(case):
    result = case.runpytest("-s", "--validation-plots", "-k", "test_case")
    result.assert_outcomes(passed=1, deselected=1)
    assert files(case.path) == [
        "docs/assets/validation/case.svg",
        "docs/assets/validation/case_dark.svg",
    ]


def test_option_with_relative_dir(case):
    result = case.runpytest("--validation-plots=out/plots", "-k", "test_case")
    result.assert_outcomes(passed=1, deselected=1)
    assert files(case.path) == ["out/plots/case.svg", "out/plots/case_dark.svg"]


def test_option_with_absolute_dir(case, tmp_path_factory):
    out = tmp_path_factory.mktemp("abs")
    result = case.runpytest(f"--validation-plots={out}", "-k", "test_case")
    result.assert_outcomes(passed=1, deselected=1)
    assert files(out) == ["case.svg", "case_dark.svg"]
    assert files(case.path) == []


def test_stamp_names_test_and_command(case):
    case.runpytest("--validation-plots", "-k", "test_case").assert_outcomes(passed=1, deselected=1)
    data = (case.path / "docs/assets/validation/case.svg").read_text()
    assert "test: test_case.py::test_case" in data
    assert "command: pytest test_case.py::test_case --validation-plots" in data


def test_help_lists_option(pytester):
    pytester.runpytest("--help").stdout.fnmatch_lines(["*--validation-plots*"])
