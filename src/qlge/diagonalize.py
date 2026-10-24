"""Exact diagonalization and spectrum caching (theory/04, PLAN.md Phase 2).

The *full* spectrum of every N-sector is needed, because the canonical and grand
partition functions sum over all eigenvalues (theory/04 "dense vs sparse"). We
therefore use a dense symmetric solver (``numpy.linalg.eigvalsh``) per sector and
cache the result so this O(dim^3) step runs once.

A :class:`Spectrum` bundles the per-sector eigenvalues with the ``RunConfig`` that
produced them. It serializes to a single ``.npz`` file; reloading reproduces the
arrays and config exactly.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass

import numpy as np

from qlge.config import RunConfig
from qlge.hamiltonian import build_from_config


@dataclass
class Spectrum:
    """Per-sector eigenvalues for one model.

    Attributes
    ----------
    config : RunConfig
        The model + numerical choices this spectrum was built from.
    eigenvalues : dict[int, np.ndarray]
        Maps particle number N -> sorted-ascending eigenvalue array of the
        N-sector. Keys are exactly ``config.sectors()``.
    """

    config: RunConfig
    eigenvalues: dict[int, np.ndarray]

    # --- derived quantities ------------------------------------------------
    @property
    def ground_energy(self) -> float:
        """Global ground-state energy across all stored sectors."""
        return float(min(ev.min() for ev in self.eigenvalues.values()))

    def all_eigenvalues(self) -> np.ndarray:
        """Flat sorted array of every eigenvalue across all sectors."""
        return np.sort(np.concatenate(list(self.eigenvalues.values())))

    def dim(self, N: int) -> int:
        return int(self.eigenvalues[N].shape[0])

    # --- persistence -------------------------------------------------------
    def save(self, path: str) -> None:
        """Write to a single ``.npz`` (eigenvalues + JSON-encoded config)."""
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        arrays = {f"N_{N}": ev for N, ev in self.eigenvalues.items()}
        np.savez(
            path,
            __config__=np.frombuffer(
                json.dumps(self.config.to_dict()).encode("utf-8"), dtype=np.uint8
            ),
            __sectors__=np.asarray(sorted(self.eigenvalues), dtype=np.int64),
            **arrays,
        )

    @classmethod
    def load(cls, path: str) -> Spectrum:
        with np.load(path, allow_pickle=False) as data:
            cfg_bytes = data["__config__"].tobytes().decode("utf-8")
            config = RunConfig.from_dict(json.loads(cfg_bytes))
            sectors = [int(N) for N in data["__sectors__"]]
            eigenvalues = {N: np.asarray(data[f"N_{N}"]) for N in sectors}
        return cls(config=config, eigenvalues=eigenvalues)


def diagonalize_sector(config: RunConfig, N: int) -> np.ndarray:
    """Full eigenvalue array (ascending) of the N-sector for ``config``."""
    _, H = build_from_config(config, N)
    # Dense symmetric eigensolver: all eigenvalues, guaranteed real, sorted.
    return np.linalg.eigvalsh(H.toarray())


def diagonalize_sector_vectors(config: RunConfig, N: int):
    """Full eigenvalues *and* eigenvectors of the N-sector.

    Returns ``(sector, evals, evecs)`` where ``evecs[:, a]`` is the a-th
    eigenvector in the sector's occupation basis. Needed for real-space
    observables (site occupations, correlations); memory grows as dim^2, so use
    for small L only.
    """
    sector, H = build_from_config(config, N)
    evals, evecs = np.linalg.eigh(H.toarray())
    return sector, evals, evecs


def diagonalize(config: RunConfig) -> Spectrum:
    """Diagonalize every requested N-sector and return a :class:`Spectrum`."""
    eigenvalues = {N: diagonalize_sector(config, N) for N in config.sectors()}
    return Spectrum(config=config, eigenvalues=eigenvalues)


def default_cache_path(config: RunConfig, data_dir: str = "data") -> str:
    return os.path.join(data_dir, f"spectrum_{config.tag()}.npz")


def load_or_compute(config: RunConfig, data_dir: str = "data") -> Spectrum:
    """Return a cached spectrum if present, else compute and cache it."""
    path = default_cache_path(config, data_dir)
    if os.path.exists(path):
        cached = Spectrum.load(path)
        if cached.config == config:
            return cached
    spectrum = diagonalize(config)
    spectrum.save(path)
    return spectrum
