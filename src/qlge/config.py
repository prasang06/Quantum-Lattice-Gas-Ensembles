"""Run configuration.

A ``RunConfig`` fully determines a model and the numerical choices made when
turning its spectrum into thermodynamics. It is serialized alongside every
cached artifact so results are reproducible (PLAN.md "Reproducibility").
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Literal

import yaml

BoundaryCondition = Literal["open", "periodic"]


@dataclass(frozen=True)
class RunConfig:
    """Parameters for a single model + post-processing run.

    Energy unit is ``t`` and ``k_B = 1`` by convention (theory/README.md); the
    free parameters are therefore ``V/t``, ``T/t``, ``mu/t``.
    """

    # Model
    L: int = 2
    t: float = 1.0
    V: float = 0.0
    bc: BoundaryCondition = "periodic"

    # Which particle-number sectors to build (None -> all N = 0..n_sites).
    n_sectors: tuple[int, ...] | None = None

    # Tilted periodic cluster wrap vectors (a1x, a1y, a2x, a2y); see cluster.py.
    # When set, it replaces the L x L torus and L is ignored.
    cluster: tuple[int, int, int, int] | None = None

    # Microcanonical modeling choices
    dE: float = 0.5  # energy-window width for Omega(E, N; dE)

    # Grids for post-processing (inclusive endpoints, step count)
    beta_min: float = 0.01
    beta_max: float = 10.0
    beta_num: int = 200
    mu_min: float = -8.0
    mu_max: float = 8.0
    mu_num: int = 200

    # Bookkeeping
    seed: int = 0
    notes: str = ""

    def __post_init__(self) -> None:
        if self.L < 1:
            raise ValueError(f"L must be >= 1, got {self.L}")
        if self.cluster is not None and self.bc != "periodic":
            raise ValueError("tilted clusters are periodic by construction")
        if self.bc not in ("open", "periodic"):
            raise ValueError(f"bc must be 'open' or 'periodic', got {self.bc!r}")
        if self.dE <= 0:
            raise ValueError(f"dE must be > 0, got {self.dE}")
        if self.n_sectors is not None:
            for n in self.n_sectors:
                if not (0 <= n <= self.n_sites):
                    raise ValueError(
                        f"sector N={n} out of range [0, {self.n_sites}]"
                    )

    @property
    def n_sites(self) -> int:
        """Number of lattice sites: L^2, or |det[a1 a2]| for a tilted cluster."""
        if self.cluster is not None:
            a1x, a1y, a2x, a2y = self.cluster
            return abs(a1x * a2y - a1y * a2x)
        return self.L * self.L

    def cluster_geometry(self):
        """The :class:`qlge.cluster.Cluster` for a tilted-cluster config."""
        from qlge.cluster import Cluster

        if self.cluster is None:
            raise ValueError("config describes an L x L torus, not a tilted cluster")
        a1x, a1y, a2x, a2y = self.cluster
        return Cluster((a1x, a1y), (a2x, a2y))

    def sectors(self) -> tuple[int, ...]:
        """Resolved list of N-sectors to build."""
        if self.n_sectors is not None:
            return tuple(self.n_sectors)
        return tuple(range(self.n_sites + 1))

    # --- serialization -----------------------------------------------------
    def to_dict(self) -> dict:
        return asdict(self)

    def to_yaml(self, path: str) -> None:
        with open(path, "w") as fh:
            yaml.safe_dump(self.to_dict(), fh, sort_keys=False)

    @classmethod
    def from_dict(cls, d: dict) -> RunConfig:
        d = dict(d)
        for key in ("n_sectors", "cluster"):
            if d.get(key) is not None:
                d[key] = tuple(d[key])
        return cls(**d)

    @classmethod
    def from_yaml(cls, path: str) -> RunConfig:
        with open(path) as fh:
            return cls.from_dict(yaml.safe_load(fh))

    def tag(self) -> str:
        """Short filesystem-safe identifier for cache files."""
        if self.cluster is not None:
            return f"C{self.n_sites}_t{self.t:g}_V{self.V:g}_{self.bc}"
        return f"L{self.L}_t{self.t:g}_V{self.V:g}_{self.bc}"
