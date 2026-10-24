"""Animations over cached spectra and on-the-fly real-space states (Phase 6).

Matplotlib FuncAnimation scenes saved as GIF (portable). Three scenes:

  anim_realspace_vsweep  -- the physical system in real space as V/t sweeps:
                            site-occupation heatmap + nearest-neighbor
                            correlation. Visualizes clustering (attractive) vs
                            anti-bunching (repulsive). Open boundary conditions
                            so spatial structure is visible.
  anim_boltzmann_T       -- canonical energy distribution P(E) filling the
                            spectrum as temperature sweeps cold -> hot.
  anim_mu_tuning         -- grand-canonical filling <N>(mu)/M for several L, with
                            a moving marker; larger L converges to the
                            thermodynamic curve.

All physics comes from the qlge modules; animation adds no model logic.
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation, PillowWriter

from qlge.config import RunConfig
from qlge.diagonalize import Spectrum
from qlge.ensembles import canonical_weights
from qlge.observables import grand
from qlge.realspace import canonical_nn_correlation, canonical_site_density

plt.rcParams.update({"figure.dpi": 110, "font.size": 11})


def _save(anim, path: str, fps: int = 12) -> str:
    anim.save(path, writer=PillowWriter(fps=fps))
    plt.close(anim._fig)
    return path


# ---------------------------------------------------------------------------
# Hero: real-space physical system as the interaction V/t sweeps
# ---------------------------------------------------------------------------
def anim_realspace_vsweep(
    L: int = 3,
    N: int | None = None,
    beta: float = 2.0,
    V_values: np.ndarray | None = None,
    path: str = "animations/anim_realspace_vsweep.gif",
) -> str:
    if N is None:
        N = (L * L) // 2 + 1
    if V_values is None:
        V_values = np.concatenate([np.linspace(4, -4, 60), np.linspace(-4, 4, 60)])

    # Precompute all frames (cheap for small L, open BC).
    densities, corrs = [], []
    for V in V_values:
        cfg = RunConfig(L=L, V=float(V), bc="open")
        densities.append(canonical_site_density(cfg, N, beta))
        corrs.append(canonical_nn_correlation(cfg, N, beta))
    densities = np.array(densities)
    corrs = np.array(corrs)
    vmax = densities.max()

    fig, (axd, axc) = plt.subplots(1, 2, figsize=(11, 4.3))
    fig.subplots_adjust(wspace=0.5, bottom=0.15, top=0.86)
    im = axd.imshow(densities[0], vmin=0, vmax=vmax, cmap="inferno", origin="lower")
    cb = fig.colorbar(im, ax=axd, fraction=0.046, pad=0.04)
    cb.set_label(r"$\langle n_i\rangle$")
    axd.set_xticks(range(L)); axd.set_yticks(range(L))
    title = axd.set_title("")

    axc.axhline(0, color="gray", lw=0.8)
    axc.plot(V_values[:1], corrs[:1], color="#1f77b4")
    (corr_line,) = axc.plot([], [], color="#1f77b4", lw=2)
    (corr_dot,) = axc.plot([], [], "o", color="#d62728", ms=8)
    axc.set_xlim(V_values.min() - 0.3, V_values.max() + 0.3)
    axc.set_ylim(corrs.min() - 0.02, corrs.max() + 0.02)
    axc.set_xlabel(r"interaction $V/t$")
    axc.set_ylabel(r"nn correlation $\langle n_i n_j\rangle_c$")
    axc.set_title("clustering (+) vs anti-bunching (-)")
    fig.suptitle(
        rf"Real-space thermal state, $L={L}$, $N={N}$, $\beta t={beta:g}$ (open BC)",
        y=0.98,
    )

    # Build a monotone V-ordered trace for the correlation curve background.
    order = np.argsort(V_values)
    axc.plot(V_values[order], corrs[order], color="#9ecae1", lw=1, alpha=0.7, zorder=0)

    def update(k):
        im.set_data(densities[k])
        V = V_values[k]
        kind = "repulsive" if V > 0.3 else ("attractive" if V < -0.3 else "free")
        title.set_text(rf"$V/t={V:+.2f}$  ({kind})")
        corr_dot.set_data([V], [corrs[k]])
        return im, corr_dot, title

    anim = FuncAnimation(fig, update, frames=len(V_values), blit=False, interval=80)
    anim._fig = fig
    return _save(anim, path)


# ---------------------------------------------------------------------------
# Canonical P(E) filling the spectrum as temperature sweeps
# ---------------------------------------------------------------------------
def anim_boltzmann_T(
    spectrum: Spectrum,
    N: int,
    T_values: np.ndarray | None = None,
    path: str = "animations/anim_boltzmann_T.gif",
) -> str:
    if T_values is None:
        T_values = np.concatenate([np.linspace(0.1, 6, 50), np.linspace(6, 0.1, 50)])
    ev = np.sort(spectrum.eigenvalues[N])
    fig, ax = plt.subplots(figsize=(7.5, 4.3))
    fig.subplots_adjust(bottom=0.15, top=0.88)
    stems = ax.vlines(ev, 0, np.zeros_like(ev), color="#d62728", lw=2)
    ax.plot(ev, np.zeros_like(ev), "|", color="gray", ms=12, alpha=0.5)
    ax.set_xlim(ev.min() - 0.5, ev.max() + 0.5)
    ax.set_ylim(0, 1.05)
    ax.set_xlabel("energy $E/t$")
    ax.set_ylabel("Boltzmann weight $p_\\alpha$ (normalized to max)")
    title = ax.set_title("")
    fig.suptitle(
        rf"Canonical occupation of the spectrum, $L={spectrum.config.L}$, $N={N}$",
        y=0.97,
    )

    def update(k):
        T = T_values[k]
        w = canonical_weights(ev, 1.0 / T)
        w = w / w.max()
        segs = [[[e, 0], [e, wi]] for e, wi in zip(ev, w)]
        stems.set_segments(segs)
        title.set_text(rf"$T/t={T:.2f}$")
        return stems, title

    anim = FuncAnimation(fig, update, frames=len(T_values), blit=False, interval=90)
    anim._fig = fig
    return _save(anim, path)


# ---------------------------------------------------------------------------
# Grand-canonical filling vs mu for several L, with a moving marker
# ---------------------------------------------------------------------------
def anim_mu_tuning(
    spectra_by_L: dict[int, Spectrum],
    beta: float = 1.0,
    mu_values: np.ndarray | None = None,
    path: str = "animations/anim_mu_tuning.gif",
) -> str:
    if mu_values is None:
        mu_values = np.concatenate([np.linspace(-6, 6, 60), np.linspace(6, -6, 60)])
    mu_grid = np.linspace(-6, 6, 300)
    curves = {}
    cmap = plt.cm.plasma(np.linspace(0.15, 0.85, len(spectra_by_L)))
    fig, ax = plt.subplots(figsize=(7.5, 4.3))
    fig.subplots_adjust(bottom=0.15, top=0.88)
    dots = {}
    for c, L in zip(cmap, sorted(spectra_by_L)):
        spec = spectra_by_L[L]
        y = grand(spec, beta, mu_grid).mean_N / spec.config.n_sites
        curves[L] = (spec, y)
        ax.plot(mu_grid, y, color=c, label=f"$L={L}$")
        (dot,) = ax.plot([], [], "o", color=c, ms=9)
        dots[L] = dot
    vline = ax.axvline(mu_values[0], color="gray", lw=1, ls="--")
    ax.set_xlabel(r"chemical potential $\mu/t$")
    ax.set_ylabel(r"filling $\langle N\rangle/M$")
    ax.set_ylim(-0.02, 1.02)
    ax.legend(loc="upper left", frameon=False)
    title = ax.set_title("")
    fig.suptitle(rf"Grand-canonical filling, $\beta t={beta:g}$", y=0.97)

    def update(k):
        mu = mu_values[k]
        vline.set_xdata([mu, mu])
        for L, (spec, _) in curves.items():
            val = float(grand(spec, beta, np.array([mu])).mean_N[0] / spec.config.n_sites)
            dots[L].set_data([mu], [val])
        title.set_text(rf"$\mu/t={mu:+.2f}$")
        return (vline, title, *dots.values())

    anim = FuncAnimation(fig, update, frames=len(mu_values), blit=False, interval=90)
    anim._fig = fig
    return _save(anim, path)
