"""Independent cross-checks of the physics (verification gates).

These go beyond unit tests: they confirm results against an independent
eigensolver (Lanczos), exact thermodynamic identities evaluated via numerical
derivatives, and symmetry arguments -- the checks one would run to trust the
output, not just the code paths.
"""

from __future__ import annotations

import numpy as np
import pytest
import scipy.sparse.linalg as sla

from qlge.config import RunConfig
from qlge.diagonalize import diagonalize
from qlge.ensembles import log_Xi
from qlge.hamiltonian import build_from_config
from qlge.observables import canonical, grand


@pytest.mark.parametrize("L,V", [(3, 0.0), (3, 2.0), (3, -2.0)])
def test_ground_state_matches_lanczos(L, V):
    # Independent algorithm: sparse Lanczos vs our dense full-spectrum ground state.
    N = (L * L) // 2
    _, H = build_from_config(RunConfig(L=L, V=V, bc="periodic"), N)
    dense = float(np.linalg.eigvalsh(H.toarray()).min())
    lanczos = float(sla.eigsh(H.astype(float), k=1, which="SA", return_eigenvectors=False)[0])
    assert dense == pytest.approx(lanczos, abs=1e-8)


def test_heat_capacity_equals_dE_dT():
    # Fluctuation identity C_V = beta^2 Var(E) must equal the numerical dE/dT.
    spec = diagonalize(RunConfig(L=3, V=0.0, bc="periodic"))
    T = np.linspace(0.3, 5.0, 400)
    res = canonical(spec, 4, 1.0 / T)
    dEdT = np.gradient(res.energy, T)
    rel = np.abs(res.heat_capacity - dEdT) / (np.abs(dEdT) + 1e-9)
    assert np.median(rel[10:-10]) < 1e-2


def test_meanN_equals_dlnXi_dmu():
    # Grand identity <N> = (1/beta) d ln Xi / d mu.
    spec = diagonalize(RunConfig(L=3, V=0.0, bc="periodic"))
    beta = 1.3
    mu = np.linspace(-3, 3, 400)
    Nw = grand(spec, beta, mu).mean_N
    Nderiv = (1.0 / beta) * np.gradient(log_Xi(spec, beta, mu), mu)
    assert np.max(np.abs(Nw - Nderiv)[5:-5]) < 1e-2


@pytest.mark.parametrize("L", [2, 3])
def test_half_filling_at_mu_zero(L):
    # Particle-hole (N <-> M-N) symmetry pins <N> = M/2 at mu=0 for every L.
    # (Checked up to L=4 out of band; L<=3 keeps the test fast.)
    spec = diagonalize(RunConfig(L=L, V=0.0, bc="periodic"))
    M = L * L
    n0 = grand(spec, 1.0, np.array([0.0])).mean_N[0]
    assert n0 == pytest.approx(M / 2, abs=1e-6)


@pytest.mark.parametrize("L,bipartite", [(2, True), (3, False)])
def test_spectral_symmetry_only_for_bipartite(L, bipartite):
    # E <-> -E spectral symmetry (V=0) holds only for bipartite lattices: even L
    # under PBC. The odd-L torus is frustrated and must NOT be symmetric.
    # (L=4 verified even/bipartite -> symmetric out of band.)
    spec = diagonalize(RunConfig(L=L, V=0.0, bc="periodic"))
    allE = np.sort(spec.all_eigenvalues())
    symmetric = np.allclose(allE, -allE[::-1], atol=1e-8)
    assert symmetric == bipartite
