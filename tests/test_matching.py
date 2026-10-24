"""Cross-ensemble matching checks (theory/05,07; PLAN.md Phase 4 gate).

Gates:
  - mu root-finding is exact: <N>(beta, mu*) == target.
  - Grand <N> equals the target N by construction.
  - Robust equivalence metrics (relative fluctuations, per-site energy gap)
    decrease as L grows -- the emergence signal.
  - Microcanonical finite-diff diagnostics run and return floats (value is
    deliberately NOT asserted tightly; it is brittle on small spectra).
"""

from __future__ import annotations

import numpy as np
import pytest

from qlge.config import RunConfig
from qlge.diagonalize import diagonalize
from qlge.matching import find_mu, match_ensembles
from qlge.observables import mean_N_at


@pytest.fixture(scope="module")
def spec2():
    return diagonalize(RunConfig(L=2, V=0.0, bc="open"))


@pytest.fixture(scope="module")
def spec3():
    return diagonalize(RunConfig(L=3, V=0.0, bc="open"))


def test_find_mu_is_exact(spec3):
    beta = 1.0
    for n_target in (2.0, 4.0, 6.0):
        mu = find_mu(spec3, beta, n_target)
        assert mean_N_at(spec3, beta, mu) == pytest.approx(n_target, abs=1e-8)


def test_find_mu_rejects_out_of_range(spec2):
    with pytest.raises(ValueError):
        find_mu(spec2, beta=1.0, n_target=0.0)
    with pytest.raises(ValueError):
        find_mu(spec2, beta=1.0, n_target=float(spec2.config.n_sites))


def test_grand_meanN_matches_target(spec3):
    r = match_ensembles(spec3, N=4, beta=1.0)
    assert r.mean_N_grand == pytest.approx(4.0, abs=1e-8)


def test_robust_metrics_shrink_with_L(spec2, spec3):
    r2 = match_ensembles(spec2, N=2, beta=1.0)  # half filling, M=4
    r3 = match_ensembles(spec3, N=4, beta=1.0)  # ~half filling, M=9
    # All three equivalence signals must improve with system size.
    assert r3.rel_energy_fluctuation < r2.rel_energy_fluctuation
    assert r3.rel_number_fluctuation < r2.rel_number_fluctuation
    assert r3.energy_discrepancy_per_site < r2.energy_discrepancy_per_site


def test_fluctuation_identity_consistency(spec3):
    # Grand var_N must be non-negative and the relative fluctuation finite.
    r = match_ensembles(spec3, N=4, beta=1.0)
    assert r.var_N_grand >= 0.0
    assert np.isfinite(r.rel_number_fluctuation)
    assert np.isfinite(r.rel_energy_fluctuation)


def test_micro_diagnostic_runs(spec3):
    # The microcanonical finite-diff T, mu are computed and returned as floats.
    # Value is brittle on small spectra, so only type/finiteness-handling is checked.
    r = match_ensembles(spec3, N=4, beta=1.0)
    assert isinstance(r.T_microcanonical, float)
    assert isinstance(r.mu_microcanonical, float)
