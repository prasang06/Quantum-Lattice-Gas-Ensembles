"""Statistical-mechanical sums over a cached spectrum (theory/05, Phase 3).

Low-level, overflow-safe building blocks shared by all three ensembles. Every
partition function is evaluated with a log-sum-exp shift (theory/08 "overflow-safe
partition functions") -- the single most common bug source in finite-T ED.

Conventions: ``k_B = 1``, ``beta = 1/T``. Functions accept scalar or array
``beta`` / ``mu`` and broadcast.
"""

from __future__ import annotations

import numpy as np
from scipy.special import logsumexp

from qlge.diagonalize import Spectrum

# ----------------------------------------------------------------------------
# Canonical ensemble (fixed N): Z_N(beta) = sum_alpha exp(-beta E_{N,alpha})
# ----------------------------------------------------------------------------


def log_Z(energies: np.ndarray, beta: np.ndarray | float) -> np.ndarray:
    """ln Z_N(beta) for one sector, computed stably via log-sum-exp.

    Parameters
    ----------
    energies : (d,) array
        Eigenvalues of the sector.
    beta : scalar or (B,) array
        Inverse temperature(s).

    Returns
    -------
    scalar or (B,) array of ln Z.
    """
    energies = np.asarray(energies, dtype=float)
    beta = np.asarray(beta, dtype=float)
    # exponent[..., i] = -beta * E_i ; logsumexp over the last axis.
    expo = -np.multiply.outer(beta, energies)
    return logsumexp(expo, axis=-1)


def canonical_weights(energies: np.ndarray, beta: float) -> np.ndarray:
    """Boltzmann weights p_alpha = exp(-beta E_alpha) / Z_N for scalar beta."""
    energies = np.asarray(energies, dtype=float)
    expo = -beta * energies
    expo -= expo.max()
    w = np.exp(expo)
    return w / w.sum()


# ----------------------------------------------------------------------------
# Grand-canonical ensemble (fixed mu): Xi = sum_N exp(beta mu N) Z_N(beta)
# ----------------------------------------------------------------------------


def _stacked_spectrum(spectrum: Spectrum) -> tuple[np.ndarray, np.ndarray]:
    """Flatten a Spectrum to (energies, particle_numbers) aligned arrays."""
    energies = []
    numbers = []
    for N, ev in spectrum.eigenvalues.items():
        energies.append(ev)
        numbers.append(np.full(ev.shape, N, dtype=float))
    return np.concatenate(energies), np.concatenate(numbers)


def log_Xi(
    spectrum: Spectrum, beta: float, mu: np.ndarray | float
) -> np.ndarray:
    """ln Xi(beta, mu) summed over all stored sectors, stable via log-sum-exp.

    ``beta`` is scalar; ``mu`` may be scalar or a (B,) array.
    """
    energies, numbers = _stacked_spectrum(spectrum)
    mu = np.asarray(mu, dtype=float)
    # exponent[..., i] = -beta (E_i - mu N_i)
    expo = -beta * (energies - np.multiply.outer(mu, numbers))
    return logsumexp(expo, axis=-1)


def grand_weights(
    spectrum: Spectrum, beta: float, mu: float
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Grand weights p_{N,alpha} for scalar (beta, mu).

    Returns ``(weights, energies, numbers)`` as aligned flat arrays.
    """
    energies, numbers = _stacked_spectrum(spectrum)
    expo = -beta * (energies - mu * numbers)
    expo -= expo.max()
    w = np.exp(expo)
    w /= w.sum()
    return w, energies, numbers


# ----------------------------------------------------------------------------
# Microcanonical ensemble (fixed N, E window): Omega(E, N; dE)
# ----------------------------------------------------------------------------


def omega(energies: np.ndarray, E: np.ndarray | float, dE: float) -> np.ndarray:
    """Number of eigenvalues in the window [E, E + dE).

    ``E`` may be scalar or an array of window left-edges.
    """
    energies = np.asarray(energies, dtype=float)
    E = np.asarray(E, dtype=float)
    lo = E[..., None] if E.ndim else E
    counts = np.sum((energies >= lo) & (energies < lo + dE), axis=-1)
    return counts


def entropy_micro(
    energies: np.ndarray, E: np.ndarray | float, dE: float
) -> np.ndarray:
    """Microcanonical entropy S = ln Omega (NaN where Omega == 0)."""
    counts = omega(energies, E, dE).astype(float)
    with np.errstate(divide="ignore"):
        return np.where(counts > 0, np.log(counts), np.nan)
