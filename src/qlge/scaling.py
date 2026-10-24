"""Finite-size scaling of ensemble discrepancies (theory/07; PLAN.md Phase 5).

Sweep lattice size L (and interaction V) at matched filling and inverse
temperature, collect the robust equivalence metrics, and fit their decay with
system size M = L^2. The scientific claim is the *trend*: the relative
fluctuations and the per-site canonical<->grand energy gap shrink toward zero as
M grows, quantifying how ensemble equivalence emerges (and how V changes it).
"""

from __future__ import annotations

import glob
import os
from dataclasses import dataclass

import numpy as np

from qlge.diagonalize import Spectrum
from qlge.matching import MatchResult, match_ensembles


@dataclass
class ScalingPoint:
    L: int
    M: int
    V: float
    N: int
    beta: float
    rel_energy_fluctuation: float
    rel_number_fluctuation: float
    energy_discrepancy_per_site: float

    @classmethod
    def from_match(cls, L: int, V: float, r: MatchResult) -> ScalingPoint:
        return cls(
            L=L,
            M=r.M,
            V=V,
            N=r.N,
            beta=r.beta,
            rel_energy_fluctuation=r.rel_energy_fluctuation,
            rel_number_fluctuation=r.rel_number_fluctuation,
            energy_discrepancy_per_site=r.energy_discrepancy_per_site,
        )


def filling_to_N(M: int, filling: float) -> int:
    """Target particle number for a given filling fraction, kept in (0, M)."""
    N = int(round(filling * M))
    return min(max(N, 1), M - 1)


def scaling_sweep(
    spectra: dict[int, Spectrum],
    beta: float,
    filling: float = 0.5,
) -> list[ScalingPoint]:
    """Collect scaling points across the provided spectra (keyed by L).

    All spectra should share the same V and boundary condition; only L varies.
    """
    points: list[ScalingPoint] = []
    for L in sorted(spectra):
        spec = spectra[L]
        N = filling_to_N(spec.config.n_sites, filling)
        r = match_ensembles(spec, N, beta)
        points.append(ScalingPoint.from_match(L, spec.config.V, r))
    return points


@dataclass
class PowerLawFit:
    """Fit y = amplitude * M^exponent via least squares in log-log space."""

    exponent: float
    amplitude: float
    r_squared: float

    def predict(self, M: np.ndarray) -> np.ndarray:
        return self.amplitude * np.asarray(M, dtype=float) ** self.exponent


def fit_power_law(M: np.ndarray, y: np.ndarray) -> PowerLawFit:
    """Least-squares power-law fit. Requires >= 2 positive finite points."""
    M = np.asarray(M, dtype=float)
    y = np.asarray(y, dtype=float)
    mask = np.isfinite(M) & np.isfinite(y) & (M > 0) & (y > 0)
    if mask.sum() < 2:
        raise ValueError("need >= 2 positive finite points to fit a power law")
    lx, ly = np.log(M[mask]), np.log(y[mask])
    slope, intercept = np.polyfit(lx, ly, 1)
    # Coefficient of determination in log space.
    resid = ly - (slope * lx + intercept)
    ss_res = float(np.sum(resid**2))
    ss_tot = float(np.sum((ly - ly.mean()) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 1.0
    return PowerLawFit(exponent=float(slope), amplitude=float(np.exp(intercept)), r_squared=r2)


def load_spectra_by_L(
    V: float, bc: str = "periodic", data_dir: str = "data"
) -> dict[int, Spectrum]:
    """Load every cached spectrum matching V and bc, keyed by L."""
    out: dict[int, Spectrum] = {}
    for path in sorted(glob.glob(os.path.join(data_dir, "spectrum_*.npz"))):
        spec = Spectrum.load(path)
        if spec.config.V == V and spec.config.bc == bc:
            out[spec.config.L] = spec
    return out
