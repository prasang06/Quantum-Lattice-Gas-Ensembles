# Implementation Plan — Quantum Lattice Gas Ensembles

Full research study: exact diagonalization of the 2D hard-core Bose–Hubbard model, three-ensemble comparison, finite-size scaling, with a complete plot + animation suite. This document is the authoritative build plan. See `theory/` for the physics and `OBJECTIVE.md` for the proposal.

## Research framing (read `RESEARCHER.md` before acting)

- **Research objective:** How does equivalence of the microcanonical, canonical, and grand-canonical ensembles emerge in an interacting quantum lattice gas as system size grows, and how do hopping `t` and interaction `V` affect finite-size discrepancies?
- **Success criteria:** (1) validated-correct ED on small lattices; (2) the three ensembles reproduce matched observables within quantified error; (3) discrepancy metrics decrease with `L` on a documented scaling trend; (4) a reproducible figure/animation set that tells the emergence story for `V=0` and `V/t≠0`.
- **Non-goals:** large-`L` frontier ED, momentum-sector optimization beyond what `L≤4` needs, hardware/quantum-circuit simulation. Correctness-first, scale later.
- **Discipline:** every quantitative claim must be backed by a test, an analytic check, or a cited limit. Record config with every artifact. Keep observed-result vs interpretation vs hypothesis distinct in the write-up.

## Tech stack

- Python 3.11+, `numpy`, `scipy` (`sparse`, `linalg.eigh`), `matplotlib` (static + `FuncAnimation`).
- **Manim** (`manim` CE) for the polished "hero" animations where it materially improves clarity (equivalence emergence, μ-tuning). Matplotlib for routine/scientific animations and all static figures. Don't Manim-ify what a quick matplotlib gif does fine.
- Data cached as `.npz` (or HDF5 if it grows); config as dataclass serialized to YAML/JSON alongside outputs.
- **Streamlit** for the interactive dashboard (Phase 6.5) — sliders over cached spectra, view-only layer, no model logic in the app.
- `pytest` for tests. `pyproject.toml` + `uv`/`pip`. Final narrative in a Jupyter notebook under `notebooks/`.

## Repository layout

```
src/qlge/
  config.py        # RunConfig dataclass: t, V, L, BC, N_list, beta_grid, mu_grid, dE, seeds; (de)serialize
  lattice.py       # site indexing (i = x + L*y), nearest-neighbor bond list, OBC/PBC
  basis.py         # bit encoding, N-sector enumeration, state->index map, popcount helpers
  hamiltonian.py   # assemble sparse H per N-sector (hopping + interaction) from matrix elements
  diagonalize.py   # full spectrum per sector via eigh; cache {E_{N,alpha}} (+ optional vectors) to disk
  ensembles.py     # microcanonical Omega/S; canonical Z_N; grand Xi (log-sum-exp safe)
  observables.py   # E, S, C_V (fluctuation), Var(N), compressibility; stable variance
  matching.py      # infer T,mu from microcanonical finite-diffs; bisection for mu s.t. <N>=N_target
  scaling.py       # discrepancy metrics across L; fits vs 1/M
  plotting.py      # static matplotlib figures
  animate.py       # matplotlib FuncAnimation scenes
  manim_scenes.py  # Manim Scene classes for hero animations
  app.py           # Streamlit interactive dashboard over cached spectra
scripts/
  run_spectra.py      # build + diagonalize + cache, per config
  run_ensembles.py    # ensembles + observables from cached spectra
  run_matching.py     # cross-ensemble matching experiment
  run_scaling.py      # sweep L, V; produce discrepancy data
  make_figures.py     # regenerate all static figures
  make_animations.py  # regenerate all animations
  run_app.py          # launch Streamlit dashboard (streamlit run src/qlge/app.py)
tests/                # see validation ladder
notebooks/            # final research write-up
data/  figures/  animations/   # generated artifacts (gitignore large ones)
```

Design rules: pure functions over state where possible; model/numerics/plotting separated; deterministic given a config; no premature OO or frameworks (per `RESEARCHER.md` §7, §7.2 engineering discipline).

## Phases

Each phase has an explicit **gate** — do not advance until it passes.

### Phase 0 — Scaffold
- `pyproject.toml`, package skeleton, `pytest` wired, `.gitignore` for `data/ figures/ animations/` large outputs.
- `RunConfig` dataclass + (de)serialization.
- **Gate:** `pytest` runs (even if trivial); `import qlge` works.

### Phase 1 — Model + validation (correctness-first core)
- `lattice.py`: bond lists for OBC and PBC; verify bond counts (OBC `2L(L-1)`, PBC `2L²`).
- `basis.py`: N-sector enumeration, index map.
- `hamiltonian.py`: assemble sparse `H` per N-sector (hopping `-t`, interaction `V`, no inter-site sign — hard-core boson convention, `theory/03`).
- **Gate (validation ladder, `theory/08`):**
  - `H` Hermitian/real-symmetric to machine precision.
  - sector dim `== C(M,N)`; no cross-sector matrix elements (N conserved).
  - `V=0`, `2×2`: eigenvalues match an independent hand/analytic calculation.
  - `Tr H == V · Σ occupied-bond counts`.

### Phase 2 — Diagonalization + caching
- Full spectra per N-sector (`eigh`), shift by `E_0`, store with config metadata.
- Feasible `L=2,3,4`; half-filling sector sets the cost ceiling (`C(16,8)=12870` for `L=4`).
- **Gate:** reload-from-cache reproduces spectra bit-for-bit; `L=3` full run completes fast; `L=4` completes within a documented time/memory budget.

### Phase 3 — Ensembles + observables
- Canonical `Z_N`, grand `Ξ` with log-sum-exp / ground-state shift (overflow-safety is the #1 bug source, `theory/08`).
- Microcanonical `Ω(E,N;ΔE)`, `S=ln Ω`; configurable `ΔE`, optional Gaussian broadening.
- Observables: `⟨E⟩`, `S`, `C_V=β²Var(E)`, `Var(N)`, compressibility `∝Var(N)`; numerically stable variances.
- **Gate (thermodynamic limits):** `T→0` → energy→ground state, `S→ln(ground degeneracy)`; `T→∞` → `⟨E⟩→` spectrum mean, `S→ln(dim)`. `ΔE`-sensitivity of microcanonical `T,μ` reported.

### Phase 4 — Ensemble matching (the core experiment)
- From microcanonical `S(E,N)`: `1/T=(∂S/∂E)_N`, `μ/T=-(∂S/∂N)_E` via central finite differences.
- Canonical `⟨E⟩_N(T)` at that `T` vs microcanonical energy.
- Grand-canonical: bisection on `μ` (monotone `⟨N⟩(μ)`, Newton option via `∂⟨N⟩/∂μ=βVar(N)`) so `⟨N⟩=N_target`; then compare `⟨E⟩` and other observables three ways.
- **Gate:** at a chosen `(L,N,V)` the three ensembles agree within an error that is (a) quantified and (b) shrinks when `L` increases.

### Phase 5 — Finite-size + interaction study
- Sweep `L∈{2,3,4}`, `V/t∈{0, +, −}` (e.g. `0, +2, −2` plus a finer scan near interesting `V`).
- Discrepancy metrics (`theory/07`): `Δ_EC=|⟨E⟩_can−E_micro|`, `Δ_N=|⟨N⟩_grand−N_target|`, intensive per-site versions.
- Plot vs `1/M`; fit scaling; compare `V=0` vs interacting.
- **Gate:** monotone (or explained) decrease of intensive discrepancies with `L`; scaling exponents reported with uncertainty; anomalies diagnosed, not hidden.

### Phase 6 — Figures, animations, write-up
- Regenerable static figures + animations from cached data via `make_figures.py` / `make_animations.py`.
- Notebook: current understanding → assessment → results → validation → remaining uncertainty (`RESEARCHER.md` §9 output contract).
- **Gate:** a fresh checkout reproduces every figure and the headline animation from `data/` + scripts.

### Phase 6.5 — Interactive dashboard (Streamlit)
- `app.py`: Streamlit app reading **cached spectra** from `data/`. The expensive step (diagonalization) is never redone in the UI — sliders only re-run the cheap ensemble/observable post-processing.
- Controls: `T`/`β`, `μ`, `ΔE` window, `V/t`, `L`, target `N`.
- Live panels: `C_V(T)`, `⟨N⟩(μ)` staircase with `μ*` marker, microcanonical `S(E)`, ensemble `⟨E⟩` overlay (micro/canonical/grand), real-space ground-state density.
- Precompute a `(V,L)` grid of spectra via `run_spectra.py`; the app selects from cache. An uncached `(V,L)` either triggers a one-off diagonalization with a spinner or is disabled — decide by `L` cost (`L=4` is slow; gate it behind an explicit button).
- Cache hot post-processing with `@st.cache_data`; keep all physics in `qlge` modules — `app.py` is view-only, no model logic.
- **Gate:** `streamlit run` launches; dragging `L` visibly tightens the ensemble overlay; no recomputation of cached spectra; app runs from a fresh checkout given a populated `data/`.

## Figures (static)

1. Energy spectrum / density of states per N-sector.
2. Microcanonical entropy `S(E)`; caloric curve `T(E)`.
3. Heat capacity `C_V(T)` — Schottky-like peak; `V=0` vs interacting.
4. `⟨N⟩(μ)` staircase — sharp steps at small `L`, smoothing with `L`.
5. `Var(N)` and compressibility vs `μ`.
6. **Ensemble overlay:** `⟨E⟩` micro vs canonical vs grand at matched params.
7. **Finite-size scaling:** discrepancy vs `1/M` with fit.
8. Interaction effect: observables vs `V/t`; ground-state nn-correlation vs `V/t`.

## Animations (the emergence story)

1. **Ensemble equivalence emerging** (hero, Manim): `P(E)` (canonical) and `P(N)` (grand) distributions narrowing as `L:2→3→4`; annotate `~1/√M` collapse. Headline deliverable.
2. **Boltzmann weights vs T** (matplotlib): sweep `β`, occupation of the spectrum shifts cold→hot.
3. **μ-tuning** (Manim or matplotlib): `⟨N⟩(μ)` sharpening into a step as `L` grows; show bisection landing on `μ*`.
4. **Interaction sweep** (matplotlib): ground-state real-space density / nn-correlations as `V/t` ramps — ordering onset.
5. **Discrepancy decay** (matplotlib): ensemble gap shrinking frame-by-frame over `L`.

## Validation ladder (gates condensed, `theory/08` §Validation)

1. Structure: Hermiticity, sector dims, N-conservation.
2. Spectrum: `V=0` `2×2` vs independent calc; expected degeneracies.
3. Thermo limits: `T→0`, `T→∞` behavior of `⟨E⟩`, `S`.
4. Cross-ensemble: canonical vs microcanonical energy; grand `⟨N⟩(μ*)` matches target.
5. Scaling: discrepancies shrink with `L` as expected.

## Reproducibility

Every dataset/figure carries: `t, V, L, BC, β/T grid, μ grid or μ*, ΔE, finite-diff steps, solver + library versions`. Modeling choices (`ΔE`, difference scheme) materially change microcanonical results and must travel with the numbers.

## Risks / open decisions

- `L=4` full-spectrum memory/time — budget it in Phase 2; if eigenvectors (for real-space density) blow memory, compute only the needed states or use symmetry reduction.
- Microcanonical discreteness at small `L` — report `ΔE` sensitivity; this is a genuine physical limitation, state it, don't paper over it.
- Manim build/render toolchain weight — introduce only at Phase 6; keep matplotlib fallback for every animation so the study is complete without Manim if needed.
