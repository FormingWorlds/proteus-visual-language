"""Tests for the checks the validation_plot fixture makes on every run."""

import pytest

CASE = """
import pytest
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

Y = [1.0, 0.0, 1.0]


def factory():
    fig, ax = plt.subplots(figsize=(3, 2))
    ax.plot([0.0, 1.0, 2.0], Y)
    return fig


def test_case(validation_plot):
    validation_plot(factory, "case")


def test_takes_fixture_without_plot(validation_plot):
    assert True


def test_fails_without_plot(validation_plot):
    assert False, "own failure"


def test_factory_runs_without_option(validation_plot):
    def boom():
        raise RuntimeError("factory called")

    validation_plot(boom, "boom")


def test_too_big(validation_plot):
    def big():
        fig, ax = plt.subplots()
        for k in range(200):
            ax.plot(np.random.default_rng(k).random(400))
        return fig

    validation_plot(big, "big")


def test_bad_name_is_caught(validation_plot):
    with pytest.raises(ValueError):
        validation_plot(factory, "bad name")


@pytest.mark.xfail(reason="passes")
def test_xpass_without_plot(validation_plot):
    assert True


def test_upper(validation_plot):
    validation_plot(factory, "Case")
"""


@pytest.fixture
def case(pytester):
    pytester.makepyfile(test_case=CASE)
    return pytester


def committed(case):
    return case.path / "docs" / "assets" / "validation"


def make_pair(case):
    case.runpytest("test_case.py::test_case", "--validation-plots").assert_outcomes(passed=1)
    return committed(case) / "case.svg"


def test_a_test_that_takes_the_fixture_and_makes_no_plot_fails(case):
    result = case.runpytest("test_case.py::test_takes_fixture_without_plot")
    result.assert_outcomes(passed=1, errors=1)
    result.stdout.fnmatch_lines(["*took validation_plot but made no plot*"])


def test_a_failing_test_without_plot_is_reported_once(case):
    result = case.runpytest("test_case.py::test_fails_without_plot")
    result.assert_outcomes(failed=1)
    assert "made no plot" not in result.stdout.str()


def test_the_factory_runs_without_the_option(case):
    result = case.runpytest("test_case.py::test_factory_runs_without_option")
    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines(["*RuntimeError: factory called*"])


def test_the_size_cap_applies_without_the_option(case):
    result = case.runpytest("test_case.py::test_too_big")
    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines(["*above the 60000 B cap*"])
    assert not committed(case).exists()


def test_a_missing_committed_pair_fails(case):
    result = case.runpytest("test_case.py::test_case")
    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines(["*case: no committed plot at */docs/assets/validation/case.svg*"])


def test_a_matching_committed_pair_passes_and_is_not_rewritten(case):
    light = make_pair(case)
    before = {p.name: p.read_bytes() for p in committed(case).iterdir()}
    case.runpytest("test_case.py::test_case").assert_outcomes(passed=1)
    assert {p.name: p.read_bytes() for p in committed(case).iterdir()} == before
    assert light.exists()


def test_changed_data_fails_as_stale(case):
    make_pair(case)
    case.makepyfile(test_changed=CASE.replace("Y = [1.0, 0.0, 1.0]", "Y = [1.0, 0.0, 1.5]"))
    result = case.runpytest("test_changed.py::test_case")
    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines(["*case: the committed plot case.svg is stale*--validation-plots*"])


def test_a_different_stamp_alone_passes(case):
    case.runpytest("test_case.py::test_case", "--validation-plots=out").assert_outcomes(passed=1)
    committed(case).mkdir(parents=True)
    for name in ("case.svg", "case_dark.svg"):
        (committed(case) / name).write_bytes((case.path / "out" / name).read_bytes())
    case.runpytest("test_case.py::test_case").assert_outcomes(passed=1)


def test_a_pair_without_summary_passes_with_a_warning(case):
    light = make_pair(case)
    text = light.read_text()
    start = text.index("; summary: ")
    end = text.index("</dc:description>", start)
    light.write_text(text[:start] + text[end:])
    result = case.runpytest("test_case.py::test_case")
    result.assert_outcomes(passed=1, warnings=1)
    result.stdout.fnmatch_lines(["*case: case.svg carries no data summary*"])


def test_the_option_writes_and_does_not_compare(case):
    make_pair(case)
    case.makepyfile(test_changed=CASE.replace("Y = [1.0, 0.0, 1.0]", "Y = [1.0, 0.0, 1.5]"))
    case.runpytest("test_changed.py::test_case", "--validation-plots").assert_outcomes(passed=1)
    case.runpytest("test_changed.py::test_case").assert_outcomes(passed=1)
    case.runpytest("test_case.py::test_case").assert_outcomes(failed=1)


def test_a_test_that_catches_an_argument_error_passes(case):
    case.runpytest("test_case.py::test_bad_name_is_caught").assert_outcomes(passed=1)


def test_an_xpass_without_plot_is_reported_once(case):
    case.runpytest("test_case.py::test_xpass_without_plot").assert_outcomes(xpassed=1)


def test_a_missing_dark_file_fails(case):
    make_pair(case)
    (committed(case) / "case_dark.svg").unlink()
    result = case.runpytest("test_case.py::test_case")
    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines(["*no committed plot at */case_dark.svg*"])


def test_a_stale_dark_file_fails(case):
    make_pair(case)
    case.makepyfile(test_changed=CASE.replace("Y = [1.0, 0.0, 1.0]", "Y = [1.0, 0.0, 1.5]"))
    case.runpytest("test_changed.py::test_case", "--validation-plots=out").assert_outcomes(passed=1)
    (committed(case) / "case_dark.svg").write_bytes((case.path / "out" / "case_dark.svg").read_bytes())
    result = case.runpytest("test_case.py::test_case")
    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines(["*case: the committed plot case_dark.svg is stale*"])


def test_a_name_in_other_case_is_not_the_committed_plot(case):
    make_pair(case)
    result = case.runpytest("test_case.py::test_upper")
    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines(["*Case: no committed plot at */Case.svg*"])


def test_an_unreadable_summary_fails(case):
    light = make_pair(case)
    light.write_text(light.read_text().replace("summary: {", "summary: {x"))
    result = case.runpytest("test_case.py::test_case")
    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines(["*case.svg carries an unreadable data summary*--validation-plots*"])


def test_a_summary_of_another_format_passes_with_a_warning(case):
    light = make_pair(case)
    light.write_text(light.read_text().replace('{&quot;v&quot;: 1', '{&quot;v&quot;: 0').replace('{"v": 1', '{"v": 0'))
    result = case.runpytest("test_case.py::test_case")
    result.assert_outcomes(passed=1, warnings=1)
    result.stdout.fnmatch_lines(["*case.svg carries no data summary of this version*"])


def test_the_pair_is_found_under_the_rootdir_from_a_subfolder(case):
    case.makeini("[pytest]\n")
    make_pair(case)
    sub = case.mkdir("sub")
    (sub / "test_sub.py").write_text(CASE)
    with pytest.MonkeyPatch.context() as mp:
        mp.chdir(sub)
        case.runpytest("test_sub.py::test_case").assert_outcomes(passed=1)
