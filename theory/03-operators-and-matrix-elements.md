# 3. Operators and matrix elements

Goal: compute `H|state⟩` for every basis `state` in an `N`-sector, giving the nonzero entries of the Hamiltonian block.

## Hard-core boson algebra

Hard-core bosons behave like ordinary bosons on **different** sites and like fermions (Pauli exclusion) on the **same** site:

```
b_i² = (b_i†)² = 0                 (no double occupancy)
[b_i, b_j†] = 0        for i ≠ j   (commute on different sites)
{b_i, b_i†} = 1                     (anticommute-like on the same site)
n_i = b_i† b_i ∈ {0,1}
```

Equivalently they are spin-1/2 raising/lowering operators: `b_i† = S_i⁺`, `b_i = S_i⁻`, `n_i = S_i^z + 1/2`. There are **no fermionic exchange signs** between sites in this bosonic convention — this is the simplest and recommended choice for 2D. (If you instead map to fermions via Jordan–Wigner you must track string signs; avoid unless cross-checking.)

## Interaction term (diagonal)

`V Σ_<i,j> n_i n_j` is diagonal in the occupation basis. For a given `state`:

```
E_int(state) = V · (number of nearest-neighbor bonds with both endpoints occupied)
```

i.e. loop over the bond list, add `V` for each bond whose two sites both have their bit set. This contributes to the diagonal matrix element `H[state, state]`.

## Hopping term (off-diagonal)

`-t Σ_<i,j> (b_i† b_j + b_j† b_i)` moves one particle across a bond. For each nearest-neighbor bond `(i, j)` and each `state`:

- If site `j` occupied and site `i` empty: `b_i† b_j` produces `state'` = (`state` with `j` cleared, `i` set), with amplitude `-t`.
- If site `i` occupied and site `j` empty: `b_j† b_i` produces the reverse move, amplitude `-t`.
- If both occupied or both empty: that direction gives zero.

Each successful move contributes `H[state', state] += -t`. Because hard-core bosons carry no inter-site sign, the amplitude is simply `-t` (no `±`). The resulting block is real symmetric.

### Pseudocode (one N-sector)

```
for each state in sector:                     # column 'state'
    H[state, state] += V * occupied_bond_count(state)   # diagonal interaction
    for (i, j) in nearest_neighbor_bonds:
        if occupied(state, j) and empty(state, i):
            state2 = move_particle(state, from=j, to=i)
            H[index[state2], index[state]] += -t
        if occupied(state, i) and empty(state, j):
            state2 = move_particle(state, from=i, to=j)
            H[index[state2], index[state]] += -t
```

`index[·]` is the state-integer → row-index map from [`02`](02-hilbert-space-and-basis.md). Hopping conserves `N`, so `state2` is always in the same sector — its index always exists.

## Lattice geometry and boundary conditions

The bond list depends on boundary conditions on the `L×L` grid:

- **Open (OBC)**: a site at `(x,y)` bonds to `(x+1,y)` and `(x,y+1)` only when the neighbor is inside the grid. Fewer bonds; stronger finite-size/edge effects.
- **Periodic (PBC)**: neighbors wrap, `(x+1 mod L, y)` and `(x, y+1 mod L)`. More uniform, restores translation symmetry, usually smaller finite-size effects. Preferred for the finite-size-scaling study.

Flatten 2D coordinates to the site index with `i = x + L*y`. Build the bond list once and reuse it for every state and every sector.

## Correctness checks (do these before trusting any spectrum)

- `H` is Hermitian / real-symmetric: `max|H - H†| ≈ 0` to machine precision.
- `N̂` conservation: hopping never changes `popcount`; verify no matrix element connects different sectors.
- Dimensions: assembled block size equals `C(M, N)`.
- `V = 0`, `2×2` lattice: compare eigenvalues against a hand or independent calculation.
- Trace check: `Tr H = V · Σ_states (occupied bonds)` since hopping is purely off-diagonal.
