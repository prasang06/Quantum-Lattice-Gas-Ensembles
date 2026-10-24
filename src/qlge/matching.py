"""Cross-ensemble parameter matching (theory/05, theory/08; PLAN.md Phase 4).

The core experiment: compute an observable three ways from one spectrum at matched
control parameters and check they agree.

Bridge logic:
  1. Canonical control: pick sector N and inverse temperature beta -> <E>_N(beta).
  2. Microcanonical: at energy E* = <E>_N estimate T via 1/T = (dS/dE)_N and
     mu via mu = -T (dS/dN)_E, using finite differences of S = ln Omega. Check
     the inferred T matches 1/beta.
  3. Grand-canonical: root-find mu* so <N>(beta, mu*) = N, then compare the grand
     <E> with the canonical <E>_N.

Finite differences on a discrete, window-binned entropy are a modeling choice;
dE and the difference step must be reported (theory/08).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import brentq

from qlge.diagonalize import Spectrum
from qlge.ensembles import entropy_micro, omega
from qlge.observables import canonical, mean_N_at


# ----------------------------------------------------------------------------
# Microcanonical inference of T and mu via finite differences
# ----------------------------------------------------------------------------


def micro_temperature(
    spectrum: Spectrum, N: int, E: float, dE: float, step: float | None = None
) -> float:
    """Microcanonical temperature at energy ``E`` from 1/T = (dS/dE)_N.

    Central difference of S = ln Omega with half-step ``step`` (defaults to dE).
    Returns ``np.nan`` if either window is empty.
    """
    step = dE if step is None else step
    ev = spectrum.eigenvalues[N]
    # Center windows on E +/- step (left edges shifted by dE/2 so the window
    # straddles the evaluation energy).
    s_plus = entropy_micro(ev, (E + step) - dE / 2, dE)
    s_minus = entropy_micro(ev, (E - step) - dE / 2, dE)
    if not (np.isfinite(s_plus) and np.isfinite(s_minus)):
        return float("nan")
    dSdE = (s_plus - s_minus) / (2 * step)
    return 1.0 / dSdE if dSdE != 0 else float("inf")


def micro_chemical_potential(
    spectrum: Spectrum, N: int, E: float, dE: float
) -> float:
    """Microcanonical chemical potential mu = -T (dS/dN)_E.

    N is integer so the N-derivative is a unit-step central difference between
    sectors N+1 and N-1 at the same energy window (theory/08). Requires both
    neighbor sectors to exist and have states in the window.
    """
    if (N + 1) not in spectrum.eigenvalues or (N - 1) not in spectrum.eigenvalues:
        return float("nan")
    left = E - dE / 2
    o_plus = omega(spectrum.eigenvalues[N + 1], left, dE)
    o_minus = omega(spectrum.eigenvalues[N - 1], left, dE)
    if o_plus <= 0 or o_minus <= 0:
        return float("nan")
    dSdN = (np.log(o_plus) - np.log(o_minus)) / 2.0
    T = micro_temperature(spectrum, N, E, dE)
    if not np.isfinite(T):
        return float("nan")
    return -T * dSdN


# ----------------------------------------------------------------------------
# Grand-canonical mu root-finding: <N>(beta, mu) = N_target
# ----------------------------------------------------------------------------


def find_mu(
    spectrum: Spectrum,
    beta: float,
    n_target: float,
    bracket: tuple[float, float] | None = None,
    xtol: float = 1e-10,
) -> float:
    """Chemical potential mu* with <N>(beta, mu*) = n_target.

    <N>(mu) is monotonically increasing, so the root is unique; solved with
    Brent's method. The bracket is auto-widened until it straddles the target.
    """
    M = spectrum.config.n_sites
    if not (0 < n_target < M):
        raise ValueError(f"n_target must lie strictly in (0, {M}), got {n_target}")

    def f(mu: float) -> float:
        return mean_N_at(spectrum, beta, mu) - n_target

    lo, hi = bracket if bracket is not None else (-20.0, 20.0)
    # Widen until sign change brackets the root.
    for _ in range(60):
        if f(lo) < 0 < f(hi):
            break
        lo *= 2.0
        hi *= 2.0
    else:
        raise RuntimeError("could not bracket mu root")
    return float(brentq(f, lo, hi, xtol=xtol))


# ----------------------------------------------------------------------------
# The matched comparison
# ----------------------------------------------------------------------------


@dataclass
class MatchResult:
    """Three-ensemble comparison at fixed (N, beta).

    The *robust* equivalence signals are the fluctuation ratios and the per-site
    energy gap, which are smooth sums over the spectrum and scale as ~1/sqrt(M)
    (theory/07). The microcanonical finite-difference T and mu are kept as a
    secondary, explicitly-noisy diagnostic (brittle on small bounded discrete
    spectra -- see the dE sweep in diagnostics).
    """

    N: int
    M: int                    # number of sites (for intensive/per-site metrics)
    beta: float
    dE: float

    # Canonical (fixed N, beta)
    energy_canonical: float   # <E>_N(beta)
    var_energy_canonical: float

    # Grand-canonical (fixed beta, mu*) with mu* tuned so <N> = N
    mu_grand: float
    energy_grand: float
    mean_N_grand: float       # == N by construction
    var_N_grand: float

    # Microcanonical finite-difference diagnostic (noisy; may be nan/inf)
    T_microcanonical: float
    mu_microcanonical: float

    # --- robust equivalence metrics ---------------------------------------
    @property
    def rel_energy_fluctuation(self) -> float:
        """sigma_E / |<E>| -- micro<->canonical equivalence signal (~1/sqrt(M))."""
        denom = abs(self.energy_canonical)
        return float(np.sqrt(self.var_energy_canonical) / denom) if denom > 0 else np.inf

    @property
    def rel_number_fluctuation(self) -> float:
        """sigma_N / <N> -- canonical<->grand equivalence signal (~1/sqrt(M))."""
        return float(np.sqrt(self.var_N_grand) / self.mean_N_grand) if self.mean_N_grand > 0 else np.inf

    @property
    def energy_discrepancy(self) -> float:
        """|<E>_grand - <E>_canonical| (extensive)."""
        return abs(self.energy_grand - self.energy_canonical)

    @property
    def energy_discrepancy_per_site(self) -> float:
        return self.energy_discrepancy / self.M

    @property
    def temperature_discrepancy(self) -> float:
        return abs(self.T_microcanonical - 1.0 / self.beta)


def match_ensembles(
    spectrum: Spectrum, N: int, beta: float, dE: float | None = None
) -> MatchResult:
    """Run the full three-ensemble comparison at fixed (N, beta)."""
    dE = spectrum.config.dE if dE is None else dE

    can = canonical(spectrum, N, beta=np.array([beta]))
    E_star = float(can.energy[0])
    varE = float(can.var_energy[0])

    T_micro = micro_temperature(spectrum, N, E_star, dE)
    mu_micro = micro_chemical_potential(spectrum, N, E_star, dE)

    mu_star = find_mu(spectrum, beta, float(N))
    w, energies, numbers = _grand_arrays(spectrum, beta, mu_star)
    N_grand = float(np.sum(w * numbers))
    E_grand = float(np.sum(w * energies))
    varN = float(np.sum(w * (numbers - N_grand) ** 2))

    return MatchResult(
        N=N,
        M=spectrum.config.n_sites,
        beta=beta,
        dE=dE,
        energy_canonical=E_star,
        var_energy_canonical=varE,
        mu_grand=mu_star,
        energy_grand=E_grand,
        mean_N_grand=N_grand,
        var_N_grand=max(varN, 0.0),
        T_microcanonical=T_micro,
        mu_microcanonical=mu_micro,
    )


def _grand_arrays(spectrum: Spectrum, beta: float, mu: float):
    from qlge.ensembles import grand_weights

    return grand_weights(spectrum, beta, mu)
