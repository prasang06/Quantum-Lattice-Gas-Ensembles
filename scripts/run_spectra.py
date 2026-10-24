"""Build and cache spectra for a grid of (V, L) models (PLAN.md Phase 2).

Usage:
    python scripts/run_spectra.py                  # default grid
    python scripts/run_spectra.py --L 2 3 --V 0 2  # custom grid
    python scripts/run_spectra.py --bc open

The expensive diagonalization runs here, once; downstream ensemble work and the
Streamlit app read the cached ``.npz`` files from ``data/``.
"""

from __future__ import annotations

import argparse
import time

from qlge.config import RunConfig
from qlge.diagonalize import default_cache_path, diagonalize


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--L", type=int, nargs="+", default=[2, 3])
    p.add_argument("--V", type=float, nargs="+", default=[0.0, 2.0, -2.0])
    p.add_argument("--t", type=float, default=1.0)
    p.add_argument("--bc", choices=["open", "periodic"], default="periodic")
    p.add_argument("--data-dir", default="data")
    args = p.parse_args()

    for L in args.L:
        for V in args.V:
            config = RunConfig(L=L, t=args.t, V=V, bc=args.bc)
            path = default_cache_path(config, args.data_dir)
            t0 = time.perf_counter()
            spectrum = diagonalize(config)
            spectrum.save(path)
            dt = time.perf_counter() - t0
            dims = {N: spectrum.dim(N) for N in spectrum.eigenvalues}
            biggest = max(dims.values())
            print(
                f"{config.tag():22s}  sectors={len(dims):2d}  "
                f"max_dim={biggest:6d}  E0={spectrum.ground_energy:+.4f}  "
                f"{dt:6.2f}s  -> {path}"
            )


if __name__ == "__main__":
    main()
