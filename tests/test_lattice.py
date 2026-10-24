"""Lattice geometry checks (PLAN.md Phase 1 gate)."""

from __future__ import annotations

import pytest

from qlge.lattice import bonds, coords, site_index


def test_index_roundtrip():
    L = 3
    for y in range(L):
        for x in range(L):
            i = site_index(x, y, L)
            assert coords(i, L) == (x, y)


@pytest.mark.parametrize("L", [2, 3, 4])
def test_open_bond_count(L):
    # Open BC on an L x L grid: 2 * L * (L - 1) bonds.
    assert len(bonds(L, "open")) == 2 * L * (L - 1)


@pytest.mark.parametrize("L", [3, 4, 5])
def test_periodic_bond_count(L):
    # Periodic BC for L >= 3: 2 * L * L bonds (no accidental duplicates).
    assert len(bonds(L, "periodic")) == 2 * L * L


def test_L2_periodic_collapses_to_plaquette():
    # For L == 2 the wrap neighbor coincides with the direct neighbor, so
    # periodic de-duplicates to the same 4-bond ring as open BC.
    assert bonds(2, "periodic") == bonds(2, "open")
    assert len(bonds(2, "open")) == 4


def test_bonds_sorted_and_unique():
    bl = bonds(4, "periodic")
    assert bl == sorted(bl)
    assert len(set(bl)) == len(bl)
    for i, j in bl:
        assert i < j
