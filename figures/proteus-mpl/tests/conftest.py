"""Shared fixtures for the proteus-mpl tests."""

import matplotlib

matplotlib.use("Agg")

# Import pyplot once in this process; in-process pytester runs then share it.
import matplotlib.pyplot

pytest_plugins = ["pytester"]
