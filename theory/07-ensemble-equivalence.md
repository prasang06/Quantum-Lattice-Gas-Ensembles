# 7. Ensemble equivalence and finite-size effects

## The statement

In the **thermodynamic limit** (`M = L² → ∞` at fixed density `n = N/M`), the microcanonical, canonical, and grand-canonical ensembles predict the **same** intensive quantities (energy density, entropy density, pressure, …). This is ensemble equivalence. The project tests how that equivalence *emerges* at finite size for an interacting quantum lattice gas.

## Why it holds in the limit

- **Canonical vs. microcanonical**: the canonical energy distribution `P(E) ∝ Ω(E) e^{-βE}` is sharply peaked. Its relative width scales as `√Var(E)/⟨E⟩ ~ 1/√M`, because `Var(E) ∝ M` (extensive) while `⟨E⟩ ∝ M`. As `M → ∞` the distribution collapses onto a single energy, so fixing `T` (canonical) is equivalent to fixing `E` (microcanonical). A saddle-point / Laplace argument makes this precise and identifies `β` with `(∂S/∂E)`.
- **Grand-canonical vs. canonical**: the number distribution `P(N) ∝ e^{βμN} Z_N` is likewise peaked with relative width `√Var(N)/⟨N⟩ ~ 1/√M` (`Var(N) ∝ M`). As `M → ∞` fixing `μ` pins `⟨N⟩` to a sharp value, equivalent to fixing `N`.

Equivalence can **fail** even in the limit at first-order phase transitions (phase coexistence, non-concave entropy) and in systems with long-range interactions. The hard-core Bose–Hubbard model with short-range `t, V` is expected to show equivalence in the limit, with interactions shifting *where* and *how fast* it sets in.

## What finite size does

At small `M` the peaks are **broad**, so the three ensembles disagree by O(1/M)-type corrections:

- The discrete spectrum makes the microcanonical `S(E)` jagged and window-dependent.
- Canonical and grand-canonical means differ from the fixed-`N`, fixed-`E` values by amounts controlled by `Var(E)` and `Var(N)`.
- Fluctuations themselves (`C_V`, compressibility) are the leading finite-size signal and the most sensitive observables to compare.

## The measurement protocol

1. For each `L` (e.g. `2×2, 3×3, 4×4`) and each `V/t`, compute an observable three ways from the shared spectrum at matched `(N, T, μ)` ([`05`](05-statistical-ensembles.md)).
2. Define discrepancy metrics, e.g.

   ```
   Δ_EC = |⟨E⟩_canonical - E_microcanonical|
   Δ_N  = |⟨N⟩_grand - N_target|
   ```

   and intensive versions (per site) for cross-`L` comparison.
3. Plot discrepancies vs. `1/M` (or `1/L`); check they trend toward zero and estimate the scaling (expect roughly `~1/M` for means, `~1/√M` for relative fluctuation widths).
4. Compare `V = 0` against `V/t ≠ 0`: quantify how hopping and interactions change the finite-size discrepancies and the approach to equivalence.

## Honest reporting (required by the objective)

Small quantum systems can have **large** finite-size discrepancies, and a microcanonical energy requires an energy window. State explicitly: the window width `ΔE`, the finite-difference scheme, the boundary conditions, the lattice sizes reached, and the resulting uncertainties. The scientific result is the *trend and its quantification*, not a claim that the ensembles are identical at small size.

## Central research question

> How does the equivalence of microcanonical, canonical, and grand-canonical ensembles emerge in an interacting quantum lattice gas as system size increases, and how do quantum hopping and interparticle interactions affect the finite-size discrepancies?
