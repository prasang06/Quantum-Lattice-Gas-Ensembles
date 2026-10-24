"""Finite-size scaling study over cached spectra (PLAN.md Phase 5).

Reads cached spectra from ``data/`` (build them first with run_spectra.py),
sweeps L at matched filling and beta for each V, and prints the ensemble
discrepancy metrics plus their power-law fits in M = L^2.

Usage:
    python scripts/run_scaling.py
    python scripts/run_scaling.py --V 0 2 -2 --beta 1.0 --filling 0.5 --bc periodic
"""

from __future__ import annotations

import argparse

import numpy as np

from qlge.scaling import fit_power_law, load_spectra_by_L, scaling_sweep


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--V", type=float, nargs="+", default=[0.0, 2.0, -2.0])
    p.add_argument("--beta", type=float, default=1.0)
    p.add_argument("--filling", type=float, default=0.5)
    p.add_argument("--bc", choices=["open", "periodic"], default="periodic")
    p.add_argument("--data-dir", default="data")
    args = p.parse_args()

    for V in args.V:
        spectra = load_spectra_by_L(V, args.bc, args.data_dir)
        if len(spectra) < 2:
            print(f"V={V:+g}: need >= 2 lattice sizes cached, found {sorted(spectra)}")
            continue
        pts = scaling_sweep(spectra, beta=args.beta, filling=args.filling)

        print(f"\nV={V:+g}  beta={args.beta}  filling={args.filling}  bc={args.bc}")
        print(f"  {'L':>2} {'M':>3} {'N':>2} {'relE':>8} {'relN':>8} {'dEgap/site':>11}")
        for pt in pts:
            print(
                f"  {pt.L:2d} {pt.M:3d} {pt.N:2d} "
                f"{pt.rel_energy_fluctuation:8.4f} {pt.rel_number_fluctuation:8.4f} "
                f"{pt.energy_discrepancy_per_site:11.4f}"
            )

        M = np.array([pt.M for pt in pts])
        for label, getter in [
            ("relE", lambda p: p.rel_energy_fluctuation),
            ("relN", lambda p: p.rel_number_fluctuation),
            ("dEgap/site", lambda p: p.energy_discrepancy_per_site),
        ]:
            y = np.array([getter(pt) for pt in pts])
            try:
                fit = fit_power_law(M, y)
                print(
                    f"    fit {label:11s} ~ M^{fit.exponent:+.3f} "
                    f"(amp={fit.amplitude:.3f}, R^2={fit.r_squared:.3f})"
                )
            except ValueError as e:
                print(f"    fit {label:11s} skipped: {e}")


if __name__ == "__main__":
    main()
