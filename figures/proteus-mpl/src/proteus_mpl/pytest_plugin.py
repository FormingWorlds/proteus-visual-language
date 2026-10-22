"""pytest plugin: the `validation_plot` fixture and the ``--validation-plots`` option.

Without the option the fixture checks its arguments and writes nothing, so a
test asserts its tolerance without writing files. ``pytest -m reference_pinned
--validation-plots`` makes every plot again in ``docs/assets/validation`` under
the pytest rootdir; ``--validation-plots=DIR`` writes to another folder.
"""

import shlex
from pathlib import Path

import pytest

DEFAULT_DIR = "docs/assets/validation"
_WRITTEN = pytest.StashKey[set]()


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


def pytest_configure(config):
    """Refuse an empty folder and a word that the bare option has read as its folder."""
    outdir = config.getoption("validation_plots")
    args = list(config.invocation_params.args)
    if outdir == "":
        raise pytest.UsageError("--validation-plots=DIR needs a folder")
    for flag, word in zip(args, args[1:]):
        if flag == "--validation-plots" and word == outdir:
            raise pytest.UsageError(
                f"--validation-plots read {word!r} as its folder; write "
                "--validation-plots=DIR, or put the option after the test paths"
            )
    config.stash[_WRITTEN] = set()


@pytest.fixture
def validation_plot(request):
    """Return ``plot(fig_factory, name, kind="line")``, which saves a validation plot pair.

    The call returns the written paths, or an empty list without
    ``--validation-plots``; `fig_factory` is then not called. A file written
    twice in one session raises ValueError.
    """
    from .validation import KINDS, check_args, save

    config = request.config
    outdir = config.getoption("validation_plots")

    def plot(fig_factory, name, kind="line"):
        check_args(name, kind)
        if outdir is None:
            return []
        folder = Path(config.rootpath, outdir)
        light = folder / f"{name}.{KINDS[kind]}"
        if light in config.stash[_WRITTEN]:
            raise ValueError(f"{name}: written twice in this session; give each plot its own name")
        nodeid = request.node.nodeid
        paths = save(
            fig_factory,
            name,
            folder,
            kind,
            test_id=nodeid,
            command=f"pytest {shlex.quote(nodeid)} --validation-plots",
        )
        config.stash[_WRITTEN].add(light)
        return paths

    return plot
