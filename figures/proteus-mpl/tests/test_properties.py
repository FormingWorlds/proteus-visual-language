"""Property tests for the inputs of the validation helper and the pytest option."""

import re
from types import SimpleNamespace

import pytest
from hypothesis import example, given
from hypothesis import strategies as st

from proteus_mpl import pytest_plugin
from proteus_mpl.validation import check_args

STEM = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")


@given(st.text())
@example("1abc")
@example("a.b-c_1")
def test_name_is_accepted_only_as_a_plain_stem(name):
    plain = bool(STEM.fullmatch(name)) and not name.lower().endswith("_dark")
    try:
        check_args(name, "line")
    except ValueError:
        assert not plain
    else:
        assert plain
        assert "/" not in name and "\\" not in name and name not in (".", "..")


@given(
    st.one_of(
        st.sampled_from(["line", "map"]),
        st.text(),
        st.integers(),
        st.floats(),
        st.none(),
        st.booleans(),
        st.lists(st.text()),
        st.dictionaries(st.text(), st.text()),
    )
)
def test_kind_other_than_line_or_map_raises_value_error(kind):
    if kind in ("line", "map") and isinstance(kind, str):
        check_args("case", kind)
    else:
        with pytest.raises(ValueError, match="kind must be 'line' or 'map'"):
            check_args("case", kind)


def fake_config(value, tmp_path, args=()):
    """A config object with the attributes pytest_configure reads."""
    return SimpleNamespace(
        getoption=lambda name: value,
        getini=lambda name: [],
        invocation_params=SimpleNamespace(args=args, dir=tmp_path),
        stash={},
    )


@given(st.text())
@example("a\x00b")
@example("a:b")
@example("C:/plots")
@example("a" * 300)
def test_option_value_is_refused_only_when_empty_or_a_test_path(tmp_path_factory, value):
    root = tmp_path_factory.mktemp("cwd")
    root.joinpath("test_a.py").write_text("")
    test_path = value == "" or "::" in value or value.endswith(".py")
    try:
        is_file = root.joinpath(value).is_file()
    except (OSError, ValueError):
        is_file = False
    try:
        pytest_plugin.pytest_configure(
            fake_config(value, root, args=(f"--validation-plots={value}",))
        )
    except pytest.UsageError:
        assert test_path or is_file
    else:
        assert not (test_path or is_file)


@pytest.mark.parametrize("value", ["missing.py", "data.txt", "pkg/test_x.py::test_y"])
def test_option_value_naming_a_file_is_refused(tmp_path, value):
    tmp_path.joinpath("data.txt").write_text("")
    with pytest.raises(pytest.UsageError, match="is a test path, not a folder"):
        pytest_plugin.pytest_configure(
            fake_config(value, tmp_path, args=(f"--validation-plots={value}",))
        )


@pytest.mark.parametrize("value", ["numpy", "out/copy", "plots"])
def test_folder_name_ending_in_py_without_a_dot_is_accepted(tmp_path, value):
    config = fake_config(value, tmp_path, args=(f"--validation-plots={value}",))
    pytest_plugin.pytest_configure(config)
    assert config.stash == {pytest_plugin._SEEN: {}}
