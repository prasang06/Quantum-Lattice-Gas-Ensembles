"""Real-space thermal observable checks (PLAN.md Phase 6)."""

from __future__ import annotations

import numpy as np
import pytest

from qlge.config import RunConfig
from qlge.realspace import canonical_nn_correlation, canonical_site_density


def test_density_sums_to_N():
    cfg = RunConfig(L=3, V=1.0, bc="open")
    rho = canonical_site_density(cfg, N=4, beta=1.5)
    assert rho.sum() == pytest.approx(4.0, abs=1e-10)
    assert np.all(rho >= -1e-12) and np.all(rho <= 1 + 1e-12)


def test_pbc_density_is_uniform():
    # Translation symmetry under periodic BC => every site has <n_i> = N/M.
    cfg = RunConfig(L=3, V=-2.0, bc="periodic")
    rho = canonical_site_density(cfg, N=4, beta=2.0)
    assert rho.std() == pytest.approx(0.0, abs=1e-9)
    assert np.allclose(rho, 4.0 / 9.0, atol=1e-9)


def test_nn_correlation_sign_follows_interaction():
    # Attractive -> bunching (positive); repulsive -> anti-bunching (negative).
    N, beta = 4, 2.0
    c_attr = canonical_nn_correlation(RunConfig(L=3, V=-3.0, bc="open"), N, beta)
    c_rep = canonical_nn_correlation(RunConfig(L=3, V=+3.0, bc="open"), N, beta)
    assert c_attr > c_rep
    assert c_rep < 0.0  # hard-core + repulsion anti-bunches


def test_open_bc_shows_structure():
    # Strong attraction breaks uniformity under open BC (clustering).
    cfg = RunConfig(L=3, V=-4.0, bc="open")
    rho = canonical_site_density(cfg, N=4, beta=2.0)
    assert rho.std() > 0.05
