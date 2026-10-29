"""Finite-size scaling as a function of temperature, over cached spectra.

Repeats the run_scaling.py study on a temperature grid: for each V and T it
fits each equivalence metric to M^p across the cached lattice sizes, and prints
the exponents next to the analytical baselines (benchmarks.py): the beta -> 0
binomial limit and, for attraction, the classical Onsager T_c.

Usage:
    python scripts/run_temperature_sweep.py
    python scripts/run_temperature_sweep.py --V -3 -2 0 2 --T 0.5 1 2 4 --csv data/tsweep.csv
"""

from __future__ import annotations

import argparse
import csv

import numpy as np

from qlge.benchmarks import ising_critical_temperature, phase_separates
from qlge.scaling import SCALING_METRICS, load_spectra_by_L, temperature_sweep


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--V", type=float, nargs="+", default=[-3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0])
    p.add_argument("--T", type=float, nargs="+", default=[0.25, 0.5, 1.0, 1.5, 2.0, 3.0, 5.0, 10.0])
    p.add_argument("--filling", type=float, default=0.5)
    p.add_argument("--bc", choices=["open", "periodic"], default="periodic")
    p.add_argument("--data-dir", default="data")
    p.add_argument("--csv", default=None, help="also write every (V, T) row to this CSV")
    args = p.parse_args()

    T = np.asarray(args.T, dtype=float)
    rows = []
    for V in args.V:
        spectra = load_spectra_by_L(V, args.bc, args.data_dir)
        if len(spectra) < 2:
            print(f"V={V:+g}: need >= 2 lattice sizes cached, found {sorted(spectra)}")
            continue
        sw = temperature_sweep(spectra, 1.0 / T, filling=args.filling)
        Mmax = max(spectra) ** 2

        note = ""
        if V < 0:
            note = (f"  classical T_c={ising_critical_temperature(V):.3f}; "
                    f"{'easy-axis (phase separates)' if phase_separates(V) else 'not easy-axis'}")
        print(f"\nV={V:+g}  L={sorted(spectra)}  filling={args.filling}  bc={args.bc}{note}")
        print(f"  {'T':>6} {'p(relE)':>8} {'p(relN)':>8} {'p(gap)':>8} {'relN@M=' + str(Mmax):>11}")
        for k, Tk in enumerate(T):
            print(
                f"  {Tk:6.2f} {sw['rel_energy_fluctuation'][k]:+8.3f} "
                f"{sw['rel_number_fluctuation'][k]:+8.3f} "
                f"{sw['energy_discrepancy_per_site'][k]:+8.3f} "
                f"{sw['rel_number_fluctuation_largest'][k]:11.4f}"
            )
            rows.append({"V": V, "T": Tk, **{f"p_{a}": sw[a][k] for a in SCALING_METRICS},
                         **{f"{a}_M{Mmax}": sw[a + "_largest"][k] for a in SCALING_METRICS}})

    if args.csv and rows:
        with open(args.csv, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
        print("\nwrote", args.csv)


if __name__ == "__main__":
    main()
