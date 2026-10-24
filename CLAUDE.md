# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## How to think here (read first)

`RESEARCHER.md` is the operating mindset for this project: act as an Adaptive Research Engineer — recover context automatically, identify the real problem, question assumptions, verify math before coding, prefer small discriminating tests, validate scientifically (not cosmetically), and keep observed-result / interpretation / hypothesis distinct. Apply it to any substantive reasoning, design, or implementation task in this repo, not just when asked. Correctness and evidence over the appearance of sophistication.

`PLAN.md` is the authoritative build plan (phases, gates, file layout, figure/animation list). `theory/` holds the physics derivations (read `theory/README.md` for the index). `OBJECTIVE.md` is the original proposal.

## Status

Phases 0–6 complete (PLAN.md), including interactive dashboard (6.5). `src/qlge/`: `config, lattice, basis, hamiltonian, diagonalize, ensembles, observables, matching, scaling, plotting, animate, realspace, app`. 61 tests pass. Spectra cached for L∈{2,3,4}×V∈{0,±2} in `data/`. Figures in `figures/`, animations in `animations/`, the write-up in `paper/` (`paper.md`, `paper.tex`, compiled `paper.pdf` — APS-style, authors Prasang Das, Aryan Shakya, Dhruv Thakur). Possible next: full temperature sweep of scaling exponents; density–density correlation / structure-factor imaging of the attractive clustering; symmetry-resolved ED toward L=5.

**Key methodology decision (this project):** microcanonical finite-difference T and μ are numerically brittle on the small bounded discrete spectra reachable by full-spectrum ED (`T→∞` in gaps, sign-flips at the DOS peak) — an inherent small-system limitation, not a bug. So ensemble equivalence is measured primarily through the **well-conditioned fluctuation scalings** (`σ_E/|⟨E⟩|`, `σ_N/⟨N⟩` ~ 1/√M) and the per-site canonical↔grand energy gap. `S=ln Ω` and finite-diff T,μ are kept as an explicitly-noisy secondary diagnostic (theory/07; OBJECTIVE §5 caveats). Verified: all three robust metrics shrink monotonically L=2→3→4.

Docs: `OBJECTIVE.md` (proposal), `PLAN.md` (build plan + gates), `RESEARCHER.md` (mindset), `theory/` (derivations).

## Commands

```bash
uv venv --python 3.14 .venv          # one-time: create virtualenv
uv pip install -e ".[dev]"           # install package + pytest (add ,app ,anim as needed)
.venv/bin/python -m pytest -q        # run the full validation ladder
.venv/bin/python -m pytest tests/test_hamiltonian.py -q          # one test file
.venv/bin/python -m pytest tests/test_hamiltonian.py::test_hermitian   # one test

.venv/bin/python scripts/run_spectra.py      # build + cache per-sector spectra (do this first)
.venv/bin/python scripts/run_scaling.py      # finite-size discrepancy metrics + fits
.venv/bin/python scripts/make_figures.py     # regenerate figures/ from cache
.venv/bin/python scripts/make_animations.py  # regenerate animations/ (GIFs)
.venv/bin/streamlit run src/qlge/app.py       # interactive dashboard (needs .[app])
cd paper && pdflatex paper.tex && pdflatex paper.tex   # compile the paper PDF
```

Each PLAN.md phase has a **gate** encoded as tests — keep them green before advancing. Optional extras: `.[app]` (Streamlit), `.[anim]` (Manim).

## Planned stack (see PLAN.md)

Python 3.11+ with `numpy`/`scipy`/`matplotlib`; `pytest` for the validation ladder; **Manim** for hero animations, matplotlib for routine ones; **Streamlit** for the interactive dashboard (view-only over cached spectra — no model logic in the app). Package under `src/qlge/`, run scripts under `scripts/`, cached spectra in `data/`. Every artifact records its `RunConfig` for reproducibility.

## Project

A computational statistical-mechanics project. Goal: simulate interacting quantum particles on a 2D lattice via **exact diagonalization**, then test whether the microcanonical, canonical, and grand-canonical ensembles describe the same system — and measure how that equivalence emerges as lattice size grows. `OBJECTIVE.md` is the authoritative spec; read it before implementing physics.

## Physics model (the domain that drives all code)

2D hard-core Bose–Hubbard model on a square lattice:

- Hamiltonian: `H = -t Σ_<i,j> (b_i† b_j + b_j† b_i) + V Σ_<i,j> n_i n_j`, sum over nearest-neighbor pairs.
- Hard-core constraint: each site holds 0 or 1 boson (`n_i ∈ {0,1}`, `b_i² = 0`). Local Hilbert space is 2 states/site, so a site maps to a bit.
- `H` conserves total particle number `N` (`[H,N]=0`). Work **per N-sector**: full Hilbert space is `2^(L²)`, each fixed-N sector is `C(L², N)`.
- `V=0` is the non-interacting validation case; `V/t ≠ 0` is the interacting physics of interest.

## Ensembles (all reuse the same per-N eigenvalues)

Build once: for each N, diagonalize `H` restricted to that sector to get eigenvalues `E_{N,α}`. Then:

- **Microcanonical**: count states in an energy window → `Ω(E,N;ΔE)`, entropy `S = k_B ln Ω`. Temperature/chemical potential from finite differences of `S` in E and N. The energy-window width `ΔE` and finite-difference scheme are modeling choices — they must be configurable and documented in output.
- **Canonical**: `Z_N(β) = Σ_α e^{-β E_{N,α}}`, mean energy `⟨E⟩_N = -∂ln Z_N/∂β`.
- **Grand-canonical**: `Ξ(β,μ) = Σ_N e^{βμN} Z_N(β)`, giving `⟨N⟩` and `⟨E⟩`. Tune `μ` so `⟨N⟩` matches the N used in the other two ensembles, then compare observables.

## Implementation sequence (from OBJECTIVE.md §4)

1. Validate on a 2×2 lattice; build `H` per N-sector; assert Hermiticity and particle-number conservation.
2. Exact diagonalization for eigenvalues of each allowed N.
3. Thermodynamic quantities: entropy, energy, heat capacity, particle-number fluctuations.
4. Match ensemble parameters: infer T and μ from microcanonical data, pick canonical/grand-canonical params to match mean quantities.
5. Finite-size study across lattice sizes; quantify ensemble discrepancies rather than assuming equivalence.

Correctness-first ordering matters: validate small (2×2, V=0, Hermiticity + N conservation checks) before scaling L or turning on V. Exact diagonalization cost explodes with L² — start small.
