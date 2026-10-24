"""Diagonalization + caching checks (PLAN.md Phase 2 gate)."""

from __future__ import annotations

import numpy as np
import pytest

from qlge.config import RunConfig
from qlge.diagonalize import (
    Spectrum,
    default_cache_path,
    diagonalize,
    load_or_compute,
)


def test_spectrum_matches_full_space():
    # Union of per-sector spectra equals the independently-built full spectrum.
    cfg = RunConfig(L=2, V=2.0, bc="open")
    spec = diagonalize(cfg)

    from test_hamiltonian import full_space_hamiltonian
    from qlge.lattice import bonds

    Hfull = full_space_hamiltonian(cfg.n_sites, bonds(cfg.L, cfg.bc), cfg.t, cfg.V)
    full = np.sort(np.linalg.eigvalsh(Hfull))
    assert np.allclose(spec.all_eigenvalues(), full, atol=1e-10)


def test_ground_energy_is_global_min():
    cfg = RunConfig(L=2, V=-2.0, bc="open")
    spec = diagonalize(cfg)
    assert spec.ground_energy == pytest.approx(spec.all_eigenvalues().min())


def test_analytic_single_particle():
    # V=0 2x2 N=1 sector == C4 ring spectrum {-2, 0, 0, +2} (t=1).
    spec = diagonalize(RunConfig(L=2, V=0.0, bc="open"))
    assert np.allclose(np.sort(spec.eigenvalues[1]), [-2.0, 0.0, 0.0, 2.0], atol=1e-10)


def test_save_load_roundtrip(tmp_path):
    cfg = RunConfig(L=3, V=1.5, bc="periodic")
    spec = diagonalize(cfg)
    path = str(tmp_path / "spec.npz")
    spec.save(path)
    reloaded = Spectrum.load(path)

    assert reloaded.config == cfg
    assert set(reloaded.eigenvalues) == set(spec.eigenvalues)
    for N in spec.eigenvalues:
        # Bit-for-bit: cached arrays reproduce exactly.
        assert np.array_equal(reloaded.eigenvalues[N], spec.eigenvalues[N])


def test_load_or_compute_uses_cache(tmp_path):
    cfg = RunConfig(L=2, V=0.0, bc="open")
    data_dir = str(tmp_path)
    path = default_cache_path(cfg, data_dir)

    first = load_or_compute(cfg, data_dir)  # computes + writes
    import os

    assert os.path.exists(path)
    mtime = os.path.getmtime(path)

    second = load_or_compute(cfg, data_dir)  # should hit cache, not rewrite
    assert os.path.getmtime(path) == mtime
    for N in first.eigenvalues:
        assert np.array_equal(first.eigenvalues[N], second.eigenvalues[N])


def test_sector_dimensions():
    from math import comb

    cfg = RunConfig(L=2, V=0.0, bc="open")
    spec = diagonalize(cfg)
    for N in range(cfg.n_sites + 1):
        assert spec.dim(N) == comb(cfg.n_sites, N)
