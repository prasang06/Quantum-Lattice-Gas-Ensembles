"""Real-space thermal observables (site occupations and correlations).

These require eigenvectors, so they are computed on the fly for small lattices
(see diagonalize.diagonalize_sector_vectors). Used by the real-space animations
that visualize the physical system as parameters shift.

For a canonical state at fixed N and inverse temperature beta, the thermal
expectation of a Fock-diagonal operator O (such as n_i or n_i n_j) is

    <O> = sum_a p_a <psi_a| O |psi_a>,   p_a = e^{-beta E_a} / Z,

and since n_i is diagonal in the occupation basis,

    <psi_a| n_i |psi_a> = sum_k |psi_a[k]|^2 * occ(state_k, i).
"""

from __future__ import annotations

import numpy as np

from qlge.basis import Sector
from qlge.config import RunConfig
from qlge.diagonalize import diagonalize_sector_vectors
from qlge.ensembles import canonical_weights


def _occupation_matrix(sector: Sector) -> np.ndarray:
    """(dim, M) array: row k is the occupation vector of basis state k."""
    states = sector.states
    M = sector.M
    bits = ((states[:, None] >> np.arange(M)[None, :]) & 1).astype(float)
    return bits  # bits[k, i] = n_i of state k


def canonical_site_density(
    config: RunConfig, N: int, beta: float
) -> np.ndarray:
    """Thermal <n_i> for each site, returned as an L x L grid.

    Under periodic boundary conditions this is uniform (= N/M) by translation
    symmetry; use open boundary conditions to see spatial structure.
    """
    sector, evals, evecs = diagonalize_sector_vectors(config, N)
    occ = _occupation_matrix(sector)              # (dim, M)
    prob = evecs**2                               # (dim, dim): prob[k, a]
    # <n_i>_a = sum_k occ[k,i] * prob[k,a]  -> (M, dim)
    n_site_per_eigstate = occ.T @ prob            # (M, dim)
    w = canonical_weights(evals, beta)            # (dim,)
    n_site = n_site_per_eigstate @ w              # (M,)
    return n_site.reshape(config.L, config.L)


def canonical_nn_correlation(config: RunConfig, N: int, beta: float) -> float:
    """Average connected nearest-neighbor correlation <n_i n_j> - <n_i><n_j>.

    Positive => bunching/clustering (attractive); negative => anti-bunching
    (repulsive checkerboard tendency).
    """
    from qlge.lattice import bonds

    sector, evals, evecs = diagonalize_sector_vectors(config, N)
    occ = _occupation_matrix(sector)              # (dim, M)
    prob = evecs**2                               # (dim, dim)
    w = canonical_weights(evals, beta)            # (dim,)
    # Thermal population of each basis state: P(state_k) = sum_a w_a |psi_a[k]|^2
    Pk = prob @ w                                 # (dim,)
    n_mean = occ.T @ Pk                           # (M,) thermal <n_i>

    bl = bonds(config.L, config.bc)
    vals = []
    for i, j in bl:
        nninj = float(np.sum(Pk * occ[:, i] * occ[:, j]))
        vals.append(nninj - n_mean[i] * n_mean[j])
    return float(np.mean(vals))
