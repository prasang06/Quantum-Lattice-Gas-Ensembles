"""Symmetry-reduced full-spectrum ED on tilted clusters (cluster.py).

Three symmetries cut the cost of the dense diagonalization:

- Translations. Each N-sector splits into M momentum blocks. For a basis state
  ``a`` that is the smallest member of its translation orbit, the Bloch state

      |a, k> = sum_r exp(-i k.r) T_r |a>

  is a T eigenstate (T_s |a,k> = exp(i k.s) |a,k>); it vanishes unless k.r is a
  multiple of 2 pi for every r that fixes ``a``. Different representatives have
  disjoint support, so normalized Bloch states are orthonormal, and the k-block
  is H_k = V_k^dag H V_k with V_k the (dim x D_k) matrix of Bloch columns. H
  itself is the existing real sector matrix (hamiltonian.build_sector), so no
  new matrix elements are written by hand.

- Point group. A rotation or reflection R that maps the cluster to itself maps
  the k-block onto the Rk-block, so blocks in one star share a spectrum. Only
  one block per star is diagonalized; its eigenvalues are repeated star-size
  times.

- Particle-hole. Hard-core hopping is invariant under n -> 1 - n, and with B
  bonds of coordination z the interaction picks up a constant:
  E_{M-N} = E_N + V (B - z N). Sectors N > M/2 come free from N < M/2.

Each block is real symmetric when 2k = 0 mod 2pi and complex Hermitian
otherwise; both use a dense LAPACK eigensolver.
"""

from __future__ import annotations

import numpy as np
import scipy.sparse as sp

from qlge.basis import Sector
from qlge.cluster import Cluster
from qlge.config import RunConfig


def translate_states(states: np.ndarray, perm: np.ndarray) -> np.ndarray:
    """Apply a site permutation (site i -> perm[i]) to an array of bit states."""
    out = np.zeros_like(states)
    for i, j in enumerate(perm):
        out |= ((states >> i) & 1) << int(j)
    return out


def bloch_basis(sector: Sector, cluster: Cluster, k_index: int) -> sp.csc_matrix:
    """(dim x D_k) matrix whose columns are the normalized Bloch states at momentum k."""
    states = sector.states
    k = cluster.momenta[k_index]
    images = np.stack([translate_states(states, cluster.translations[r]) for r in range(cluster.M)])
    is_rep = images.min(axis=0) == states
    rep_cols = np.flatnonzero(is_rep)

    phases = np.exp(-1j * (cluster.sites @ k))  # (M,), phase for translation r
    rows = np.searchsorted(states, images[:, rep_cols]).ravel()  # (M * R,)
    cols = np.tile(np.arange(rep_cols.size), cluster.M)
    vals = np.repeat(phases, rep_cols.size)
    V = sp.coo_matrix((vals, (rows, cols)), shape=(sector.dim, rep_cols.size)).tocsc()
    V.sum_duplicates()

    norms = np.sqrt(np.asarray(abs(V).power(2).sum(axis=0)).ravel())
    keep = norms > 1e-9
    V = V[:, keep] @ sp.diags(1.0 / norms[keep])
    if np.allclose(phases.imag, 0.0):
        V = V.real
    return V.tocsc()


def sector_eigenvalues(config: RunConfig, cluster: Cluster, N: int, H=None) -> np.ndarray:
    """Full sorted spectrum of the N-sector, assembled from one block per k-star."""
    from qlge.hamiltonian import build_sector

    sector = Sector(cluster.M, N)
    if H is None:
        H = build_sector(sector, cluster.bonds, config.t, config.V)
    parts = []
    for k_index, star_size in cluster.momentum_stars:
        V = bloch_basis(sector, cluster, k_index)
        if V.shape[1] == 0:
            continue
        Hk = (V.conj().T @ (H @ V)).toarray()
        ev = np.linalg.eigvalsh(Hk)
        parts.append(np.tile(ev, star_size))
    ev = np.sort(np.concatenate(parts))
    if ev.size != sector.dim:
        raise RuntimeError(f"N={N}: assembled {ev.size} eigenvalues, expected {sector.dim}")
    return ev


def particle_hole_shift(cluster: Cluster, V: float, N: int) -> float:
    """E_{M-N} - E_N for the matching eigenvalue: V (B - z N)."""
    B = len(cluster.bonds)
    z = 2 * B // cluster.M
    return V * (B - z * N)


def diagonalize_cluster(config: RunConfig, progress=None) -> dict[int, np.ndarray]:
    """Per-sector eigenvalues for a tilted-cluster config, using all three symmetries."""
    cluster = config.cluster_geometry()
    M = cluster.M
    wanted = set(config.sectors())
    out: dict[int, np.ndarray] = {}
    for N in range(M // 2 + 1):
        if N not in wanted and (M - N) not in wanted:
            continue
        ev = sector_eigenvalues(config, cluster, N)
        if N in wanted:
            out[N] = ev
        if (M - N) in wanted and M - N != N:
            out[M - N] = np.sort(ev + particle_hole_shift(cluster, config.V, N))
        if progress is not None:
            progress(N)
    return dict(sorted(out.items()))
