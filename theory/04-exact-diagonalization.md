# 4. Exact diagonalization

Exact diagonalization (ED) means building the Hamiltonian matrix in a chosen basis and computing its eigenvalues (and eigenvectors if needed) numerically, with no approximation beyond floating point. It is the standard benchmark method for small Bose–Hubbard systems.

## Workflow

For each particle-number sector `N`:

1. **Enumerate** the sector basis: all bit strings with `popcount == N` (dimension `C(M,N)`). Build the `state → index` map.
2. **Assemble** the block using the matrix elements from [`03`](03-operators-and-matrix-elements.md). Store sparse (COO/CSR) — hopping produces only O(bonds) nonzeros per column.
3. **Diagonalize** to obtain `{E_{N,α}}` (and `{|ψ_{N,α}⟩}` if computing observables beyond energy).
4. **Store** the eigenvalues per sector. The complete set `{E_{N,α} : N = 0..M}` is the one object every ensemble calculation consumes.

## Dense vs. sparse / full vs. partial

- **Dense, full spectrum** (`numpy.linalg.eigh` / LAPACK `syev`/`heev`): returns *all* eigenvalues. Required here — the canonical and grand-canonical partition functions sum over the **entire** spectrum, so you cannot use a few-eigenvalue Lanczos solver for the thermodynamics. Cost ~ `O(dim³)` time, `O(dim²)` memory.
- **Sparse, partial** (Lanczos / `scipy.sparse.linalg.eigsh`): returns only the lowest (or a few) eigenvalues. Useful for ground-state checks and for pushing to larger `L`, but insufficient for full partition functions.

Because full spectra are needed, the largest feasible sector dimension (half filling, `C(M, M/2)`) sets the hard size limit.

## Practical size limits (full spectrum, real symmetric)

| `L` | `M` | largest sector `C(M,M/2)` | dense ED feasibility |
| --- | --- | --- | --- |
| 2 | 4 | 6 | trivial |
| 3 | 9 | 126 | instant |
| 4 | 16 | 12 870 | seconds–minutes, GBs for all eigenvectors |
| 5 | 25 | 5 200 300 | full dense spectrum infeasible on a workstation |

So full-spectrum ensemble comparisons are realistic up to about `L=4` (`4×4`); `L=5` and beyond need symmetry reduction or a different method and are out of scope for the core validation.

## Reducing cost with symmetry (optional)

Momentum (translation) and point-group symmetries further block-diagonalize each `N`-sector into smaller irreducible blocks, lowering the `O(dim³)` cost and exposing degeneracies. Not needed for `L ≤ 3` and for a first correct implementation; consider only if pushing `L = 4` eigenvector calculations or `L = 5` ground states.

## Numerical hygiene

- Use a symmetric/Hermitian eigensolver (`eigh`), not the general one — it is faster and guarantees real eigenvalues.
- Eigenvalues come out sorted ascending; keep them that way for energy-window binning in the microcanonical calculation.
- Shift energies by the ground-state energy `E_0` before exponentiating (`e^{-β(E-E_0)}`) to avoid overflow in partition functions (see [`08`](08-numerical-methods.md)).
- Record `t`, `V`, `L`, boundary condition, and solver with the stored spectra so results are reproducible.
