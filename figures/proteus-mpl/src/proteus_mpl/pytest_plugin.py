"""pytest plugin: the `validation_plot` fixture and the ``--validation-plots`` option.

Without the option the fixture checks its arguments and writes nothing, so a
test asserts its tolerance without writing files. ``pytest -m reference_pinned
--validation-plots`` makes every plot again in ``docs/assets/validation`` under
the pytest rootdir; ``--validation-plots=DIR`` writes to another folder.
"""

import os
import shlex
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
    """Replace each ``@file`` argument by the lines of that file, as argparse reads them."""
    out = []
    for arg in args:
        if arg.startswith("@"):
            try:
                lines = Path(folder, arg[1:]).read_text().splitlines()
            except OSError:
                lines = [arg]
            else:
                lines = _expand_argfiles(lines, folder)
            out.extend(lines)
        else:
            out.append(arg)
    return out


def _is_file(path):
    """Return True for an existing file; a path the system cannot stat is not one."""
    try:
        return path.is_file()
    except OSError:
        return False


def pytest_configure(config):
    """Refuse an empty folder and a word that the bare option has read as its folder."""
    outdir = config.getoption("validation_plots")
    if outdir == "":
        raise pytest.UsageError("--validation-plots=DIR needs a folder")
    # pytest parses ini addopts, then PYTEST_ADDOPTS, then the command line, as one list
    args = [
        *config.getini("addopts"),
        *shlex.split(os.environ.get("PYTEST_ADDOPTS", "")),
        *_expand_argfiles(map(str, config.invocation_params.args), config.invocation_params.dir),
    ]
    if ("--validation-plots", outdir) in zip(args, args[1:]):
        raise pytest.UsageError(
            f"--validation-plots read {outdir!r} as its folder; write --validation-plots=DIR, "
            "also in addopts and PYTEST_ADDOPTS, or put the option after the test paths"
        )
    if outdir and (
        "::" in outdir
        or outdir.endswith(".py")
        or _is_file(Path(config.invocation_params.dir, outdir))
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
