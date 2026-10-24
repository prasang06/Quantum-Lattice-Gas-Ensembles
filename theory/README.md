# Theory

Background needed to implement and interpret the quantum-lattice-gas ensemble project. Each file is self-contained but builds on the previous ones.

Read in order:

1. [`01-model-hamiltonian.md`](01-model-hamiltonian.md) — the hard-core Bose–Hubbard model, parameters, symmetries.
2. [`02-hilbert-space-and-basis.md`](02-hilbert-space-and-basis.md) — occupation-number basis, bit encoding, particle-number sectors, dimensions.
3. [`03-operators-and-matrix-elements.md`](03-operators-and-matrix-elements.md) — hard-core algebra, hopping/interaction matrix elements, fermion-vs-boson sign conventions.
4. [`04-exact-diagonalization.md`](04-exact-diagonalization.md) — assembling the sparse Hamiltonian and diagonalizing it.
5. [`05-statistical-ensembles.md`](05-statistical-ensembles.md) — microcanonical, canonical, grand-canonical definitions and how they share one spectrum.
6. [`06-thermodynamic-observables.md`](06-thermodynamic-observables.md) — entropy, energy, heat capacity, compressibility, number fluctuations.
7. [`07-ensemble-equivalence.md`](07-ensemble-equivalence.md) — why ensembles agree in the thermodynamic limit and what finite size does.
8. [`08-numerical-methods.md`](08-numerical-methods.md) — energy windows, finite differences, root-finding for μ, validation checks.

## Notation used throughout

| Symbol | Meaning |
| --- | --- |
| `L` | linear lattice size; number of sites `M = L²` for an `L×L` square lattice |
| `t` | hopping amplitude |
| `V` | nearest-neighbor interaction energy |
| `N` | total particle number (conserved) |
| `β` | inverse temperature, `β = 1/(k_B T)` |
| `μ` | chemical potential |
| `E_{N,α}` | α-th energy eigenvalue in the N-particle sector |
| `Ω, Z, Ξ` | microcanonical count, canonical partition function, grand partition function |

Units: set `k_B = 1` and measure energy in units of `t` (so the free parameters are `V/t`, `T/t`, `μ/t`) unless a file states otherwise.
