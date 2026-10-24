# 1. The model Hamiltonian

## Physical picture

Ultracold bosonic atoms sit in a periodic optical lattice formed by intersecting laser beams. Each site is a potential well; atoms tunnel (hop) between neighboring wells. In the **hard-core limit** the on-site repulsion is so strong that two atoms can never occupy the same site, so every site holds either 0 or 1 boson. This is the regime the project studies.

The model captures three effects:

- **Hopping** — atoms move between neighboring sites (kinetic energy, amplitude `t`).
- **Quantum superposition** — a particle is generally delocalized over many sites.
- **Interactions** — neighboring occupied sites cost (or gain) energy `V`.

## Hamiltonian

On a square lattice,

```
H = -t Σ_<i,j> ( b_i† b_j + b_j† b_i )  +  V Σ_<i,j> n_i n_j
```

- `Σ_<i,j>` runs over **nearest-neighbor pairs**, each counted once.
- `b_i†`, `b_i` create / annihilate a boson at site `i`, subject to the hard-core constraint below.
- `n_i = b_i† b_i` is the number operator at site `i` (eigenvalues 0 or 1).
- The first term lowers energy for delocalized states; the second penalizes (`V>0`) or rewards (`V<0`) adjacent occupation.

### Hard-core constraint

```
n_i ∈ {0, 1},     b_i² = (b_i†)² = 0.
```

A site cannot be doubly occupied. This truncates the local Hilbert space to 2 states, which is what makes exact diagonalization feasible (see [`02`](02-hilbert-space-and-basis.md)).

## Parameters and regimes

| Parameter | Role | Project use |
| --- | --- | --- |
| `t` | hopping energy scale | sets the energy unit; usually `t = 1` |
| `V` | nearest-neighbor interaction | `V = 0` validation (free hard-core bosons), then `V/t ≠ 0` for interacting physics |
| `L` | linear size (`M = L²` sites) | start at `2×2`, scale up for finite-size study |

Start with `V = 0`: the non-interacting hard-core gas has analytic / easily-checked results, so it validates the code. Then turn on `V` for the genuine interacting results.

## Symmetries and conservation laws

- **Particle-number conservation**: `[H, N̂] = 0` with `N̂ = Σ_i n_i`. Hopping moves a particle without changing the total; the interaction is diagonal in occupation. Consequence: `H` is block-diagonal in `N`, so each sector is diagonalized independently. This is the single most important structural fact for the implementation.
- **Hermiticity**: `H = H†`. The hopping term is written symmetrically (`b_i† b_j + b_j† b_i`) precisely so it is Hermitian; the interaction is real diagonal. Asserting Hermiticity on the assembled matrix is a primary correctness check.
- **Lattice symmetries** (translations, point-group rotations/reflections, and for `V=0` a particle–hole-like mapping). Not required for a first working code, but they further block-diagonalize `H` and can be used to check degeneracies.

## Mapping to spin-1/2 / fermions

The hard-core boson algebra is isomorphic to spin-1/2: `b_i† ↔ S_i⁺`, `n_i ↔ S_i^z + 1/2`. So this is equivalent to an XY model with an Ising `n_i n_j` coupling in a sense fixed by `N` (magnetization). In 1D a Jordan–Wigner transformation maps it to free fermions when `V=0`; in 2D the transformation carries nontrivial strings, so direct exact diagonalization in the occupation basis is the practical route. These mappings are useful mainly as independent cross-checks of numerical spectra.
