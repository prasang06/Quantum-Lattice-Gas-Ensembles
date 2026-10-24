"""Ensemble + observable checks (theory/05-06; PLAN.md Phase 3 gate).

Gates:
  - Thermodynamic limits: T->0 and T->inf behavior of <E>, S, C_V.
  - Analytic canonical values for the V=0 2x2 N=1 sector.
  - log-sum-exp stability at extreme beta (no overflow/NaN).
  - Grand-canonical <N> monotone in mu; Xi consistent with sum_N Z_N weights.
  - Microcanonical Omega counts match brute force and sum to sector dimension.
"""

from __future__ import annotations

import numpy as np
import pytest

from qlge.config import RunConfig
from qlge.diagonalize import diagonalize
from qlge.ensembles import log_Xi, log_Z, omega
from qlge.observables import canonical, grand, mean_N_at


@pytest.fixture(scope="module")
def spec_free():
    # V=0, 2x2: analytic single-particle spectrum available.
    return diagonalize(RunConfig(L=2, V=0.0, bc="open"))


# --- canonical limits & analytics ------------------------------------------
def test_canonical_high_T_limit(spec_free):
    N = 2
    ev = spec_free.eigenvalues[N]
    res = canonical(spec_free, N, beta=np.array([1e-9]))
    # T -> inf: <E> -> spectrum mean, S -> ln(dim), C_V -> 0.
    assert res.energy[0] == pytest.approx(ev.mean(), abs=1e-6)
    assert res.entropy[0] == pytest.approx(np.log(len(ev)), abs=1e-6)
    assert res.heat_capacity[0] == pytest.approx(0.0, abs=1e-6)


def test_canonical_low_T_limit(spec_free):
    N = 1
    ev = spec_free.eigenvalues[N]
    res = canonical(spec_free, N, beta=np.array([50.0]))
    # T -> 0: <E> -> ground energy; S -> ln(ground degeneracy).
    e0 = ev.min()
    degeneracy = int(np.sum(np.isclose(ev, e0)))
    assert res.energy[0] == pytest.approx(e0, abs=1e-8)
    assert res.entropy[0] == pytest.approx(np.log(degeneracy), abs=1e-6)
    assert res.heat_capacity[0] == pytest.approx(0.0, abs=1e-6)


def test_canonical_analytic_single_particle(spec_free):
    # N=1 eigenvalues {-2,0,0,2}; Z = e^{2b}+2+e^{-2b}, <E>=(-2e^{2b}+2e^{-2b})/Z.
    b = 0.7
    res = canonical(spec_free, 1, beta=np.array([b]))
    Z = np.exp(2 * b) + 2 + np.exp(-2 * b)
    E = (-2 * np.exp(2 * b) + 2 * np.exp(-2 * b)) / Z
    assert res.energy[0] == pytest.approx(E, abs=1e-10)
    assert np.exp(res.entropy[0] - b * res.energy[0]) == pytest.approx(Z, rel=1e-10)


def test_logZ_stable_at_extreme_beta(spec_free):
    ev = spec_free.eigenvalues[2]
    for b in (0.0, 1e-12, 1e3):
        val = log_Z(ev, b)
        assert np.isfinite(val)


# --- grand-canonical --------------------------------------------------------
def test_grand_meanN_monotone_in_mu(spec_free):
    mu = np.linspace(-15, 15, 80)
    res = grand(spec_free, beta=1.0, mu=mu)
    assert np.all(np.diff(res.mean_N) >= -1e-12)  # non-decreasing
    # Deep in each limit <N> saturates to 0 and to M.
    assert res.mean_N[0] == pytest.approx(0.0, abs=1e-5)
    assert res.mean_N[-1] == pytest.approx(spec_free.config.n_sites, abs=1e-5)


def test_grand_dNdmu_is_beta_varN(spec_free):
    beta = 1.3
    mu = np.linspace(-4, 4, 40)
    res = grand(spec_free, beta=beta, mu=mu)
    assert np.allclose(res.dNdmu, beta * res.var_N)


def test_logXi_matches_sector_combination(spec_free):
    # ln Xi = logsumexp_N ( ln Z_N + beta mu N ).
    beta, mu = 0.9, 0.4
    from scipy.special import logsumexp

    terms = []
    for N, ev in spec_free.eigenvalues.items():
        terms.append(log_Z(ev, beta) + beta * mu * N)
    expected = logsumexp(terms)
    assert log_Xi(spec_free, beta, mu) == pytest.approx(expected, abs=1e-10)


def test_mean_N_at_matches_grand(spec_free):
    beta, mu = 1.1, 0.3
    res = grand(spec_free, beta=beta, mu=np.array([mu]))
    assert mean_N_at(spec_free, beta, mu) == pytest.approx(res.mean_N[0], abs=1e-12)


# --- microcanonical ---------------------------------------------------------
def test_omega_counts_sum_to_dimension(spec_free):
    ev = spec_free.eigenvalues[2]
    # Tile the whole spectral range with non-overlapping windows; counts sum to dim.
    dE = 0.25
    edges = np.arange(ev.min() - dE, ev.max() + dE, dE)
    total = sum(int(omega(ev, e, dE)) for e in edges)
    assert total == len(ev)


def test_omega_brute_force(spec_free):
    ev = spec_free.eigenvalues[2]
    E, dE = -0.5, 1.0
    brute = int(np.sum((ev >= E) & (ev < E + dE)))
    assert int(omega(ev, E, dE)) == brute
