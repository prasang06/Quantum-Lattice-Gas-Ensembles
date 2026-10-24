"""Hamiltonian validation ladder (theory/03, theory/08; PLAN.md Phase 1 gate).

Independent checks:
  1. Hermiticity / real-symmetry of every sector block.
  2. Sector dimension == C(M, N).
  3. Particle-number conservation: an independently-built full-space H is block
     diagonal in N, and the union of per-sector spectra equals the full spectrum.
  4. Analytic spectrum: V=0, 2x2, N=1 sector equals the C4 ring tight-binding
     spectrum {-2t, 0, 0, +2t}.
  5. Trace identity: Tr H == V * sum over states of occupied-bond count.
"""

from __future__ import annotations

from itertools import combinations
from math import comb

import numpy as np
import pytest

from qlge.basis import Sector
from qlge.hamiltonian import build_sector, interaction_energy
from qlge.lattice import bonds


# --- independent full-space builder (different code path than build_sector) ---
def full_space_hamiltonian(M, bond_list, t, V):
    """Dense 2^M x 2^M Hamiltonian over the entire Fock space, built directly."""
    dim = 2**M
    H = np.zeros((dim, dim))
    for state in range(dim):
        # diagonal interaction
        H[state, state] += V * sum(
            1 for i, j in bond_list if (state >> i) & 1 and (state >> j) & 1
        )
        # hopping
        for i, j in bond_list:
            if (state >> j) & 1 and not (state >> i) & 1:
                tgt = (state & ~(1 << j)) | (1 << i)
                H[tgt, state] += -t
            if (state >> i) & 1 and not (state >> j) & 1:
                tgt = (state & ~(1 << i)) | (1 << j)
                H[tgt, state] += -t
    return H


@pytest.mark.parametrize("L,bc,V", [(2, "open", 0.0), (2, "open", 2.0), (3, "open", 1.5)])
def test_hermitian(L, bc, V):
    M = L * L
    bl = bonds(L, bc)
    for N in range(M + 1):
        H = build_sector(Sector(M, N), bl, t=1.0, V=V).toarray()
        assert np.allclose(H, H.T, atol=1e-12)


@pytest.mark.parametrize("L", [2, 3])
def test_sector_dim_matches_binomial(L):
    M = L * L
    bl = bonds(L, "open")
    for N in range(M + 1):
        H = build_sector(Sector(M, N), bl, t=1.0, V=1.0)
        assert H.shape == (comb(M, N), comb(M, N))


@pytest.mark.parametrize("V", [0.0, 2.0, -1.0])
def test_number_conservation_and_full_spectrum(V):
    # The sector blocks must reproduce the full-space spectrum exactly, which
    # only holds if H is block diagonal in N (i.e. N is conserved).
    L, t = 2, 1.0
    M = L * L
    bl = bonds(L, "open")

    sector_eigs = []
    for N in range(M + 1):
        H = build_sector(Sector(M, N), bl, t=t, V=V).toarray()
        sector_eigs.append(np.linalg.eigvalsh(H))
    sector_spectrum = np.sort(np.concatenate(sector_eigs))

    Hfull = full_space_hamiltonian(M, bl, t=t, V=V)
    assert np.allclose(Hfull, Hfull.T, atol=1e-12)
    full_spectrum = np.sort(np.linalg.eigvalsh(Hfull))

    assert np.allclose(sector_spectrum, full_spectrum, atol=1e-10)


def test_analytic_single_particle_2x2():
    # V=0, 2x2 ring (C4). N=1 tight-binding spectrum = -t * eig(adjacency(C4))
    # = {-2t, 0, 0, +2t}.
    t = 1.0
    H = build_sector(Sector(4, 1), bonds(2, "open"), t=t, V=0.0).toarray()
    eigs = np.sort(np.linalg.eigvalsh(H))
    assert np.allclose(eigs, np.array([-2.0, 0.0, 0.0, 2.0]) * t, atol=1e-10)


@pytest.mark.parametrize("L", [3, 4])
def test_single_particle_dispersion_pbc(L):
    # Literature check: the N=1 sector under periodic BC must reproduce the exact
    # tight-binding band eps(k) = -2t[cos(kx)+cos(ky)], k = 2*pi*n/L.
    # (L=2 is excluded: its periodic lattice de-duplicates to a single-bond ring,
    #  not the true double-bonded 2-torus -- see qlge.lattice.)
    t = 1.0
    H = build_sector(Sector(L * L, 1), bonds(L, "periodic"), t=t, V=0.0).toarray()
    numeric = np.sort(np.linalg.eigvalsh(H))
    ks = 2 * np.pi * np.arange(L) / L
    analytic = np.sort(
        np.array([-2 * t * (np.cos(kx) + np.cos(ky)) for kx in ks for ky in ks])
    )
    assert np.allclose(numeric, analytic, atol=1e-10)


def test_trace_identity():
    # Hopping is purely off-diagonal, so Tr H equals the summed interaction.
    L, V = 3, 1.3
    M = L * L
    bl = bonds(L, "periodic")
    expected = 0.0
    for bits in _all_states(M):
        expected += interaction_energy(bits, bl, V)
    trace = 0.0
    for N in range(M + 1):
        trace += build_sector(Sector(M, N), bl, t=1.0, V=V).diagonal().sum()
    assert np.isclose(trace, expected, atol=1e-10)


def _all_states(M):
    for N in range(M + 1):
        for comb_bits in combinations(range(M), N):
            yield sum(1 << b for b in comb_bits)
