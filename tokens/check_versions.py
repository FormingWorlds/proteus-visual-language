#!/usr/bin/env python3
"""Verify the published packages declare the same version.

The npm token package (``tokens/package.json``) and the ``proteus-mpl`` PyPI
package (``figures/proteus-mpl/pyproject.toml``) release together off a single
``vX.Y.Z`` git tag. The release workflow asserts each manifest against the tag
independently, so if the two manifests disagree, one package publishes while
the other is rejected. Keeping the two version fields equal is what allows both
packages to publish from one tag.

Run without arguments to compare the two manifest versions; the exit code is
non-zero when they differ. Paths resolve relative to this file.
"""

import json
import sys
import tomllib
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PACKAGE_JSON = REPO / "tokens" / "package.json"
PYPROJECT = REPO / "figures" / "proteus-mpl" / "pyproject.toml"


def npm_version():
    """Return the version declared in ``tokens/package.json``.

    Returns
    -------
    str
        The value of the top-level ``version`` field.
    """
    data = json.loads(PACKAGE_JSON.read_text(encoding="utf-8"))
    return data["version"]


def pypi_version():
    """Return the version declared in ``proteus-mpl``'s ``pyproject.toml``.

    Returns
    -------
    str
        The value of ``[project] version``.
    """
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    return data["project"]["version"]


def main(argv):
    """Compare the two manifest versions.

    Parameters
    ----------
    argv : list of str
        Command-line arguments; none are accepted.

    Returns
    -------
    int
        ``0`` when the versions match, ``1`` on a mismatch or read error,
        ``2`` on misuse.
    """
    if argv[1:]:
        print("usage: check_versions.py")
        return 2
    try:
        npm = npm_version()
        pypi = pypi_version()
    except (OSError, KeyError, ValueError) as exc:
        print(f"could not read package versions: {exc}")
        return 1
    if npm != pypi:
        print(
            "package versions are out of lockstep; set both to the same "
            "version (the bare X.Y.Z, no v prefix) before tagging a release:\n"
            f"  tokens/package.json: {npm}\n"
            f"  figures/proteus-mpl/pyproject.toml: {pypi}"
        )
        return 1
    print(f"package versions are in lockstep ({npm})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
