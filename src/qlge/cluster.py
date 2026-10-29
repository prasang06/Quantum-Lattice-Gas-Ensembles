"""Tilted periodic clusters of the square lattice (Betts-style tori).

An L x L torus is one way to make a finite periodic square lattice; the general
way is to identify sites that differ by any integer combination of two lattice
vectors ``a1`` and ``a2``. The cluster then has ``M = |det[a1 a2]|`` sites, and
every site keeps four distinct nearest neighbors, so the local geometry is that
of the infinite square lattice for any M that admits such a pair.

The cluster is bipartite (checkerboard-colorable) exactly when ``a1`` and ``a2``
both have even ``x + y``. That rules out odd-L tori such as 3 x 3, and the 2 x 2
torus fails the four-distinct-neighbors test (it collapses to a 4-site ring).
The family in ``TILTED_CLUSTERS`` passes both tests at M = 8, 10, 16, 18, 20, so
finite-size fits on it compare lattices of one geometry rather than three.

Site i has integer coordinates ``sites[i]``, the canonical representative of its
class modulo the superlattice; translations, momenta, and the point group that
the cluster preserves are what symmetry.py needs to block-diagonalize H.
"""

from __future__ import annotations

from functools import cached_property

import numpy as np

# Wrap vectors (a1x, a1y, a2x, a2y) of bipartite square-lattice clusters, by M.
TILTED_CLUSTERS: dict[int, tuple[int, int, int, int]] = {
    8: (2, 2, 2, -2),
    10: (3, 1, 1, -3),
    16: (4, 0, 0, 4),
    18: (3, 3, 3, -3),
    20: (4, 2, 2, -4),
}

_NEIGHBOR_STEPS = ((1, 0), (0, 1))
# The eight orthogonal integer matrices of the square's point group D4.
_D4 = [
    np.array(m)
    for m in (
        [[1, 0], [0, 1]], [[0, -1], [1, 0]], [[-1, 0], [0, -1]], [[0, 1], [-1, 0]],
        [[1, 0], [0, -1]], [[-1, 0], [0, 1]], [[0, 1], [1, 0]], [[0, -1], [-1, 0]],
    )
]


class Cluster:
    """Periodic square-lattice cluster spanned by wrap vectors ``a1``, ``a2``."""

    def __init__(self, a1: tuple[int, int], a2: tuple[int, int]):
        self.A = np.array([a1, a2], dtype=np.int64).T  # columns are a1, a2
        det = int(round(np.linalg.det(self.A)))
        if det == 0:
            raise ValueError("wrap vectors are parallel")
        self.M = abs(det)
        self._Ainv = np.linalg.inv(self.A)

        # Canonical representative of each site class: fractional coordinates
        # in [0, 1) with respect to (a1, a2).
        reps: dict[tuple[int, int], int] = {}
        span = int(np.abs(self.A).sum()) + 1
        for x in range(-span, span + 1):
            for y in range(-span, span + 1):
                key = self._key(x, y)
                if key not in reps:
                    reps[key] = len(reps)
        if len(reps) != self.M:
            raise RuntimeError("site enumeration failed")
        # Order sites by their canonical (smallest) coordinates for stability.
        sites = sorted(self._canonical(*self._from_key(k)) for k in reps)
        self.sites = np.array(sites, dtype=np.int64)
        self._index = {self._key(x, y): i for i, (x, y) in enumerate(sites)}

    # --- coordinates ---------------------------------------------------------
    def _key(self, x: int, y: int) -> tuple[int, int]:
        f = self._Ainv @ np.array([x, y], dtype=float)
        f = np.round(f - np.floor(f + 1e-9), 9) % 1.0
        return (int(round(f[0] * self.M)) % self.M, int(round(f[1] * self.M)) % self.M)

    def _from_key(self, key: tuple[int, int]) -> tuple[int, int]:
        v = self.A @ (np.array(key, dtype=float) / self.M)
        return int(round(v[0])), int(round(v[1]))

    def _canonical(self, x: int, y: int) -> tuple[int, int]:
        """Smallest (by |x|+|y|, then x, y) member of the class of (x, y)."""
        best = None
        for m in range(-2, 3):
            for n in range(-2, 3):
                p = np.array([x, y]) + m * self.A[:, 0] + n * self.A[:, 1]
                cand = (int(abs(p[0]) + abs(p[1])), int(p[0]), int(p[1]))
                if best is None or cand < best:
                    best = cand
        return best[1], best[2]

    def index(self, x: int, y: int) -> int:
        """Site index of the class containing integer point (x, y)."""
        return self._index[self._key(x, y)]

    # --- geometry ------------------------------------------------------------
    @cached_property
    def bonds(self) -> list[tuple[int, int]]:
        """Nearest-neighbor bonds as sorted pairs, each once."""
        pairs = set()
        for i, (x, y) in enumerate(self.sites):
            for dx, dy in _NEIGHBOR_STEPS:
                j = self.index(x + dx, y + dy)
                if i != j:
                    pairs.add((min(i, j), max(i, j)))
        return sorted(pairs)

    @property
    def coordination_ok(self) -> bool:
        """Every site has four distinct neighbors (bond count 2M)."""
        return len(self.bonds) == 2 * self.M

    @property
    def bipartite(self) -> bool:
        return all((int(v[0]) + int(v[1])) % 2 == 0 for v in self.A.T)

    # --- symmetry ------------------------------------------------------------
    @cached_property
    def translations(self) -> np.ndarray:
        """(M, M) int array: ``translations[r, i]`` is site i shifted by site r's vector."""
        T = np.empty((self.M, self.M), dtype=np.int64)
        for r, (rx, ry) in enumerate(self.sites):
            for i, (x, y) in enumerate(self.sites):
                T[r, i] = self.index(x + rx, y + ry)
        return T

    @cached_property
    def momenta(self) -> np.ndarray:
        """(M, 2) allowed momenta k with k . a1, k . a2 in 2 pi Z, folded to [0, 2pi)."""
        B = 2 * np.pi * np.linalg.inv(self.A).T  # columns: reciprocal of a1, a2
        found: dict[tuple[float, float], np.ndarray] = {}
        for n1 in range(self.M):
            for n2 in range(self.M):
                k = np.mod(B @ np.array([n1, n2], dtype=float), 2 * np.pi)
                key = tuple(np.round(k / (2 * np.pi) * 4 * self.M).astype(int) % (4 * self.M))
                found.setdefault(key, k)
                if len(found) == self.M:
                    break
            if len(found) == self.M:
                break
        return np.array([found[k] for k in sorted(found)])

    def momentum_index(self, k: np.ndarray) -> int:
        d = np.mod(self.momenta - np.asarray(k), 2 * np.pi)
        d = np.minimum(d, 2 * np.pi - d)
        j = int(np.argmin(np.abs(d).sum(axis=1)))
        if np.abs(d[j]).sum() > 1e-6:
            raise ValueError(f"momentum {k} not allowed on this cluster")
        return j

    @cached_property
    def point_group(self) -> list[np.ndarray]:
        """D4 elements that map the superlattice onto itself (always contains C2)."""
        out = []
        for R in _D4:
            C = self._Ainv @ (R @ self.A)
            if np.allclose(C, np.round(C)):
                out.append(R)
        return out

    @cached_property
    def momentum_stars(self) -> list[tuple[int, int]]:
        """(representative momentum index, star size) for each point-group orbit of k.

        Blocks related by a symmetry of the cluster share their spectrum, so
        only one per star needs diagonalizing.
        """
        seen: set[int] = set()
        stars = []
        for j in range(self.M):
            if j in seen:
                continue
            orbit = {self.momentum_index(R @ self.momenta[j]) for R in self.point_group}
            seen |= orbit
            stars.append((j, len(orbit)))
        return stars


def tilted_cluster(M: int) -> Cluster:
    """The bipartite cluster with M sites from ``TILTED_CLUSTERS``."""
    a1x, a1y, a2x, a2y = TILTED_CLUSTERS[M]
    return Cluster((a1x, a1y), (a2x, a2y))
