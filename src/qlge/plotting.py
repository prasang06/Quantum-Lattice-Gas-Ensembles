"""Static research figures over cached spectra (theory/06-07; PLAN.md Phase 6).

Each ``fig_*`` function builds one figure and returns it; ``save`` writes a PNG.
All physics is pulled from the ``qlge`` modules -- plotting adds no model logic.
Use a non-interactive backend so figures render headless.
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from qlge.diagonalize import Spectrum
from qlge.ensembles import entropy_micro
from qlge.matching import match_ensembles, micro_temperature
from qlge.observables import canonical, grand
from qlge.scaling import fit_power_law, scaling_sweep

# --- house style ------------------------------------------------------------
plt.rcParams.update(
    {
        "figure.dpi": 140,
        "savefig.dpi": 160,
        "font.size": 11,
        "axes.grid": True,
        "grid.alpha": 0.25,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "legend.frameon": False,
    }
)

_VCOLORS = {0.0: "#1f77b4", 2.0: "#d62728", -2.0: "#2ca02c"}


def _vlabel(V: float) -> str:
    kind = "free" if V == 0 else ("repulsive" if V > 0 else "attractive")
    return f"$V/t={V:+g}$ ({kind})"


def _vcolor(V: float, Vs) -> str:
    """Diverging color keyed by interaction: attractive->blue, repulsive->red.

    Falls back to the fixed palette when exactly the canonical {-2,0,+2} set is
    plotted (keeps earlier figures visually identical).
    """
    Vs = sorted(Vs)
    if set(Vs) <= {-2.0, 0.0, 2.0}:
        return _VCOLORS.get(V, "#333333")
    vmax = max(abs(min(Vs)), abs(max(Vs)), 1e-9)
    return plt.cm.coolwarm(0.5 + 0.5 * V / vmax)


def save(fig, path: str) -> str:
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------
# Figure 1 -- energy spectrum / density of states per N-sector
# ---------------------------------------------------------------------------
def fig_spectrum_dos(spectrum: Spectrum):
    fig, (ax0, ax1) = plt.subplots(1, 2, figsize=(11, 4.2))
    M = spectrum.config.n_sites
    sectors = sorted(spectrum.eigenvalues)
    cmap = plt.cm.viridis(np.linspace(0, 1, len(sectors)))

    for c, N in zip(cmap, sectors):
        ev = spectrum.eigenvalues[N]
        ax0.plot(np.full_like(ev, N), ev, ".", color=c, ms=3, alpha=0.6)
    ax0.set_xlabel("particle number $N$")
    ax0.set_ylabel("energy $E/t$")
    ax0.set_title(f"Spectrum per sector ({spectrum.config.tag()})")

    allE = spectrum.all_eigenvalues()
    ax1.hist(allE, bins=min(60, max(10, allE.size // 20)), color="#444", alpha=0.85)
    ax1.set_xlabel("energy $E/t$")
    ax1.set_ylabel("density of states")
    ax1.set_title("Total density of states")
    ax1.grid(axis="x", alpha=0.0)
    fig.suptitle(f"Hard-core Bose-Hubbard, $L={spectrum.config.L}$, $M={M}$", y=1.02)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Figure 2 -- heat capacity C_V(T), free vs interacting
# ---------------------------------------------------------------------------
def fig_heat_capacity(spectra: dict[float, Spectrum], N: int, T=None):
    if T is None:
        T = np.linspace(0.05, 6.0, 400)
    beta = 1.0 / T
    fig, ax = plt.subplots(figsize=(6.2, 4.4))
    for V, spec in sorted(spectra.items()):
        res = canonical(spec, N, beta)
        ax.plot(T, res.heat_capacity, color=_VCOLORS.get(V, None), label=_vlabel(V))
    ax.set_xlabel("temperature $T/t$")
    ax.set_ylabel("heat capacity $C_V$")
    any_spec = next(iter(spectra.values()))
    ax.set_title(f"Canonical heat capacity, $L={any_spec.config.L}$, $N={N}$")
    ax.legend()
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Figure 3 -- <N>(mu) staircase sharpening with L
# ---------------------------------------------------------------------------
def fig_mu_staircase(spectra_by_L: dict[int, Spectrum], beta: float, mu=None):
    if mu is None:
        mu = np.linspace(-6, 6, 400)
    fig, ax = plt.subplots(figsize=(6.2, 4.4))
    cmap = plt.cm.plasma(np.linspace(0.15, 0.85, len(spectra_by_L)))
    for c, L in zip(cmap, sorted(spectra_by_L)):
        spec = spectra_by_L[L]
        res = grand(spec, beta, mu)
        ax.plot(mu, res.mean_N / spec.config.n_sites, color=c, label=f"$L={L}$ ($M={spec.config.n_sites}$)")
    ax.set_xlabel(r"chemical potential $\mu/t$")
    ax.set_ylabel(r"filling $\langle N\rangle / M$")
    ax.set_title(rf"Grand-canonical filling, $\beta t={beta:g}$")
    ax.legend()
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Figure 4 -- number fluctuations & compressibility vs mu
# ---------------------------------------------------------------------------
def fig_number_fluctuations(spectrum: Spectrum, beta: float, mu=None):
    if mu is None:
        mu = np.linspace(-6, 6, 400)
    res = grand(spectrum, beta, mu)
    fig, (ax0, ax1) = plt.subplots(1, 2, figsize=(11, 4.2))
    ax0.plot(mu, res.var_N, color="#8c564b")
    ax0.set_xlabel(r"$\mu/t$"); ax0.set_ylabel(r"$\mathrm{Var}(N)$")
    ax0.set_title("Number fluctuations")
    ax1.plot(mu, res.compressibility, color="#9467bd")
    ax1.set_xlabel(r"$\mu/t$"); ax1.set_ylabel(r"$\kappa \sim \mathrm{Var}(N)/\langle N\rangle^2$")
    ax1.set_title("Compressibility")
    fig.suptitle(
        rf"Grand-canonical, $L={spectrum.config.L}$, {_vlabel(spectrum.config.V)}, $\beta t={beta:g}$",
        y=1.02,
    )
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Figure 5 -- ensemble energy comparison: canonical vs grand vs T
# ---------------------------------------------------------------------------
def fig_energy_ensembles(spectrum: Spectrum, N: int, T=None):
    if T is None:
        T = np.linspace(0.1, 6.0, 120)
    beta = 1.0 / T
    can = canonical(spectrum, N, beta)
    E_grand = np.empty_like(T)
    for k, b in enumerate(beta):
        r = match_ensembles(spectrum, N, float(b))
        E_grand[k] = r.energy_grand
    fig, ax = plt.subplots(figsize=(6.2, 4.4))
    ax.plot(T, can.energy / spectrum.config.n_sites, "-", color="#1f77b4", label="canonical $\\langle E\\rangle_N$")
    ax.plot(T, E_grand / spectrum.config.n_sites, "--", color="#d62728", label="grand-canonical (matched $\\langle N\\rangle=N$)")
    ax.set_xlabel("temperature $T/t$")
    ax.set_ylabel(r"energy per site $\langle E\rangle / M$")
    ax.set_title(
        rf"Ensemble energy, $L={spectrum.config.L}$, $N={N}$, {_vlabel(spectrum.config.V)}"
    )
    ax.legend()
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Figure 6 -- finite-size scaling of equivalence metrics (the headline)
# ---------------------------------------------------------------------------
def fig_scaling(spectra_by_V_L: dict[float, dict[int, Spectrum]], beta: float, filling=0.5,
                family: str = ""):
    metrics = [
        ("rel_energy_fluctuation", r"$\sigma_E/|\langle E\rangle|$"),
        ("rel_number_fluctuation", r"$\sigma_N/\langle N\rangle$"),
        ("energy_discrepancy_per_site", r"$|\Delta\langle E\rangle|/M$"),
    ]
    Vs = sorted(spectra_by_V_L)
    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.3))
    for ax, (attr, label) in zip(axes, metrics):
        for V in Vs:
            spectra = spectra_by_V_L[V]
            pts = scaling_sweep(spectra, beta=beta, filling=filling)
            M = np.array([p.M for p in pts], float)
            y = np.array([getattr(p, attr) for p in pts], float)
            color = _vcolor(V, Vs)
            # One legend entry per V, carrying the fitted exponent.
            try:
                fit = fit_power_law(M, y)
                mm = np.linspace(M.min(), M.max(), 50)
                ax.loglog(mm, fit.predict(mm), "-", color=color, alpha=0.6)
                lab = f"$V/t={V:+g}$ ($M^{{{fit.exponent:+.2f}}}$)"
            except ValueError:
                lab = f"$V/t={V:+g}$"
            ax.loglog(M, y, "o", color=color, label=lab)
        ax.set_xlabel("system size $M$ (sites)")
        ax.set_ylabel(label)
        ax.set_title(label)
        ax.legend(fontsize=7, ncol=1)
    fig.suptitle(
        rf"Emergence of ensemble equivalence with size{family}, $\beta t={beta:g}$, filling $={filling:g}$",
        y=1.03,
    )
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Figure 7 -- interaction dependence of equivalence metrics
# ---------------------------------------------------------------------------
def fig_interaction_dependence(spectra_by_V_L: dict[float, dict[int, Spectrum]], beta: float, filling=0.5):
    Vs = sorted(spectra_by_V_L)
    fig, ax = plt.subplots(figsize=(6.4, 4.4))
    for attr, label, marker in [
        ("rel_energy_fluctuation", r"$\sigma_E/|\langle E\rangle|$", "o"),
        ("rel_number_fluctuation", r"$\sigma_N/\langle N\rangle$", "s"),
        ("energy_discrepancy_per_site", r"$|\Delta\langle E\rangle|/M$", "^"),
    ]:
        # Use the largest available L per V.
        vals = []
        for V in Vs:
            spectra = spectra_by_V_L[V]
            Lmax = max(spectra)
            pts = scaling_sweep({Lmax: spectra[Lmax]}, beta=beta, filling=filling)
            vals.append(getattr(pts[0], attr))
        ax.plot(Vs, vals, marker + "-", label=label)
    ax.set_xlabel("interaction $V/t$")
    ax.set_ylabel("equivalence discrepancy (largest $L$)")
    ax.set_title(rf"Interaction dependence, $\beta t={beta:g}$, filling $={filling:g}$")
    ax.legend()
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Figure 8 -- canonical entropy per site vs temperature, free vs interacting
# ---------------------------------------------------------------------------
def fig_entropy_temperature(spectra: dict[float, Spectrum], N: int, T=None):
    if T is None:
        T = np.linspace(0.05, 8.0, 400)
    beta = 1.0 / T
    fig, ax = plt.subplots(figsize=(6.4, 4.4))
    for V, spec in sorted(spectra.items()):
        res = canonical(spec, N, beta)
        M = spec.config.n_sites
        ax.plot(T, res.entropy / M, color=_VCOLORS.get(V, None), label=_vlabel(V))
        ax.axhline(np.log(spec.dim(N)) / M, color=_VCOLORS.get(V, None), ls=":", lw=1, alpha=0.6)
    any_spec = next(iter(spectra.values()))
    ax.set_xlabel("temperature $T/t$")
    ax.set_ylabel(r"entropy per site $S/M$")
    ax.set_title(rf"Canonical entropy, $L={any_spec.config.L}$, $N={N}$ "
                 rf"(dotted: $\ln(\dim)/M$)")
    ax.legend()
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Figure 9 -- entropy per site converging with L (thermodynamic limit)
# ---------------------------------------------------------------------------
def fig_entropy_convergence(spectra_by_L: dict[int, Spectrum], filling=0.5, T=None):
    if T is None:
        T = np.linspace(0.05, 8.0, 400)
    beta = 1.0 / T
    fig, ax = plt.subplots(figsize=(6.4, 4.4))
    cmap = plt.cm.viridis(np.linspace(0.15, 0.85, len(spectra_by_L)))
    for c, L in zip(cmap, sorted(spectra_by_L)):
        spec = spectra_by_L[L]
        M = spec.config.n_sites
        N = max(1, min(M - 1, round(filling * M)))
        res = canonical(spec, N, beta)
        ax.plot(T, res.entropy / M, color=c, label=f"$L={L}$ ($M={M}$)")
    ax.set_xlabel("temperature $T/t$")
    ax.set_ylabel(r"entropy per site $S/M$")
    ax.set_title(rf"Entropy per site vs size (filling $={filling:g}$)")
    ax.legend()
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Figure 10 -- microcanonical entropy S(E)=ln Omega: window & jaggedness
# ---------------------------------------------------------------------------
def fig_microcanonical_entropy(spectrum: Spectrum, N: int, dE_list=(0.25, 0.75, 1.5)):
    ev = np.sort(spectrum.eigenvalues[N])
    fig, ax = plt.subplots(figsize=(6.4, 4.4))
    for dE in dE_list:
        E = np.arange(ev.min(), ev.max(), dE / 2)
        S = entropy_micro(ev, E, dE)  # NaN where Omega==0
        ax.plot(E + dE / 2, S, ".-", ms=4, lw=1, label=rf"$\Delta E={dE:g}$")
    ax.set_xlabel("energy $E/t$")
    ax.set_ylabel(r"microcanonical $S=\ln\Omega$")
    ax.set_title(rf"Microcanonical entropy, $L={spectrum.config.L}$, $N={N}$ "
                 rf"(window-dependent, jagged)")
    ax.legend(title="energy window")
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Figure 11 -- caloric curve: smooth canonical T(E) vs noisy microcanonical
# ---------------------------------------------------------------------------
def fig_caloric_curve(spectrum: Spectrum, N: int, dE=0.75, T=None):
    if T is None:
        T = np.linspace(0.1, 8.0, 300)
    can = canonical(spectrum, N, 1.0 / T)  # smooth E(T) -> parametric caloric
    ev = np.sort(spectrum.eigenvalues[N])
    # Microcanonical finite-difference temperature at window centers.
    Ec = np.arange(ev.min() + dE, ev.max() - dE, dE / 2)
    Tm = np.array([micro_temperature(spectrum, N, float(e), dE) for e in Ec])
    fig, ax = plt.subplots(figsize=(6.4, 4.4))
    ax.plot(can.energy, T, "-", color="#1f77b4", lw=2, label="canonical (smooth)")
    finite = np.isfinite(Tm)
    ax.plot(Ec[finite], Tm[finite], "x", color="#d62728", ms=7,
            label=r"microcanonical $1/(\partial S/\partial E)$")
    ax.axhline(0, color="gray", lw=0.8)
    ax.set_xlabel("energy $E/t$")
    ax.set_ylabel("temperature $T/t$")
    ax.set_title(rf"Caloric curve, $L={spectrum.config.L}$, $N={N}$ "
                 rf"($\Delta E={dE:g}$): micro is brittle")
    ax.legend()
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Figure 12 -- dense interaction sweep at fixed L (many V points)
# ---------------------------------------------------------------------------
def fig_interaction_sweep(L=3, beta=1.0, filling=0.5, V_array=None, bc="open"):
    """Equivalence metrics vs V/t on a dense grid, at fixed L (diagonalized here).

    Cheap for small L (L=3 is instant), so this gives the fine interaction
    resolution that the cached {0,+2,-2} grid cannot.
    """
    from qlge.config import RunConfig
    from qlge.diagonalize import diagonalize
    from qlge.matching import match_ensembles

    if V_array is None:
        V_array = np.linspace(-4.0, 4.0, 33)
    M = L * L
    N = max(1, min(M - 1, round(filling * M)))
    rE, rN, gap = [], [], []
    for V in V_array:
        spec = diagonalize(RunConfig(L=L, V=float(V), bc=bc))
        r = match_ensembles(spec, N, beta)
        rE.append(r.rel_energy_fluctuation)
        rN.append(r.rel_number_fluctuation)
        gap.append(r.energy_discrepancy_per_site)

    fig, ax = plt.subplots(figsize=(6.6, 4.4))
    ax.plot(V_array, rE, "-o", ms=3, color="#1f77b4", label=r"$\sigma_E/|\langle E\rangle|$")
    ax.plot(V_array, rN, "-s", ms=3, color="#d62728", label=r"$\sigma_N/\langle N\rangle$")
    ax.plot(V_array, gap, "-^", ms=3, color="#2ca02c", label=r"$|\Delta\langle E\rangle|/M$")
    ax.axvline(0, color="gray", lw=0.8, ls="--")
    ax.set_xlabel(r"interaction $V/t$")
    ax.set_ylabel("equivalence discrepancy")
    ax.set_title(rf"Dense interaction sweep, $L={L}$, $N={N}$, $\beta t={beta:g}$ ({bc} BC)")
    ax.legend()
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Figure 13 -- finite-size exponents as a function of temperature
# ---------------------------------------------------------------------------
def fig_temperature_exponents(sweeps: dict[float, dict[str, np.ndarray]], filling=0.5,
                              family: str = ""):
    """Fitted exponent p (metric ~ M^p) of each equivalence metric versus T.

    ``sweeps`` maps V -> :func:`qlge.scaling.temperature_sweep` output. Dotted
    verticals mark the classical (t = 0) Onsager T_c for attractive couplings.
    """
    from qlge.benchmarks import ising_critical_temperature

    metrics = [
        ("rel_number_fluctuation", r"$p(\sigma_N/\langle N\rangle)$"),
        ("energy_discrepancy_per_site", r"$p(|\Delta\langle E\rangle|/M)$"),
        ("rel_energy_fluctuation", r"$p(\sigma_E/|\langle E\rangle|)$"),
    ]
    Vs = sorted(sweeps)
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.3), sharex=True)
    for ax, (attr, label) in zip(axes, metrics):
        for V in Vs:
            sw = sweeps[V]
            ax.semilogx(1.0 / sw["beta"], sw[attr], "-", color=_vcolor(V, Vs), label=f"$V/t={V:+g}$")
            if V < 0 and attr == "rel_number_fluctuation":
                ax.axvline(ising_critical_temperature(V), color=_vcolor(V, Vs), ls=":", lw=1)
        ax.axhline(-0.5, color="gray", lw=0.8, ls="--")
        ax.axhline(0.0, color="black", lw=0.6)
        ax.set_xlabel("temperature $T/t$")
        ax.set_ylabel(label)
        ax.set_title(label)
    axes[0].legend(fontsize=7)
    fig.suptitle(
        rf"Finite-size exponents vs temperature{family} "
        rf"($M={','.join(str(m) for m in next(iter(sweeps.values()))['M'])}$, filling $={filling:g}$; "
        r"dashed: $M^{-1/2}$, dotted: classical Onsager $T_c$)" "\n"
        r"spikes in the middle and right panels are where the metric crosses zero "
        r"($\langle E\rangle$ or $\Delta\langle E\rangle$ changes sign), not physics",
        y=1.03,
    )
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Figure 14 -- number channel vs T against analytical baselines, and (V, T) map
# ---------------------------------------------------------------------------
def fig_number_channel_temperature(sweeps: dict[float, dict[str, np.ndarray]], M_largest: int,
                                   filling=0.5):
    """Left: sigma_N/<N> on the largest lattice vs T, with the beta -> 0 binomial
    limit and the classical (t = 0) Ising prediction for V < 0. Right: the
    number-channel exponent over the (V, T) plane; its zero contour separates
    convergence from the phase-separation anomaly.
    """
    from qlge.benchmarks import (
        heisenberg_number_fluctuation,
        infinite_temperature_number_fluctuation,
        ising_critical_temperature,
        ising_number_fluctuation,
    )

    Vs = sorted(sweeps)
    T = 1.0 / sweeps[Vs[0]]["beta"]
    fig, (ax0, ax1) = plt.subplots(1, 2, figsize=(13, 4.6))

    Tfine = np.geomspace(T.min(), T.max(), 400)
    for V in Vs:
        color = _vcolor(V, Vs)
        ax0.semilogx(T, sweeps[V]["rel_number_fluctuation_largest"], "-", color=color,
                     label=f"$V/t={V:+g}$")
        if V < 0:
            ax0.semilogx(Tfine, ising_number_fluctuation(V, Tfine), "--", color=color, lw=1)
        if V == -2.0 and M_largest % 2 == 0:
            ax0.plot(T[T < 1.0], np.full((T < 1.0).sum(), float(heisenberg_number_fluctuation(M_largest))),
                     "-.", color="black", lw=1, label=r"$V=-2t$, $T\to0$: $\sqrt{(M+2)/3M}$")
    N = max(1, min(M_largest - 1, round(filling * M_largest)))
    ax0.axhline(float(infinite_temperature_number_fluctuation(M_largest, N)), color="gray",
                lw=0.8, ls=":", label=r"$\beta\to0$ binomial")
    ax0.set_xlabel("temperature $T/t$")
    ax0.set_ylabel(rf"$\sigma_N/\langle N\rangle$ at $M={M_largest}$")
    ax0.set_title("Number fluctuation (dashed: classical Ising, $M\\to\\infty$)")
    ax0.legend(fontsize=7)

    P = np.array([sweeps[V]["rel_number_fluctuation"] for V in Vs])  # (V, T)
    vmax = np.nanmax(np.abs(P))
    mesh = ax1.pcolormesh(np.array(Vs), T, P.T, shading="nearest", cmap="RdBu_r",
                          vmin=-vmax, vmax=vmax)
    ax1.contour(np.array(Vs), T, P.T, levels=[0.0], colors="black", linewidths=1.5)
    # Classical T_c, clipped to the plotted temperature range (it -> 0 at V = 0).
    Vneg = np.linspace(min(Vs), 0, 200)
    Tc = np.array([ising_critical_temperature(v) for v in Vneg])
    keep = Tc >= T.min()
    ax1.plot(Vneg[keep], Tc[keep], "k--", lw=1, label=r"classical $T_c=0.567|V|$")
    ax1.set_ylim(T.min(), T.max())
    ax1.axvline(-2.0, color="black", ls=":", lw=1, label=r"Heisenberg point $V=-2t$")
    ax1.set_yscale("log")
    ax1.set_xlabel("interaction $V/t$")
    ax1.set_ylabel("temperature $T/t$")
    ax1.set_title(r"Exponent $p(\sigma_N/\langle N\rangle)$ (solid: $p=0$)")
    ax1.legend(fontsize=7, loc="upper right")
    fig.colorbar(mesh, ax=ax1, label="$p$")
    fig.tight_layout()
    return fig
