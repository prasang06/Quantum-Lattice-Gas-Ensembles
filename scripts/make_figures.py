"""Regenerate all static figures from cached spectra (PLAN.md Phase 6).

Build spectra first with scripts/run_spectra.py. Figures land in figures/.
``--family tilted`` instead draws the scaling figures (6, 13, 14) on the
bipartite tilted clusters, as fig6b/fig13b/fig14b.
"""

from __future__ import annotations

import argparse
import os

import numpy as np

from qlge import plotting as P
from qlge.scaling import load_cluster_spectra, load_spectra_by_L, temperature_sweep


def tilted_figures(args) -> None:
    """Scaling figures on the bipartite tilted clusters (M = 8, 10, 16, 18, 20)."""
    by_V_M = {V: load_cluster_spectra(V, data_dir=args.data_dir) for V in args.V}
    by_V_M = {V: d for V, d in by_V_M.items() if len(d) >= 2}
    if not by_V_M:
        raise SystemExit("no cached cluster spectra; run scripts/run_spectra.py --clusters ...")
    label = ", tilted bipartite clusters"
    T = np.geomspace(args.T_min, args.T_max, args.T_num)
    sweeps = {V: temperature_sweep(d, 1.0 / T, args.filling) for V, d in by_V_M.items()}
    M_largest = min(max(d) for d in by_V_M.values())
    out = [
        P.save(P.fig_scaling(by_V_M, args.beta, args.filling, family=label),
               f"{args.out}/fig6b_scaling_tilted.png"),
        P.save(P.fig_temperature_exponents(sweeps, args.filling, family=label),
               f"{args.out}/fig13b_temperature_exponents_tilted.png"),
        P.save(P.fig_number_channel_temperature(sweeps, M_largest, args.filling),
               f"{args.out}/fig14b_number_channel_temperature_tilted.png"),
    ]
    for pth in out:
        print("wrote", pth)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--V", type=float, nargs="+", default=[0.0, 2.0, -2.0])
    p.add_argument("--bc", choices=["open", "periodic"], default="periodic")
    p.add_argument("--beta", type=float, default=1.0)
    p.add_argument("--filling", type=float, default=0.5)
    p.add_argument("--data-dir", default="data")
    p.add_argument("--out", default="figures")
    p.add_argument("--T-min", type=float, default=0.2)
    p.add_argument("--T-max", type=float, default=10.0)
    p.add_argument("--T-num", type=int, default=40)
    p.add_argument("--family", choices=["square", "tilted"], default="square")
    args = p.parse_args()
    os.makedirs(args.out, exist_ok=True)

    if args.family == "tilted":
        return tilted_figures(args)

    # spectra_by_V_L[V][L] = Spectrum
    by_V_L = {V: load_spectra_by_L(V, args.bc, args.data_dir) for V in args.V}
    by_V_L = {V: d for V, d in by_V_L.items() if d}
    if not by_V_L:
        raise SystemExit("no cached spectra found; run scripts/run_spectra.py first")

    V0 = 0.0 if 0.0 in by_V_L else sorted(by_V_L)[0]
    Lmax = max(by_V_L[V0])
    spec_big = by_V_L[V0][Lmax]
    N_half = max(1, min(spec_big.config.n_sites - 1, round(args.filling * spec_big.config.n_sites)))

    out = []
    # 1. spectrum + DOS for the largest free lattice
    out.append(P.save(P.fig_spectrum_dos(spec_big), f"{args.out}/fig1_spectrum_dos.png"))

    # 2. heat capacity, free vs interacting, at largest common L
    common_L = set.intersection(*[set(d) for d in by_V_L.values()])
    Lc = max(common_L)
    spectra_at_Lc = {V: by_V_L[V][Lc] for V in by_V_L}
    N_c = max(1, min(Lc * Lc - 1, round(args.filling * Lc * Lc)))
    out.append(P.save(P.fig_heat_capacity(spectra_at_Lc, N_c), f"{args.out}/fig2_heat_capacity.png"))

    # 3. mu staircase sharpening with L (free)
    out.append(P.save(P.fig_mu_staircase(by_V_L[V0], args.beta), f"{args.out}/fig3_mu_staircase.png"))

    # 4. number fluctuations & compressibility (largest free lattice)
    out.append(P.save(P.fig_number_fluctuations(spec_big, args.beta), f"{args.out}/fig4_number_fluctuations.png"))

    # 5. ensemble energy comparison (largest common L, free)
    out.append(P.save(P.fig_energy_ensembles(by_V_L[V0][Lc], N_c), f"{args.out}/fig5_energy_ensembles.png"))

    # 6. finite-size scaling of equivalence metrics (headline)
    out.append(P.save(P.fig_scaling(by_V_L, args.beta, args.filling), f"{args.out}/fig6_scaling.png"))

    # 7. interaction dependence
    out.append(P.save(P.fig_interaction_dependence(by_V_L, args.beta, args.filling), f"{args.out}/fig7_interaction.png"))

    # 8. canonical entropy per site vs T, free vs interacting (largest common L)
    out.append(P.save(P.fig_entropy_temperature(spectra_at_Lc, N_c), f"{args.out}/fig8_entropy_temperature.png"))

    # 9. entropy per site converging with L (free)
    out.append(P.save(P.fig_entropy_convergence(by_V_L[V0], args.filling), f"{args.out}/fig9_entropy_convergence.png"))

    # 10. microcanonical entropy S(E)=ln Omega: window dependence / jaggedness
    out.append(P.save(P.fig_microcanonical_entropy(spec_big, N_half), f"{args.out}/fig10_micro_entropy.png"))

    # 11. caloric curve: smooth canonical T(E) vs brittle microcanonical
    out.append(P.save(P.fig_caloric_curve(spec_big, N_half), f"{args.out}/fig11_caloric_curve.png"))

    # 12. dense interaction sweep at fixed L (diagonalized on the fly; L=3 fast)
    out.append(P.save(P.fig_interaction_sweep(L=3, beta=args.beta, filling=args.filling),
                      f"{args.out}/fig12_interaction_sweep.png"))

    # 13-14. temperature axis: exponents vs T and the number channel vs baselines
    multi = {V: d for V, d in by_V_L.items() if len(d) >= 2}
    if multi:
        T = np.geomspace(args.T_min, args.T_max, args.T_num)
        sweeps = {V: temperature_sweep(d, 1.0 / T, args.filling) for V, d in multi.items()}
        out.append(P.save(P.fig_temperature_exponents(sweeps, args.filling),
                          f"{args.out}/fig13_temperature_exponents.png"))
        M_largest = min(max(d) for d in multi.values()) ** 2
        out.append(P.save(P.fig_number_channel_temperature(sweeps, M_largest, args.filling),
                          f"{args.out}/fig14_number_channel_temperature.png"))

    for pth in out:
        print("wrote", pth)


if __name__ == "__main__":
    main()
