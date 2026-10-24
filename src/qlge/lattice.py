"""Square-lattice geometry: site indexing and nearest-neighbor bonds.

Sites on an L x L grid are flattened as ``i = x + L*y`` with ``x, y in 0..L-1``
(theory/03). A bond is an unordered pair ``(i, j)`` of nearest neighbors, each
counted once. Boundary conditions:

- "open":     neighbors only inside the grid; bond count = 2*L*(L-1).
- "periodic": neighbors wrap; bond count = 2*L*L (for L >= 2).

For L == 1 there are no bonds under either convention. For L == 2 periodic the
two wrap bonds coincide with the open bonds in each direction, so the pair set
collapses to the 4 open bonds (handled by de-duplication).
"""

from __future__ import annotations

from qlge.config import BoundaryCondition


def site_index(x: int, y: int, L: int) -> int:
    """Flatten 2D coordinates to a site index."""
    return x + L * y


def coords(i: int, L: int) -> tuple[int, int]:
    """Inverse of :func:`site_index`."""
    return i % L, i // L


def bonds(L: int, bc: BoundaryCondition = "periodic") -> list[tuple[int, int]]:
    """Return the nearest-neighbor bond list for an L x L lattice.

    Each bond appears once as a sorted tuple ``(i, j)`` with ``i < j``. Duplicate
    pairs (which can arise for L == 2 periodic, where forward and backward wrap
    land on the same neighbor) are removed.
    """
    if bc not in ("open", "periodic"):
        raise ValueError(f"bc must be 'open' or 'periodic', got {bc!r}")

    pairs: set[tuple[int, int]] = set()
    for y in range(L):
        for x in range(L):
            i = site_index(x, y, L)
            # +x neighbor
            if x + 1 < L:
                j = site_index(x + 1, y, L)
                pairs.add((min(i, j), max(i, j)))
            elif bc == "periodic" and L > 1:
                j = site_index(0, y, L)
                if i != j:
                    pairs.add((min(i, j), max(i, j)))
            # +y neighbor
            if y + 1 < L:
                j = site_index(x, y + 1, L)
                pairs.add((min(i, j), max(i, j)))
            elif bc == "periodic" and L > 1:
                j = site_index(x, 0, L)
                if i != j:
                    pairs.add((min(i, j), max(i, j)))

    return sorted(pairs)
