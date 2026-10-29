"""Tilted clusters and symmetry-reduced ED (cluster.py, symmetry.py)."""

from __future__ import annotations

import numpy as np
import pytest

from qlge.basis import Sector
from qlge.cluster import TILTED_CLUSTERS, Cluster, tilted_cluster
from qlge.config import RunConfig
from qlge.diagonalize import Spectrum, diagonalize, diagonalize_sector
from qlge.symmetry import bloch_basis, particle_hole_shift


@pytest.mark.parametrize("M", sorted(TILTED_CLUSTERS))
def test_cluster_geometry(M):
    c = tilted_cluster(M)
    assert c.M == M
    assert c.bipartite and c.coordination_ok  # four distinct neighbors, 2M bonds
    # Checkerboard coloring: every bond joins the two sublattices.
    parity = (c.sites.sum(axis=1)) % 2
    assert all(parity[i] != parity[j] for i, j in c.bonds)
    # Translations form a group of permutations; stars partition the momenta.
    assert all(sorted(row) == list(range(M)) for row in c.translations)
    assert sum(size for _, size in c.momentum_stars) == M


def test_small_tori_fail_the_geometry_tests():
    assert not Cluster((2, 0), (0, 2)).coordination_ok  # 2x2 torus is a 4-ring
    assert not Cluster((3, 0), (0, 3)).bipartite


@pytest.mark.parametrize("M", [8, 10])
def test_one_particle_band(M):
    # V is irrelevant for N = 1: eigenvalues are -2t(cos kx + cos ky) on allowed k.
    c = tilted_cluster(M)
    spec = diagonalize(RunConfig(cluster=TILTED_CLUSTERS[M], V=1.7, n_sectors=(1,)))
    band = np.sort(-2 * (np.cos(c.momenta[:, 0]) + np.cos(c.momenta[:, 1])))
    assert np.allclose(spec.eigenvalues[1], band, atol=1e-12)


def test_bloch_columns_orthonormal():
    c = tilted_cluster(10)
    sector = Sector(10, 5)
    total = 0
    for j in range(c.M):
        V = bloch_basis(sector, c, j)
        G = (V.conj().T @ V).toarray()
        assert np.allclose(G, np.eye(V.shape[1]), atol=1e-12)
        total += V.shape[1]
    assert total == sector.dim


@pytest.mark.parametrize("M,V", [(8, -3.0), (8, 2.0), (10, -2.0), (10, 0.0), (10, 3.0)])
def test_symmetric_spectrum_matches_direct(M, V):
    config = RunConfig(cluster=TILTED_CLUSTERS[M], V=V)
    spec = diagonalize(config)
    for N in range(M + 1):
        assert np.allclose(spec.eigenvalues[N], diagonalize_sector(config, N), atol=1e-10)


def test_square_cluster_matches_L4_torus():
    # The M = 16 member of the family is the 4x4 torus.
    sectors = (2, 3, 13, 14)
    a = diagonalize(RunConfig(cluster=TILTED_CLUSTERS[16], V=-1.5, n_sectors=sectors))
    for N in sectors:
        assert np.allclose(a.eigenvalues[N], diagonalize_sector(RunConfig(L=4, V=-1.5), N), atol=1e-10)


def test_particle_hole_shift():
    config = RunConfig(cluster=TILTED_CLUSTERS[10], V=2.5)
    c = config.cluster_geometry()
    for N in (1, 3, 4):
        shifted = np.sort(diagonalize_sector(config, N) + particle_hole_shift(c, 2.5, N))
        assert np.allclose(shifted, diagonalize_sector(config, 10 - N), atol=1e-10)


def test_cluster_config_roundtrip(tmp_path):
    config = RunConfig(cluster=TILTED_CLUSTERS[8], V=-1.0)
    assert config.n_sites == 8 and config.tag() == "C8_t1_V-1_periodic"
    with pytest.raises(ValueError):
        RunConfig(cluster=TILTED_CLUSTERS[8], bc="open")
    path = tmp_path / "s.npz"
    diagonalize(config).save(str(path))
    assert Spectrum.load(str(path)).config == config
