"""Analytical baselines (benchmarks.py) and their agreement with ED."""

from __future__ import annotations

import numpy as np
import pytest

from qlge.benchmarks import (
    infinite_temperature_number_fluctuation,
    ising_critical_temperature,
    ising_number_fluctuation,
    phase_separates,
)
from qlge.config import RunConfig
from qlge.diagonalize import diagonalize
from qlge.matching import match_ensembles


@pytest.mark.parametrize("V", [-3.0, 0.0, 2.0])
def test_infinite_temperature_limit_matches_ed(V):
    # beta -> 0: grand-canonical N is binomial for any t, V.
    spec = diagonalize(RunConfig(L=3, V=V, bc="periodic"))
    r = match_ensembles(spec, 4, beta=1e-4)
    assert r.rel_number_fluctuation == pytest.approx(
        float(infinite_temperature_number_fluctuation(9, 4)), rel=1e-3
    )


def test_infinite_temperature_is_inverse_sqrt_M_at_half_filling():
    M = np.array([4, 16, 64, 256])
    assert np.allclose(infinite_temperature_number_fluctuation(M, M / 2), M ** -0.5)


def test_onsager_critical_temperature():
    # T_c = 2J / ln(1 + sqrt 2) with J = |V|/4.
    assert ising_critical_temperature(-4.0) == pytest.approx(2.0 / np.log(1 + np.sqrt(2)))
    assert ising_critical_temperature(-3.0) == pytest.approx(1.7019, abs=1e-4)
    assert ising_critical_temperature(3.0) == ising_critical_temperature(-3.0)
    assert ising_critical_temperature(0.0) == 0.0


def test_yang_magnetization_limits():
    V = -4.0
    Tc = ising_critical_temperature(V)
    m = ising_number_fluctuation(V, np.array([1e-3, 0.5 * Tc, 0.999 * Tc, 1.5 * Tc]))
    assert m[0] == pytest.approx(1.0)
    assert 0 < m[2] < m[1] < 1
    assert m[3] == 0.0
    assert np.all(ising_number_fluctuation(2.0, np.array([0.1, 1.0])) == 0.0)


def test_phase_separation_threshold_is_heisenberg_point():
    assert phase_separates(-3.0)
    assert not phase_separates(-2.0)
    assert not phase_separates(-1.0)
    assert phase_separates(-5.0, t=2.0) and not phase_separates(-3.0, t=2.0)


def test_classical_gas_tracks_ising_below_tc():
    # t = 0, strong attraction, deep below T_c: the grand number distribution is
    # two-peaked, so sigma_N/<N> is close to the Ising order parameter already
    # at M = 9, and far above the beta -> 0 binomial value.
    spec = diagonalize(RunConfig(L=3, t=0.0, V=-4.0, bc="periodic"))
    T = 0.4 * ising_critical_temperature(-4.0)
    r = match_ensembles(spec, 4, beta=1.0 / T)
    assert r.rel_number_fluctuation > 0.9 * float(ising_number_fluctuation(-4.0, T))
    assert r.rel_number_fluctuation > 2 * float(infinite_temperature_number_fluctuation(9, 4))
