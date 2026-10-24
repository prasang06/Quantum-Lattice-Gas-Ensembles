# 8. Numerical methods and pitfalls

Practical recipes for turning the spectra `{E_{N,α}}` into reliable thermodynamics.

## Overflow-safe partition functions

Never exponentiate raw energies. Shift by a reference (the global ground state `E_0`, or the per-sum maximum weight):

```
Z_N(β) = e^{-β E_0} Σ_α e^{-β (E_{N,α} - E_0)}
```

Only energy **differences** enter observables, so the `e^{-β E_0}` prefactor cancels in means and in ratios like `p_α`. For the grand sum, shift the exponent `E_{N,α} - μN` by its minimum over all `(N,α)` before exponentiating. Equivalently, use a **log-sum-exp**:

```
ln Ξ = a + ln Σ_{N,α} e^{(-β(E_{N,α}-μN)) - a},   a = max_{N,α} (-β(E_{N,α}-μN))
```

This is the single most common bug source in finite-temperature ED post-processing — get it right first.

## Microcanonical energy window `ΔE`

- The spectrum is discrete, so `Ω(E,N;ΔE)` is a histogram; results depend on `ΔE`.
- Choose `ΔE` large enough to contain several levels (smooth `S`) but small compared to the energy scale over which `S` varies. A rule of thumb: a few × the **mean level spacing** in the region of interest.
- Report `S(E)` for **several** `ΔE` values and show the inferred `T`, `μ` are stable; this sensitivity analysis is part of the deliverable.
- Optional smoothing: Gaussian-broaden each level, `Ω(E) = Σ_α g(E - E_{N,α})` with width `σ ~ ΔE`, for a differentiable `S(E)`.

## Finite differences for `T` and `μ`

From `S(E,N) = ln Ω`:

```
1/T = (∂S/∂E)_N ≈ [S(E+δE, N) - S(E-δE, N)] / (2 δE)     # central difference
μ/T = -(∂S/∂N)_E ≈ -[S(E, N+1) - S(E, N-1)] / 2          # N is integer: step = 1
```

- Use **central** differences where possible (second-order accurate).
- `N` is discrete, so its derivative is unavoidably a unit-step difference — a real limitation at small size; document it.
- Step-size `δE` in energy trades bias (too large) against discreteness noise (too small); scan it.

## Tuning μ in the grand-canonical ensemble

Goal: find `μ*` such that `⟨N⟩(β, μ*) = N_target`.

- `⟨N⟩(μ)` is **monotonically increasing** in `μ` at fixed `T`, so the root is unique → use bisection or Brent's method.
- Bracket: `μ` very negative → `⟨N⟩ → 0`; `μ` very positive → `⟨N⟩ → M`. Start from a wide bracket (e.g. `[E_min - c, E_max + c]`) and shrink.
- Derivative available for Newton steps: `∂⟨N⟩/∂μ = β Var(N) > 0` ([`06`](06-thermodynamic-observables.md)).
- Reuse the shifted weights; recompute `Ξ`, `⟨N⟩` each iteration. Convergence to `|⟨N⟩ - N_target| < tol` is fast.

## Stable variances

`Var(X) = ⟨X²⟩ - ⟨X⟩²` suffers cancellation. Prefer accumulating the mean first then `Σ p_α (X_α - ⟨X⟩)²`, or a compensated sum. Clamp tiny negative results (roundoff) to 0 before taking square roots or forming `C_V`.

## Validation ladder (follow in order)

1. **Structure**: `H` Hermitian; sector dim `= C(M,N)`; `N̂` conserved (no cross-sector elements). [`03`](03-operators-and-matrix-elements.md)
2. **Spectrum, `V=0`, `2×2`**: compare eigenvalues to an independent/analytic result; check expected degeneracies.
3. **Thermodynamic limits**: `T → 0` → energy → ground state, entropy → `ln(ground degeneracy)`; `T → ∞` → `⟨E⟩ → ` spectrum mean, `S → ln(dim)`.
4. **Cross-ensemble**: canonical `⟨E⟩_N(T)` matches microcanonical energy at the `T` from `(∂S/∂E)`; grand-canonical `⟨N⟩(μ*)` matches target `N`.
5. **Scaling**: discrepancies decrease with `L` as expected ([`07`](07-ensemble-equivalence.md)).

## Reproducibility

Record with every dataset: `t`, `V`, `L`, boundary conditions, `β`/`T` grid, `μ` grid or `μ*`, `ΔE`, finite-difference steps, solver and library versions. The modeling choices (`ΔE`, difference scheme) materially affect microcanonical results and must travel with the numbers.
