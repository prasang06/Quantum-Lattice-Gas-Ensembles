"""Occupation-number basis with bit encoding (theory/02).

A basis state is an integer whose bit ``i`` is the occupation ``n_i in {0, 1}``.
Working per fixed-N sector, we enumerate all integers with exactly ``N`` set bits
and build a ``state -> row index`` map so hopping can find the column a move lands
in. Sector dimension is ``C(M, N)``.
"""

from __future__ import annotations

from itertools import combinations

import numpy as np


def occupied(state: int, i: int) -> bool:
    """Is site ``i`` occupied in ``state``?"""
    return bool((state >> i) & 1)


def popcount(state: int) -> int:
    """Number of set bits (= total particle number N)."""
    return int(state).bit_count()


def move_particle(state: int, frm: int, to: int) -> int:
    """Move a particle from site ``frm`` to empty site ``to``.

    Caller guarantees ``frm`` occupied and ``to`` empty.
    """
    return (state & ~(1 << frm)) | (1 << to)


class Sector:
    """Fixed-N sector: the list of basis states and a lookup from state to index.

    Attributes
    ----------
    M : int
        Number of sites.
    N : int
        Particle number of this sector.
    states : np.ndarray[int64]
        Basis-state integers, ascending. ``dim = len(states) == C(M, N)``.
    """

    def __init__(self, M: int, N: int):
        if not (0 <= N <= M):
            raise ValueError(f"N={N} out of range [0, {M}]")
        self.M = M
        self.N = N
        # Enumerate integers with exactly N set bits among M sites, ascending.
        states = [
            sum(1 << b for b in bits) for bits in combinations(range(M), N)
        ]
        states.sort()
        self.states = np.asarray(states, dtype=np.int64)
        # Reverse map: state integer -> row index.
        self._index = {int(s): k for k, s in enumerate(self.states)}

    @property
    def dim(self) -> int:
        return int(self.states.shape[0])

    def index(self, state: int) -> int:
        """Row index of a state within this sector."""
        return self._index[int(state)]
