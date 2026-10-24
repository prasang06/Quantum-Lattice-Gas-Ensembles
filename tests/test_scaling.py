"""Finite-size scaling checks (theory/07; PLAN.md Phase 5 gate)."""

from __future__ import annotations

import numpy as np
import pytest

from qlge.config import RunConfig
from qlge.diagonalize import diagonalize
from qlge.scaling import (
    PowerLawFit,
    ScalingPoint,
    fit_power_law,
    filling_to_N,
    scaling_sweep,
)


@pytest.fixture(scope="module")
def spectra():
    return {L: diagonalize(RunConfig(L=L, V=0.0, bc="open")) for L in (2, 3)}


def test_filling_to_N_clamped():
    assert filling_to_N(4, 0.5) == 2
    assert filling_to_N(9, 0.5) == 4  # round(4.5) -> 4 under banker's rounding
    assert filling_to_N(4, 0.0) == 1  # never 0
    assert filling_to_N(4, 1.0) == 3  # never M


def test_scaling_sweep_decreases(spectra):
    pts = scaling_sweep(spectra, beta=1.0, filling=0.5)
    assert [p.L for p in pts] == [2, 3]
    # Discrepancy metrics decrease with L.
    assert pts[1].rel_energy_fluctuation < pts[0].rel_energy_fluctuation
    assert pts[1].rel_number_fluctuation < pts[0].rel_number_fluctuation
    assert pts[1].energy_discrepancy_per_site < pts[0].energy_discrepancy_per_site


def test_power_law_fit_recovers_slope():
    M = np.array([4.0, 9.0, 16.0, 25.0])
    y = 3.0 * M ** (-0.5)  # exact power law
    fit = fit_power_law(M, y)
    assert isinstance(fit, PowerLawFit)
    assert fit.exponent == pytest.approx(-0.5, abs=1e-10)
    assert fit.amplitude == pytest.approx(3.0, rel=1e-10)
    assert fit.r_squared == pytest.approx(1.0, abs=1e-12)


def test_power_law_fit_negative_exponent(spectra):
    # The decay exponent of the relative energy fluctuation must be negative.
    pts = scaling_sweep(spectra, beta=1.0, filling=0.5)
    M = np.array([p.M for p in pts])
    y = np.array([p.rel_energy_fluctuation for p in pts])
    fit = fit_power_law(M, y)
    assert fit.exponent < 0


def test_power_law_fit_needs_two_points():
    with pytest.raises(ValueError):
        fit_power_law(np.array([4.0]), np.array([1.0]))
