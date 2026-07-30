#!/usr/bin/env python3
"""Verify the published packages declare the same version.

The npm token package (``tokens/package.json``) and the ``proteus-mpl`` PyPI
package (``figures/proteus-mpl/pyproject.toml``) release together off a single
``vX.Y.Z`` git tag. The release workflow asserts each manifest against the tag
independently, so if the two manifests disagree, one package publishes while
the other is rejected. Keeping the two version fields equal is what allows both
packages to publish from one tag.

The version is also written out in prose in several artifacts a reader sees:
the brand-guide page, the README footer, the Beamer theme, the web chrome, and
the token file header. Those carry ``vX.Y`` only. Nothing generates them, so
they drift a release behind unless something checks them, which is what the
second half of this script does.

Run without arguments to compare the manifest versions and the displayed ones;
the exit code is non-zero when any disagree. Paths resolve relative to this
file.
"""

import json
import sys
import tomllib
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PACKAGE_JSON = REPO / "tokens" / "package.json"
PYPROJECT = REPO / "figures" / "proteus-mpl" / "pyproject.toml"

# Artifacts that spell the version out for a reader -> the exact strings that
# must carry it. Each entry is checked, so a file that stops matching is an
# error rather than a silent pass.
DISPLAYED = {
    "site/index.html": ["PROTEUS Visual Language v{v} \u2014", "V{V} \u00b7 THERMOCLINE"],
    "README.md": ["Thermocline v{v}"],
    "talks/beamer/beamerthemeproteus.sty": [
        "PROTEUS Thermocline beamer theme v{v}",
        "v{v} PROTEUS Thermocline]",
    ],
    "templates/web/site.css": ["(Thermocline v{v})"],
    "tokens/tokens.css": ["THERMOCLINE DESIGN TOKENS  v{v}"],
}


def displayed_problems(version):
    """Return one message per artifact that does not display this version.

    Parameters
    ----------
    version : str
        The package version, ``X.Y.Z``.

    Returns
    -------
    list of str
        One message per missing string, naming the file and what it should
        contain.
    """
    short = ".".join(version.split(".")[:2])
    problems = []
    for name, patterns in DISPLAYED.items():
        path = REPO / name
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            problems.append(f"{name}: cannot read ({exc})")
            continue
        for pattern in patterns:
            wanted = pattern.format(v=short, V=short.upper())
            if wanted not in text:
                problems.append(f"{name}: does not display {wanted!r}")
    return problems


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
    problems = displayed_problems(npm)
    if problems:
        print(
            f"the packages are at {npm}, but the version shown to readers has not "
            "been updated to match:"
        )
        for problem in problems:
            print(f"  {problem}")
        return 1
    print(f"package versions are in lockstep ({npm}), and the displayed version matches")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
