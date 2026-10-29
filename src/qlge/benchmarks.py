"""Analytical baselines for the number-channel equivalence metric.

Three limits bracket what sigma_N/<N> should do, independently of ED:

1. Infinite temperature (beta -> 0 at fixed filling n = N/M). Every Fock state
   is equally weighted, so the grand-canonical N is binomial(M, n):

       sigma_N / <N> = sqrt((1 - n) / (n M)),

   an exact M^{-1/2} law for any t and V.

2. Classical limit (t = 0). With n_i = (1 + s_i)/2 the lattice gas is an Ising
   model with coupling J = -V/4 and zero field at the particle-hole symmetric
   point mu = zV/2 (half filling). For attraction (V < 0) it is a ferromagnet,
   and on the infinite square lattice Onsager gives

       T_c = 2J / ln(1 + sqrt 2) = |V| / (2 ln(1 + sqrt 2)) ~ 0.567 |V|.

   Below T_c the grand ensemble at half filling splits into a dense and a dilute
   phase: N = M(1 + m)/2 with spontaneous magnetization m = +/- m_0 (Yang), so

       sigma_N / <N>  ->  m_0(T) = [1 - sinh(2J/T)^{-4}]^{1/8}    (M -> inf),

   a size-independent value instead of a decay. This is phase separation seen
   through the number channel.

3. Quantum anisotropy. Hard-core bosons map to the spin-1/2 XXZ model
   (b^dag = S^+, n = S^z + 1/2):

       H = sum_<ij> [ -2t (S^x S^x + S^y S^y) + V S^z S^z ] + field.

   For V < 0 this is a ferromagnet with J_z = |V| and J_xy = 2t. It is Ising-like
   (easy axis, finite-T phase separation) only for V < -2t; V = -2t is the
   SU(2) Heisenberg point, where Mermin-Wagner forces T_c = 0; for -2t < V < 0
   it is easy-plane (superfluid, no phase separation). Hopping therefore lowers
   T_c below the classical value and drives it to zero at V = -2t.

4. The Heisenberg point itself (V = -2t), as T -> 0. The model is then exactly
   an SU(2) ferromagnet on any connected lattice; its ground multiplet has total
   spin M/2 and one state in every N-sector. At the particle-hole symmetric mu
   those M + 1 states are degenerate, so the grand ensemble is uniform on
   N = 0..M and, for even M,

       sigma_N / <N> = sqrt((M + 2) / (3M))  ->  1/sqrt(3)    (M -> inf),

   size-independent like the phase-separated case, but at a smaller value.

Conventions: k_B = 1, energies in units of t (theory/README.md). The Ising
results are thermodynamic-limit statements for the square lattice; the 2x2
torus (a 4-site ring) and the 3x3 torus are not square-lattice-like enough for
them to apply quantitatively.
"""

from __future__ import annotations

import numpy as np

ONSAGER_FACTOR = 2.0 / np.log(1.0 + np.sqrt(2.0))  # k T_c / J for the square lattice


def infinite_temperature_number_fluctuation(M: int | np.ndarray, N: float) -> np.ndarray:
    """beta -> 0 limit of sigma_N/<N> at matched <N> = N (binomial statistics)."""
    M = np.asarray(M, dtype=float)
    n = N / M
    return np.sqrt((1.0 - n) / (n * M))


def ising_coupling(V: float) -> float:
    """Ising J for the t = 0 lattice gas (H_Ising = -J sum s_i s_j); J > 0 for V < 0."""
    return -V / 4.0


def ising_critical_temperature(V: float) -> float:
    """Onsager T_c of the t = 0 lattice gas at half filling (square lattice).

    The bipartite square lattice maps antiferromagnet onto ferromagnet, so T_c
    depends only on |V|: for V > 0 it marks checkerboard (solid) ordering, for
    V < 0 phase separation. Returns 0 for V == 0.
    """
    return ONSAGER_FACTOR * abs(V) / 4.0


def ising_number_fluctuation(V: float, T: np.ndarray | float) -> np.ndarray:
    """Thermodynamic-limit sigma_N/<N> at half filling for the t = 0 gas, V < 0.

    Equals Yang's spontaneous magnetization m_0(T) below T_c and 0 above. For
    V >= 0 the order parameter does not couple to N, so this returns 0.
    """
    T = np.asarray(T, dtype=float)
    if V >= 0:
        return np.zeros_like(T)
    J = ising_coupling(V)
    with np.errstate(divide="ignore", over="ignore", invalid="ignore"):
        inv4 = np.sinh(2.0 * J / T) ** -4.0
        m = np.where(T < ising_critical_temperature(V), (1.0 - inv4) ** 0.125, 0.0)
    return np.nan_to_num(m, nan=0.0)


def heisenberg_number_fluctuation(M: int | np.ndarray) -> np.ndarray:
    """T -> 0 limit of sigma_N/<N> at V = -2t and half filling (even M)."""
    M = np.asarray(M, dtype=float)
    return np.sqrt((M + 2.0) / (3.0 * M))


def phase_separates(V: float, t: float = 1.0) -> bool:
    """True when the XXZ mapping is easy-axis (V < -2|t|): finite-T phase separation."""
    return V < -2.0 * abs(t)
