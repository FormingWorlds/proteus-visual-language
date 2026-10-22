"""Shared fixtures for the proteus-mpl tests."""

import matplotlib

matplotlib.use("Agg")

# Import pyplot once in this process, so in-process pytester runs share it; without
# it a nested run fails with "Single argument to subplot must be a three-digit integer".
import matplotlib.pyplot

pytest_plugins = ["pytester"]
