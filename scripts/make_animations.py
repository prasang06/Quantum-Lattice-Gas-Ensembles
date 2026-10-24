"""Regenerate all animations (PLAN.md Phase 6).

Real-space scene is computed on the fly (small L, open BC); thermodynamic scenes
read cached spectra from data/. Output GIFs land in animations/.
"""

from __future__ import annotations

import argparse
import os

from qlge import animate as A
from qlge.scaling import load_spectra_by_L


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--bc", choices=["open", "periodic"], default="periodic")
    p.add_argument("--beta", type=float, default=1.0)
    p.add_argument("--data-dir", default="data")
    p.add_argument("--out", default="animations")
    p.add_argument("--only", nargs="+", choices=["realspace", "boltzmann", "mu"], default=None)
    args = p.parse_args()
    os.makedirs(args.out, exist_ok=True)
    want = set(args.only) if args.only else {"realspace", "boltzmann", "mu"}

    if "realspace" in want:
        print("rendering real-space V-sweep ...")
        print("  ->", A.anim_realspace_vsweep(L=3, beta=2.0, path=f"{args.out}/anim_realspace_vsweep.gif"))

    if "boltzmann" in want:
        free = load_spectra_by_L(0.0, args.bc, args.data_dir)
        if free:
            Lmax = max(free)
            spec = free[Lmax]
            N = spec.config.n_sites // 2
            print("rendering Boltzmann-vs-T ...")
            print("  ->", A.anim_boltzmann_T(spec, N, path=f"{args.out}/anim_boltzmann_T.gif"))

    if "mu" in want:
        free = load_spectra_by_L(0.0, args.bc, args.data_dir)
        if len(free) >= 2:
            print("rendering mu-tuning ...")
            print("  ->", A.anim_mu_tuning(free, beta=args.beta, path=f"{args.out}/anim_mu_tuning.gif"))


if __name__ == "__main__":
    main()
