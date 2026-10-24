# 2. Hilbert space, basis, and sectors

## Occupation-number (Fock) basis

With the hard-core constraint each of the `M = L²` sites is either empty or singly occupied. A basis state is a string of occupation numbers

```
|n_0 n_1 … n_{M-1}⟩,   n_i ∈ {0,1}.
```

The full Hilbert space has dimension `2^M`. For an `L×L` lattice:

| `L` | `M = L²` | full dim `2^M` |
| --- | --- | --- |
| 2 | 4 | 16 |
| 3 | 9 | 512 |
| 4 | 16 | 65 536 |
| 5 | 25 | 33 554 432 |

`2^M` grows explosively — the reason the project "starts small and only scales up after validating."

## Bit encoding

Because each site is a single bit, encode a basis state as one integer whose bit `i` is `n_i`:

```
state = Σ_i n_i · 2^i
```

Then occupation, hopping, and counting become bit operations:

- occupancy of site `i`: `(state >> i) & 1`
- total number `N`: `popcount(state)`
- empty a site: `state & ~(1 << i)`; fill a site: `state | (1 << i)`
- move a particle from `j` to `i`: clear bit `j`, set bit `i`.

This makes basis manipulation O(1) per operation and is the standard exact-diagonalization representation.

## Particle-number sectors

Since `[H, N̂] = 0`, states of fixed `N` do not mix. The `N`-particle sector is spanned by all bit strings with exactly `N` set bits; its dimension is

```
dim(N) = C(M, N)   (binomial coefficient)
```

and `Σ_{N=0}^{M} C(M,N) = 2^M`, so the sectors partition the full space. Example (`L=2`, `M=4`): sector dims are `1, 4, 6, 4, 1` for `N = 0..4`.

**Work one sector at a time.** For each `N`:

1. Enumerate all integers in `[0, 2^M)` with `popcount == N` (or generate combinations directly). These are the sector basis states.
2. Build an index map `state_integer → row index` (e.g. a hash map or a sorted array with binary search) so matrix elements can look up the column that a hopped state lands in.
3. Assemble and diagonalize the `dim(N) × dim(N)` Hamiltonian block.

The largest block is at half filling `N = M/2`, where `C(M, M/2)` dominates the cost.

## Why the sector structure matters

- It shrinks the matrices by orders of magnitude versus the full `2^M` space.
- It is exactly the structure the ensembles exploit: microcanonical and canonical quantities are computed **inside a fixed `N`** from `{E_{N,α}}`, and the grand-canonical sum stitches sectors together with the weight `e^{βμN}` (see [`05`](05-statistical-ensembles.md)). So the per-sector eigenvalues `{E_{N,α}}` are the central data object the whole project produces once and reuses.
