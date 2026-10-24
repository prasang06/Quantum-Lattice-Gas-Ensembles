"""Thermodynamic observables from a cached spectrum (theory/06, Phase 3).

Means and fluctuations are evaluated directly from Boltzmann/grand weights. Heat
capacity and compressibility use the exact fluctuation identities
(``C_V = beta^2 Var(E)``, ``d<N>/dmu = beta Var(N)``) rather than numerically
differentiating the means -- no step-size error (theory/06 "why the fluctuation
formulas are preferred").
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from qlge.diagonalize import Spectrum
from qlge.ensembles import canonical_weights, grand_weights, log_Z


def _stable_variance(weights: np.ndarray, x: np.ndarray, mean: float) -> float:
    """Weighted variance via the centered form; clamp tiny negatives to 0."""
    var = float(np.sum(weights * (x - mean) ** 2))
    return max(var, 0.0)


# ----------------------------------------------------------------------------
# Canonical (fixed N, T)
# ----------------------------------------------------------------------------


@dataclass
class CanonicalResult:
    beta: np.ndarray
    energy: np.ndarray      # <E>_N
    var_energy: np.ndarray  # Var(E)_N
    heat_capacity: np.ndarray  # C_V = beta^2 Var(E)
    entropy: np.ndarray     # S = beta<E> + ln Z
    free_energy: np.ndarray  # F = -T ln Z


def canonical(spectrum: Spectrum, N: int, beta: np.ndarray) -> CanonicalResult:
    """Canonical observables of the N-sector over a beta grid."""
    energies = np.asarray(spectrum.eigenvalues[N], dtype=float)
    beta = np.atleast_1d(np.asarray(beta, dtype=float))

    lnZ = log_Z(energies, beta)  # (B,)
    E = np.empty_like(beta)
    var = np.empty_like(beta)
    for k, b in enumerate(beta):
        w = canonical_weights(energies, b)
        mean = float(np.sum(w * energies))
        E[k] = mean
        var[k] = _stable_variance(w, energies, mean)

    C = beta * beta * var
    S = beta * E + lnZ
    F = -lnZ / beta
    return CanonicalResult(
        beta=beta, energy=E, var_energy=var, heat_capacity=C, entropy=S, free_energy=F
    )


# ----------------------------------------------------------------------------
# Grand-canonical (fixed T, mu)
# ----------------------------------------------------------------------------


@dataclass
class GrandResult:
    mu: np.ndarray
    mean_N: np.ndarray
    var_N: np.ndarray
    mean_E: np.ndarray
    dNdmu: np.ndarray       # = beta Var(N)
    compressibility: np.ndarray  # kappa ~ Var(N) / <N>^2 (0 where <N>==0)


def grand(spectrum: Spectrum, beta: float, mu: np.ndarray) -> GrandResult:
    """Grand-canonical observables over a mu grid at fixed beta."""
    mu = np.atleast_1d(np.asarray(mu, dtype=float))
    mean_N = np.empty_like(mu)
    var_N = np.empty_like(mu)
    mean_E = np.empty_like(mu)
    for k, m in enumerate(mu):
        w, energies, numbers = grand_weights(spectrum, beta, float(m))
        nbar = float(np.sum(w * numbers))
        ebar = float(np.sum(w * energies))
        mean_N[k] = nbar
        var_N[k] = _stable_variance(w, numbers, nbar)
        mean_E[k] = ebar

    dNdmu = beta * var_N
    with np.errstate(divide="ignore", invalid="ignore"):
        kappa = np.where(mean_N > 0, var_N / mean_N**2, 0.0)
    return GrandResult(
        mu=mu, mean_N=mean_N, var_N=var_N, mean_E=mean_E, dNdmu=dNdmu, compressibility=kappa
    )


def mean_N_at(spectrum: Spectrum, beta: float, mu: float) -> float:
    """Mean particle number at scalar (beta, mu). Used by mu root-finding."""
    w, _, numbers = grand_weights(spectrum, beta, mu)
    return float(np.sum(w * numbers))
