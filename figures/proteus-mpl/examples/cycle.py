"""Render the categorical cycle on each surface variant.

Regenerates the example figures committed next to this script:

    python examples/cycle.py

Writes cycle_light.png, cycle_dark.png, and cycle_white.png into the
script's directory, one 9-line (light/white) or 6-line (dark) plot per
surface, so the cycle and fonts are visible directly in the repository.
"""

from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

import proteus_mpl

HERE = Path(__file__).parent


def render(variant: str, path: Path) -> None:
    """Render one demo figure for a surface variant.

    Parameters
    ----------
    variant : {"light", "dark", "white"}
        Surface variant passed to ``proteus_mpl.use``.
    path : Path
        Output PNG path.
    """
    proteus_mpl.use(variant)
    cycle = proteus_mpl.CYCLE_DARK if variant == "dark" else proteus_mpl.CYCLE
    x = np.linspace(0.0, 10.0, 300)
    fig, ax = plt.subplots(figsize=(8, 5))
    for i in range(len(cycle)):
        y = np.sin(x - 0.55 * i) * np.exp(-x / 15.0) + 0.35 * (len(cycle) - i)
        ax.plot(x, y, label=f"series {i + 1}")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_title(f"categorical cycle, {variant}")
    ax.legend(ncol=3, fontsize=10)
    fig.savefig(path, dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    for variant in ("light", "dark", "white"):
        out = HERE / f"cycle_{variant}.png"
        render(variant, out)
        print(f"wrote {out}")
