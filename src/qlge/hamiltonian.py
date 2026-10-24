"""Assemble the hard-core Bose-Hubbard Hamiltonian per N-sector (theory/03).

    H = -t * sum_<i,j> (b_i^dag b_j + b_j^dag b_i)  +  V * sum_<i,j> n_i n_j

Hard-core bosons carry no inter-site exchange sign, so every hop contributes a
plain ``-t`` and each sector block is real symmetric. The interaction is diagonal:
``V`` times the number of occupied nearest-neighbor bonds.
"""

from __future__ import annotations

import numpy as np
import scipy.sparse as sp

from qlge.basis import Sector, move_particle, occupied
from qlge.config import RunConfig
from qlge.lattice import bonds


def interaction_energy(state: int, bond_list: list[tuple[int, int]], V: float) -> float:
    """Diagonal interaction: V * (# bonds with both endpoints occupied)."""
    count = sum(1 for i, j in bond_list if occupied(state, i) and occupied(state, j))
    return V * count


def build_sector(
    sector: Sector,
    bond_list: list[tuple[int, int]],
    t: float,
    V: float,
) -> sp.csr_matrix:
    """Build the sparse Hamiltonian block for one N-sector.

    Returns a ``(dim, dim)`` real CSR matrix. Columns are indexed by
    ``sector.states``; hopping conserves N so every target state is in-sector.
    """
    rows: list[int] = []
    cols: list[int] = []
    vals: list[float] = []

    for col, state in enumerate(sector.states):
        state = int(state)
        # Diagonal interaction term.
        diag = interaction_energy(state, bond_list, V)
        if diag != 0.0:
            rows.append(col)
            cols.append(col)
            vals.append(diag)
        # Off-diagonal hopping across each bond, both directions.
        for i, j in bond_list:
            if occupied(state, j) and not occupied(state, i):
                tgt = move_particle(state, frm=j, to=i)
                rows.append(sector.index(tgt))
                cols.append(col)
                vals.append(-t)
            if occupied(state, i) and not occupied(state, j):
                tgt = move_particle(state, frm=i, to=j)
                rows.append(sector.index(tgt))
                cols.append(col)
                vals.append(-t)

    dim = sector.dim
    H = sp.coo_matrix((vals, (rows, cols)), shape=(dim, dim), dtype=np.float64)
    return H.tocsr()


def build_from_config(config: RunConfig, N: int) -> tuple[Sector, sp.csr_matrix]:
    """Convenience: build the sector basis and Hamiltonian for config at fixed N."""
    sector = Sector(config.n_sites, N)
    bond_list = bonds(config.L, config.bc)
    H = build_sector(sector, bond_list, config.t, config.V)
    return sector, H
