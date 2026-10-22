"""Shared fixtures for the proteus-mpl tests."""

import matplotlib

matplotlib.use("Agg")

pytest_plugins = ["pytester"]
