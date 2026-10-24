"""Quantum lattice gas: exact diagonalization and ensemble equivalence.

2D hard-core Bose-Hubbard model. See PLAN.md for the build plan and theory/ for
the physics. This package is organized so the expensive step (diagonalization)
runs once and caches, while ensemble post-processing is cheap and reusable.
"""

from qlge.config import RunConfig

__all__ = ["RunConfig"]
__version__ = "0.1.0"
