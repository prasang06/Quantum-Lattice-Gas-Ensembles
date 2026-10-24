"""Basis / sector checks (theory/02, PLAN.md Phase 1 gate)."""

from __future__ import annotations

from math import comb

import pytest

from qlge.basis import Sector, move_particle, occupied, popcount


@pytest.mark.parametrize("M,N", [(4, 0), (4, 1), (4, 2), (4, 4), (9, 3), (16, 8)])
def test_sector_dimension(M, N):
    assert Sector(M, N).dim == comb(M, N)


def test_sectors_partition_full_space():
    M = 4
    total = sum(Sector(M, N).dim for N in range(M + 1))
    assert total == 2**M


def test_states_have_correct_particle_number():
    sec = Sector(6, 3)
    for s in sec.states:
        assert popcount(int(s)) == 3


def test_index_is_inverse_of_states():
    sec = Sector(5, 2)
    for k, s in enumerate(sec.states):
        assert sec.index(int(s)) == k


def test_move_particle_preserves_number():
    # Occupy site 0, empty site 1: move 0 -> 1.
    state = 0b0001
    assert occupied(state, 0) and not occupied(state, 1)
    moved = move_particle(state, frm=0, to=1)
    assert moved == 0b0010
    assert popcount(moved) == popcount(state)


def test_invalid_sector_raises():
    with pytest.raises(ValueError):
        Sector(4, 5)
