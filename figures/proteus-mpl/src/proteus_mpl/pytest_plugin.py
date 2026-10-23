"""pytest plugin: the `validation_plot` fixture and the ``--validation-plots`` option.

Without the option the fixture checks its arguments and writes nothing, so a
test asserts its tolerance without writing files. ``pytest -m reference_pinned
--validation-plots`` makes every plot again in ``docs/assets/validation`` under
the pytest rootdir; ``--validation-plots=DIR`` writes to another folder.
"""

import os
import re
import shlex
import sys
from pathlib import Path

import pytest

DEFAULT_DIR = "docs/assets/validation"
_SEEN = pytest.StashKey[dict]()


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

    A word whose file cannot be read stays as it is; argparse refuses such a
    file before this runs, so the word only reaches here on a pytest that does
    not read argfiles.
    """
    out = []
    for arg in args:
        if not arg.startswith("@"):
            out.append(arg)
            continue
        try:
            with open(
                Path(folder, arg[1:]),
                encoding=sys.getfilesystemencoding(),
                errors=sys.getfilesystemencodeerrors(),
            ) as fh:
                lines = fh.read().splitlines()
        except OSError:
            out.append(arg)
        else:
            out.extend(_expand_argfiles(lines, folder))
    return out


# argparse takes a word like -1 or -.5 as a value, not an option
_NEGATIVE_NUMBER = re.compile(r"-\d+$|-\d*\.\d+$")


def _swallowed_word(args):
    """Return the word a bare ``--validation-plots`` reads as its folder, or None."""
    for flag, word in zip(args, args[1:]):
        if flag == "--":
            return None
        if flag == "--validation-plots" and (
            not word.startswith("-") or word == "-" or _NEGATIVE_NUMBER.match(word)
        ):
            return word
    return None


def pytest_configure(config):
    """Refuse an empty folder and a word that the bare option has read as its folder."""
    outdir = config.getoption("validation_plots")
    if outdir == "":
        raise pytest.UsageError("--validation-plots=DIR needs a folder")
    if outdir is None:
        config.stash[_SEEN] = {}
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
    word = _swallowed_word(args)
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
    config.stash[_SEEN] = {}


@pytest.fixture
def validation_plot(request):
    """Return ``plot(fig_factory, name, kind="line")``, which saves a validation plot pair.

    The call returns the written paths, or an empty list without
    ``--validation-plots``; `fig_factory` is then not called. A name used twice
    for one kind in a session raises ValueError, with or without the option; a
    rerun of the same test may use its names again.
    """
    from .validation import check_args, save

    config = request.config
    outdir = config.getoption("validation_plots")
    nodeid = request.node.nodeid
    option = "--validation-plots"
    if outdir not in (None, DEFAULT_DIR):
        option = shlex.quote(f"{option}={outdir}")
    seen = config.stash[_SEEN]
    for key in [key for key, owner in seen.items() if owner == nodeid]:
        del seen[key]

    def plot(fig_factory, name, kind="line"):
        check_args(name, kind)
        key = (name.lower(), kind)
        if key in seen:
            raise ValueError(
                f"{name}: used twice in this session, first in {seen[key]}; "
                "give each plot its own name"
            )
        seen[key] = nodeid
        if outdir is None:
            return []
        return save(
            fig_factory,
            name,
            Path(config.rootpath, outdir),
            kind,
            test_id=nodeid,
            command=f"pytest {shlex.quote(nodeid)} {option}",
        )

    return plot
