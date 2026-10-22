"""Tests for the validation_plot fixture and the --validation-plots option."""

import pytest

CASE = """
import pytest
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


def test_map(validation_plot):
    validation_plot(factory, "field", kind="map")


@pytest.mark.parametrize("value", ["a b"])
def test_spaced_id(validation_plot, value):
    validation_plot(factory, "spaced")


def test_bad_kind(validation_plot):
    validation_plot(factory, "bad", kind="bar")


def test_same_name_twice(validation_plot):
    first = validation_plot(factory, "twice")
    before = first[0].read_bytes() if first else None

    def other():
        fig = factory()
        fig.axes[0].plot([0, 2], [0, 2])
        return fig

    with pytest.raises(ValueError, match="used twice in this session"):
        validation_plot(other, "Twice")
    if first:
        assert first[0].read_bytes() == before


def test_same_name_for_line_and_map(validation_plot):
    validation_plot(factory, "both")
    validation_plot(factory, "both", kind="map")


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
    """Every file under root except test sources, ini files and caches."""
    return sorted(
        str(p.relative_to(root))
        for p in root.rglob("*")
        if p.is_file()
        and p.suffix not in (".py", ".ini")
        and not any(
            part.startswith(".") or part == "__pycache__" for part in p.relative_to(root).parts
        )
    )


def test_without_option_writes_nothing(case):
    result = case.runpytest("-s")
    result.assert_outcomes(passed=6, failed=1)
    result.stdout.fnmatch_lines(["*test_bad_kind*kind must be 'line' or 'map'*"])
    result.stdout.fnmatch_lines(["*WRITTEN []*"])
    assert files(case.path) == []


def test_option_alone_writes_to_default_dir(case):
    result = case.runpytest("-s", "test_case.py::test_case", "--validation-plots")
    result.assert_outcomes(passed=1)
    assert files(case.path) == [
        "docs/assets/validation/case.svg",
        "docs/assets/validation/case_dark.svg",
    ]


def test_option_with_relative_dir(case):
    result = case.runpytest("--validation-plots=out/plots", "test_case.py::test_case")
    result.assert_outcomes(passed=1)
    assert files(case.path) == ["out/plots/case.svg", "out/plots/case_dark.svg"]


def test_option_with_absolute_dir(case, tmp_path_factory):
    out = tmp_path_factory.mktemp("abs")
    result = case.runpytest(f"--validation-plots={out}", "test_case.py::test_case")
    result.assert_outcomes(passed=1)
    assert files(out) == ["case.svg", "case_dark.svg"]
    assert files(case.path) == []


def test_stamp_names_test_and_command(case):
    case.runpytest("test_case.py::test_case", "--validation-plots").assert_outcomes(passed=1)
    data = (case.path / "docs/assets/validation/case.svg").read_text()
    assert "test: test_case.py::test_case" in data
    assert "command: pytest test_case.py::test_case --validation-plots" in data


def test_help_lists_option(pytester):
    pytester.runpytest("--help").stdout.fnmatch_lines(["*--validation-plots*"])


@pytest.mark.parametrize("value", ["test_case.py", "test_case.py::test_case", "."])
def test_word_after_bare_option_is_refused(case, value):
    result = case.runpytest("--validation-plots", value)
    assert result.ret == pytest.ExitCode.USAGE_ERROR
    result.stderr.fnmatch_lines(["*read*as its folder*--validation-plots=DIR*"])
    assert files(case.path) == []


def test_empty_dir_is_refused(case):
    result = case.runpytest("test_case.py::test_case", "--validation-plots=")
    assert result.ret == pytest.ExitCode.USAGE_ERROR
    result.stderr.fnmatch_lines(["*--validation-plots=DIR needs a folder*"])
    assert files(case.path) == []


def test_equals_form_accepts_an_existing_folder(case):
    case.mkdir("tests")
    result = case.runpytest("test_case.py::test_case", "--validation-plots=tests")
    result.assert_outcomes(passed=1)
    assert files(case.path) == ["tests/case.svg", "tests/case_dark.svg"]


def test_stamp_quotes_a_node_id_with_a_space(case):
    case.runpytest("test_case.py::test_spaced_id", "--validation-plots").assert_outcomes(passed=1)
    data = (case.path / "docs/assets/validation/spaced.svg").read_text()
    assert "command: pytest 'test_case.py::test_spaced_id[a b]' --validation-plots" in data


def test_same_name_twice_in_a_session_is_refused(case):
    result = case.runpytest("test_case.py::test_same_name_twice", "--validation-plots")
    result.assert_outcomes(passed=1)


def test_map_kind_writes_avif(case):
    case.runpytest("test_case.py::test_map", "--validation-plots").assert_outcomes(passed=1)
    assert files(case.path) == [
        "docs/assets/validation/field.avif",
        "docs/assets/validation/field_dark.avif",
    ]


def test_relative_dir_resolves_against_rootdir(case):
    case.makeini("[pytest]\n")
    sub = case.mkdir("sub")
    sub.joinpath("test_sub.py").write_text(CASE)
    with pytest.MonkeyPatch.context() as mp:
        mp.chdir(sub)
        result = case.runpytest("test_sub.py::test_case", "--validation-plots")
    result.assert_outcomes(passed=1)
    assert files(case.path) == [
        "docs/assets/validation/case.svg",
        "docs/assets/validation/case_dark.svg",
    ]


def test_bare_option_in_ini_addopts_is_checked(case):
    case.makeini("[pytest]\naddopts = --validation-plots\n")
    result = case.runpytest("test_case.py::test_case")
    assert result.ret == pytest.ExitCode.USAGE_ERROR
    result.stderr.fnmatch_lines(["*read 'test_case.py::test_case' as its folder*addopts*"])
    assert files(case.path) == []


def test_bare_option_in_env_addopts_is_checked(case, monkeypatch):
    monkeypatch.setenv("PYTEST_ADDOPTS", "--validation-plots")
    result = case.runpytest("test_case.py::test_case")
    assert result.ret == pytest.ExitCode.USAGE_ERROR
    result.stderr.fnmatch_lines(["*read 'test_case.py::test_case' as its folder*addopts*"])
    assert files(case.path) == []


def test_bare_option_in_addopts_before_an_option_writes_default(case):
    case.makeini("[pytest]\naddopts = --validation-plots -q\n")
    case.runpytest("test_case.py::test_case").assert_outcomes(passed=1)
    assert files(case.path) == [
        "docs/assets/validation/case.svg",
        "docs/assets/validation/case_dark.svg",
    ]


def test_line_and_map_with_one_name_write_both_pairs(case):
    case.runpytest(
        "test_case.py::test_same_name_for_line_and_map", "--validation-plots"
    ).assert_outcomes(passed=1)
    assert files(case.path) == [
        "docs/assets/validation/both.avif",
        "docs/assets/validation/both.svg",
        "docs/assets/validation/both_dark.avif",
        "docs/assets/validation/both_dark.svg",
    ]


RERUN = """
import pytest
from _pytest.runner import runtestprotocol


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_protocol(item, nextitem):
    item.ihook.pytest_runtest_logstart(nodeid=item.nodeid, location=item.location)
    reports = runtestprotocol(item, nextitem=nextitem, log=False)
    if any(r.failed for r in reports):
        reports = runtestprotocol(item, nextitem=nextitem, log=False)
    for report in reports:
        item.ihook.pytest_runtest_logreport(report=report)
    item.ihook.pytest_runtest_logfinish(nodeid=item.nodeid, location=item.location)
    return True
"""

FLAKY = """
import matplotlib.pyplot as plt

CALLS = []


def test_flaky(validation_plot):
    validation_plot(lambda: plt.subplots()[0], "flaky")
    CALLS.append(1)
    assert len(CALLS) > 1


def test_other_test_same_name(validation_plot):
    validation_plot(lambda: plt.subplots()[0], "flaky")
"""


@pytest.mark.parametrize("option", [[], ["--validation-plots"]])
def test_rerun_of_one_test_may_reuse_its_names(pytester, option):
    pytester.makeconftest(RERUN)
    pytester.makepyfile(test_flaky=FLAKY)
    result = pytester.runpytest("test_flaky.py::test_flaky", *option)
    result.assert_outcomes(passed=1)
    result = pytester.runpytest("test_flaky.py", *option)
    result.assert_outcomes(passed=1, failed=1)
    result.stdout.fnmatch_lines(["*test_other_test_same_name*used twice*"])


@pytest.mark.parametrize("word", ["test_case.py", "test_case.py::test_case"])
def test_argfile_with_bare_option_is_refused(case, word):
    case.path.joinpath("args.txt").write_text(f"--validation-plots\n{word}\n")
    result = case.runpytest("@args.txt")
    assert result.ret == pytest.ExitCode.USAGE_ERROR
    result.stderr.fnmatch_lines(["*is a test path, not a folder*"])
    assert files(case.path) == ["args.txt"]
