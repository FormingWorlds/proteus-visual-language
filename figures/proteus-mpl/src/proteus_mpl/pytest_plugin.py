"""pytest plugin: the `validation_plot` fixture and the ``--validation-plots`` option.

Without the option the fixture does nothing, so a test asserts its tolerance
without writing files. ``pytest -m reference_pinned --validation-plots`` makes
every plot again in ``docs/assets/validation``; ``--validation-plots=DIR``
writes to another folder.
"""

import shlex
from pathlib import Path

import pytest

DEFAULT_DIR = "docs/assets/validation"


def pytest_addoption(parser):
    """Register ``--validation-plots[=DIR]``."""
    parser.getgroup("proteus-mpl").addoption(
        "--validation-plots",
        nargs="?",
        const=DEFAULT_DIR,
        default=None,
        dest="validation_plots",
        metavar="DIR",
        help=(
            "write the light and dark plot of each validation_plot call to DIR "
            f"(default {DEFAULT_DIR}); give DIR with '=', since a bare word after "
            "the option is read as DIR"
        ),
    )


def pytest_configure(config):
    """Refuse a test path that the option has taken as its folder."""
    outdir = config.getoption("validation_plots")
    if outdir and (outdir.endswith(".py") or "::" in outdir):
        raise pytest.UsageError(
            f"--validation-plots took the test path {outdir!r} as its folder; "
            "write --validation-plots=DIR, or put the option after the test path"
        )


@pytest.fixture
def validation_plot(request):
    """Return ``plot(fig_factory, name, kind="line")``, which saves a validation plot pair.

    The call returns the written paths, or an empty list without
    ``--validation-plots``; `fig_factory` is then not called.
    """
    outdir = request.config.getoption("validation_plots")

    def plot(fig_factory, name, kind="line"):
        if outdir is None:
            return []
        from .validation import save

        nodeid = request.node.nodeid
        return save(
            fig_factory,
            name,
            Path(request.config.rootpath, outdir),
            kind,
            test_id=nodeid,
            command=f"pytest {shlex.quote(nodeid)} --validation-plots",
        )

    return plot
