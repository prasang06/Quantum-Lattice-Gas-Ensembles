# 6. Thermodynamic observables

All observables derive from the per-sector spectra `{E_{N,α}}`. Formulas below assume `k_B = 1`, `β = 1/T`.

## Canonical (fixed N, T)

Partition function and Boltzmann weights:

```
Z_N(β) = Σ_α e^{-β E_{N,α}},      p_α = e^{-β E_{N,α}} / Z_N
```

- **Free energy**: `F_N = -T ln Z_N`.
- **Internal energy**: `⟨E⟩ = Σ_α E_α p_α`.
- **Energy variance**: `Var(E) = ⟨E²⟩ - ⟨E⟩² = Σ_α E_α² p_α - (Σ_α E_α p_α)²`.
- **Heat capacity** (from fluctuation–dissipation, avoids numerical differentiation):

  ```
  C_V = ∂⟨E⟩/∂T = Var(E) / T² = β² Var(E)
  ```

- **Canonical entropy**: `S = (⟨E⟩ - F_N)/T = β⟨E⟩ + ln Z_N`, or directly `S = -Σ_α p_α ln p_α`.

## Grand-canonical (fixed T, μ)

Grand weights over all sectors (`p_{N,α} = e^{-β(E_{N,α} - μN)} / Ξ`):

- **Mean number**: `⟨N⟩ = Σ_{N,α} N p_{N,α}`.
- **Number variance**: `Var(N) = ⟨N²⟩ - ⟨N⟩²`.
- **Mean energy**: `⟨E⟩ = Σ_{N,α} E_{N,α} p_{N,α}`.
- **Compressibility / number susceptibility** (fluctuation form):

  ```
  ∂⟨N⟩/∂μ = β Var(N)        (at fixed T)
  κ ∝ Var(N) / ⟨N⟩²          (isothermal compressibility, up to density factors)
  ```

- **Grand potential**: `Φ = -T ln Ξ`, with `Φ = ⟨E⟩ - T S - μ⟨N⟩`.
- **Grand entropy**: `S = -Σ_{N,α} p_{N,α} ln p_{N,α} = β(⟨E⟩ - μ⟨N⟩) + ln Ξ`.

## Microcanonical (fixed N, E window)

From `Ω(E,N;ΔE)` and `S = ln Ω` ([`05`](05-statistical-ensembles.md)):

```
1/T  = (∂S/∂E)_N            # finite difference in E
μ    = -T (∂S/∂N)_E         # finite difference in N
C    = -(∂S/∂E)² / (∂²S/∂E²)   # heat capacity from curvature of S(E)
```

These rely on finite differences of a discrete, window-binned `S`; expect them to be noisier than the canonical fluctuation formulas. Use them as the *reference definitions* of `T` and `μ`, then validate against the smoother canonical/grand-canonical results.

## Why the fluctuation formulas are preferred numerically

`C_V = β² Var(E)` and `∂⟨N⟩/∂μ = β Var(N)` are **exact identities** evaluated from the same Boltzmann sums as the means — no finite differencing of `⟨E⟩(T)` or `⟨N⟩(μ)`, so no step-size error and no cancellation noise. Prefer them over numerically differentiating the means whenever an analytic fluctuation form exists.

## Numerical cautions

- Always subtract the ground-state energy before exponentiating (`E - E_0`) to prevent overflow/underflow ([`08`](08-numerical-methods.md)).
- Variances are differences of large nearly-equal numbers — compute them in a numerically stable way (accumulate weighted means first, or use a shifted/compensated sum) and watch for small negative values from roundoff (clamp to 0).
- Report observables as functions of the control parameters (`T`, `μ`, `V/t`, `L`) with the ensemble and all numerical choices recorded.
