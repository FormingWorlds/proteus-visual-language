"""pytest plugin: the `validation_plot` fixture and the ``--validation-plots`` option.

Without the option the fixture renders both themes in memory, applies the size
cap and compares the data summary with both files of the committed pair in
``docs/assets/validation`` under the pytest rootdir; it writes nothing, and a
missing or stale file fails the test. ``pytest -m reference_pinned
--validation-plots`` makes every plot again in that folder;
``--validation-plots=DIR`` writes to another folder and compares nothing.
"""

import os
import re
import shlex
import sys
import warnings
from pathlib import Path

import pytest

DEFAULT_DIR = "docs/assets/validation"
_SEEN = pytest.StashKey[dict]()
_PASSED = pytest.StashKey[bool]()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Keep whether the call phase passed, not as an xpass, for the fixture's teardown."""
    report = (yield).get_result()
    if report.when == "call":
        item.stash[_PASSED] = report.passed and not hasattr(report, "wasxfail")


def pytest_addoption(parser):
    """Register ``--validation-plots[=DIR]``."""
    parser.getgroup("proteus-mpl").addoption(
        "--validation-plots",
        nargs="?",
        const=DEFAULT_DIR,
        metavar="DIR",
        help=(
            "write the light and dark plot of each validation_plot call to DIR, "
            f"relative to the rootdir (default {DEFAULT_DIR}); give DIR as "
            "--validation-plots=DIR"
        ),
    )


def _expand_argfiles(args, folder):
    """Replace each ``@file`` argument by the lines of that file, read as argparse reads them.

    A word whose file cannot be read stays as it is.
    """
    if sys.version_info >= (3, 12):
        codec = {"encoding": sys.getfilesystemencoding(), "errors": sys.getfilesystemencodeerrors()}
    else:
        codec = {}
    out = []
    for arg in args:
        if not arg.startswith("@"):
            out.append(arg)
            continue
        try:
            text = Path(folder, arg[1:]).read_text(**codec)
        except OSError:
            out.append(arg)
        else:
            out.extend(_expand_argfiles(text.splitlines(), folder))
    return out


# argparse takes a word like -1 or -.5 as a value, not an option
_NEGATIVE_NUMBER = re.compile(r"-\d+$|-\d*\.\d+$")


def _swallowed_word(args, outdir):
    """Return the word a bare ``--validation-plots`` reads as its folder, or None.

    A word counts when argparse takes it as a value: no leading dash, a dash
    alone, a negative number, a space in it, or the parsed folder itself.
    """
    for flag, word in zip(args, args[1:]):
        if flag == "--":
            return None
        if flag == "--validation-plots" and (
            not word.startswith("-")
            or word in ("-", outdir)
            or " " in word
            or _NEGATIVE_NUMBER.match(word)
        ):
            return word
    return None


def pytest_configure(config):
    """Refuse an empty folder and a word that the bare option has read as its folder."""
    outdir = config.getoption("validation_plots")
    config.stash[_SEEN] = {}
    if outdir == "":
        raise pytest.UsageError("--validation-plots=DIR needs a folder")
    if outdir is None:
        return
    # pytest parses ini addopts, then PYTEST_ADDOPTS, then the command line, as one list
    args = _expand_argfiles(
        [
            *config.getini("addopts"),
            *shlex.split(os.environ.get("PYTEST_ADDOPTS", "")),
            *map(str, config.invocation_params.args),
        ],
        config.invocation_params.dir,
    )
    word = _swallowed_word(args, outdir)
    if word is not None:
        raise pytest.UsageError(
            f"--validation-plots read {word!r} as its folder; write --validation-plots=DIR, "
            "also in addopts and PYTEST_ADDOPTS, or put the option after the test paths"
        )
    if (
        "::" in outdir
        or outdir.endswith(".py")
        or os.path.isfile(Path(config.invocation_params.dir, outdir))
    ):
        raise pytest.UsageError(f"--validation-plots={outdir!r} is a test path, not a folder")


@pytest.fixture
def validation_plot(request):
    """Return ``plot(fig_factory, name, kind="line")``, which makes a validation plot pair.

    With ``--validation-plots`` the call writes the pair and returns the written
    paths. Without it the call renders both themes in memory (the size cap
    applies), compares the data summary with both committed files and returns an
    empty list; a missing or stale committed file fails the test, a committed file
    without a summary of this version gives a warning. A name used twice for one kind in a
    session raises ValueError, with or without the option; a rerun of the same
    test may use its names again. A test that takes the fixture and passes
    without calling it fails at teardown.
    """
    from .validation import check_args, render, save

    config = request.config
    outdir = config.getoption("validation_plots")
    nodeid = request.node.nodeid
    option = "--validation-plots"
    if outdir not in (None, DEFAULT_DIR):
        option = shlex.quote(f"{option}={outdir}")
    seen = config.stash[_SEEN]
    for key in [key for key, owner in seen.items() if owner == nodeid]:
        del seen[key]
    calls = []

    def plot(fig_factory, name, kind="line"):
        calls.append(name)
        check_args(name, kind)
        key = (name.lower(), kind)
        if key in seen:
            raise ValueError(
                f"{name}: used twice in this session, first in {seen[key]}; "
                "give each plot its own name"
            )
        seen[key] = nodeid
        if outdir is not None:
            return save(
                fig_factory,
                name,
                Path(config.rootpath, outdir),
                kind,
                test_id=nodeid,
                command=f"pytest {shlex.quote(nodeid)} {option}",
            )
        files, summary = render(fig_factory, name, kind)
        for fname, _ in files:
            _check_committed(name, Path(config.rootpath, DEFAULT_DIR, fname), summary)
        return []

    yield plot
    if not calls and request.node.stash.get(_PASSED, False):
        pytest.fail(f"{nodeid} took validation_plot but made no plot", pytrace=False)


def _check_committed(name, path, summary):
    """Fail when the committed file `path` is missing, unreadable or stale for `summary`."""
    from .validation import compare_summaries, read_summary

    again = "make it again with --validation-plots"
    if not path.is_file() or path.name not in os.listdir(path.parent):
        pytest.fail(
            f"{name}: no committed plot at {path}; make it with --validation-plots and commit it",
            pytrace=False,
        )
    try:
        committed = read_summary(path)
        same = committed is not None and committed.get("v") == summary["v"]
        diffs = compare_summaries(summary, committed) if same else []
    except (ValueError, TypeError, KeyError, AttributeError) as err:
        pytest.fail(
            f"{name}: {path.name} carries an unreadable data summary ({err}); {again} and "
            "commit it",
            pytrace=False,
        )
    if not same:
        version = "" if committed is None else " of this version"
        warnings.warn(
            f"{name}: {path.name} carries no data summary{version}; {again} so that it can "
            "be compared",
            stacklevel=3,
        )
    elif diffs:
        more = f" and {len(diffs) - 1} more" if len(diffs) > 1 else ""
        pytest.fail(
            f"{name}: the committed plot {path.name} is stale ({diffs[0]}{more}); {again} "
            "and commit it",
            pytrace=False,
        )
