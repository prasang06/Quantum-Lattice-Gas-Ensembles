# 5. The three statistical ensembles

The central idea of the project: **the same Hamiltonian and the same eigenvalues** `{E_{N,α}}` feed all three ensembles. Only the constraints and statistical weights differ. Compute the per-sector spectra once (parts [`02`](02-hilbert-space-and-basis.md)–[`04`](04-exact-diagonalization.md)), then post-process.

Units: `k_B = 1`, `β = 1/T`.

## A. Microcanonical ensemble — fixed `(N, E)`

Fix total particle number `N`, lattice size, and an energy window. Count eigenstates inside the window:

```
Ω(E, N; ΔE) = #{ α : E ≤ E_{N,α} < E + ΔE }
```

Entropy:

```
S(E, N) = k_B ln Ω(E, N; ΔE)
```

Temperature and chemical potential come from finite differences of the entropy:

```
1/T = (∂S/∂E)_N              # vary E at fixed N
μ/T = -(∂S/∂N)_E             # vary N at fixed E
```

Because the spectrum is **discrete**, `Ω` depends on the window width `ΔE`, and the derivatives must be taken as finite differences. These choices are modeling decisions and must be documented and varied to assess sensitivity (see [`08`](08-numerical-methods.md)). This is the ensemble with the most numerical subtlety.

## B. Canonical ensemble — fixed `(N, T)`

Fix `N` and temperature. Using the same fixed-`N` eigenvalues:

```
Z_N(β) = Σ_α e^{-β E_{N,α}}
⟨E⟩_N  = -∂ ln Z_N / ∂β = (1/Z_N) Σ_α E_{N,α} e^{-β E_{N,α}}
```

`N` is fixed; energy fluctuates and is exchanged with a heat bath. Compare `⟨E⟩_N(T)` with the microcanonical energy at the temperature inferred from `(∂S/∂E)`; agreement validates both calculations.

## C. Grand-canonical ensemble — fixed `(T, μ)`

Fix temperature and chemical potential; let `N` fluctuate. Stitch the sectors together:

```
Ξ(β, μ) = Σ_N e^{βμN} Z_N(β) = Σ_N Σ_α e^{-β(E_{N,α} - μN)}
```

Mean particle number and mean energy:

```
⟨N⟩ = (1/β) ∂ ln Ξ / ∂μ
⟨E⟩ = -∂ ln Ξ / ∂β + μ⟨N⟩
```

Equivalently, with the grand weight `p_{N,α} = e^{-β(E_{N,α} - μN)} / Ξ`:

```
⟨N⟩ = Σ_{N,α} N · p_{N,α}
⟨E⟩ = Σ_{N,α} E_{N,α} · p_{N,α}
```

The second form is the robust way to evaluate it numerically (no explicit differentiation of `Ξ`).

## Linking the ensembles (the actual experiment)

1. Pick a sector `N` and an energy (or energy window) → microcanonical `S`, and from its derivatives an inferred `T` and `μ`.
2. Feed that `T` into the canonical ensemble at the same `N`; check `⟨E⟩_N(T)` matches the microcanonical energy.
3. Feed that `(T, μ)` into the grand-canonical ensemble; **tune `μ`** so `⟨N⟩` equals the target `N` (root-find, [`08`](08-numerical-methods.md)); check `⟨E⟩` and other observables match.
4. Quantify the discrepancies and watch them shrink as `L` grows ([`07`](07-ensemble-equivalence.md)).

The deliverable is not three partition functions in isolation — it is the **controlled comparison** of observables computed three ways from one spectrum.
