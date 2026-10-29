"""Smoke tests: every figure builder returns a Matplotlib figure (Phase 6)."""

from __future__ import annotations

import matplotlib
import pytest

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from qlge import plotting as P
from qlge.config import RunConfig
from qlge.diagonalize import diagonalize


@pytest.fixture(scope="module")
def spectra_by_V():
    return {V: diagonalize(RunConfig(L=3, V=V, bc="open")) for V in (0.0, 2.0, -2.0)}


@pytest.fixture(scope="module")
def spectra_by_L():
    return {L: diagonalize(RunConfig(L=L, V=0.0, bc="open")) for L in (2, 3)}


def _is_fig(obj):
    return isinstance(obj, plt.Figure)


def test_core_figures_build(spectra_by_V, spectra_by_L):
    free = spectra_by_V[0.0]
    assert _is_fig(P.fig_spectrum_dos(free))
    assert _is_fig(P.fig_heat_capacity(spectra_by_V, N=4))
    assert _is_fig(P.fig_mu_staircase(spectra_by_L, beta=1.0))
    assert _is_fig(P.fig_number_fluctuations(free, beta=1.0))
    assert _is_fig(P.fig_energy_ensembles(free, N=4))
    plt.close("all")


def test_scaling_figures_build(spectra_by_V, spectra_by_L):
    by_V_L = {V: {3: s} for V, s in spectra_by_V.items()}
    by_V_L[0.0] = spectra_by_L  # give V=0 two sizes for a fit
    assert _is_fig(P.fig_scaling(by_V_L, beta=1.0))
    assert _is_fig(P.fig_interaction_dependence(by_V_L, beta=1.0))
    plt.close("all")


def test_entropy_figures_build(spectra_by_V, spectra_by_L):
    free = spectra_by_V[0.0]
    assert _is_fig(P.fig_entropy_temperature(spectra_by_V, N=4))
    assert _is_fig(P.fig_entropy_convergence(spectra_by_L))
    assert _is_fig(P.fig_microcanonical_entropy(free, N=4))
    assert _is_fig(P.fig_caloric_curve(free, N=4))
    plt.close("all")


def test_interaction_sweep_builds():
    import numpy as np

    # Tiny V-grid keeps the smoke test fast (diagonalizes L=3 on the fly).
    fig = P.fig_interaction_sweep(L=3, beta=1.0, V_array=np.array([-2.0, 0.0, 2.0]))
    assert _is_fig(fig)
    plt.close("all")


def test_temperature_figures_build(spectra_by_L):
    import numpy as np

    from qlge.scaling import temperature_sweep

    T = np.geomspace(0.3, 5.0, 6)
    sweeps = {V: temperature_sweep(spectra_by_L, 1.0 / T) for V in (0.0, -2.0)}
    assert _is_fig(P.fig_temperature_exponents(sweeps))
    assert _is_fig(P.fig_number_channel_temperature(sweeps, M_largest=9))
    plt.close("all")
