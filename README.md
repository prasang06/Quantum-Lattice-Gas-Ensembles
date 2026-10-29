# Quantum Lattice Gas: Ensemble Equivalence by Exact Diagonalization

A box of gas can be described three ways — fixed energy (microcanonical), fixed
temperature (canonical), or fixed chemical potential (grand-canonical) — and
statistical mechanics says the three agree once the system is large enough. This
repository tests *how* that agreement sets in for a small, interacting quantum
system, by diagonalizing it exactly and building all three ensembles from the one
spectrum.

The model is the 2D **hard-core Bose–Hubbard model**: bosons that hop between
neighboring sites (amplitude `t`), repel or attract neighbors (energy `V`), with
at most one boson per site. It is realized by cold atoms in an optical lattice in
the strongly interacting limit. Here "quantum lattice gas" means exactly that — a
gas of quantum particles on a lattice — and is unrelated to the quantum
lattice-gas *automaton* that shares the name.

## What we find

Diagonalizing every particle-number sector on square lattices of 4, 9, and 16
sites, and on a family of tilted bipartite clusters of 8 to 20 sites (reached with
translation, point-group, and particle-hole symmetry), we measure equivalence
through fluctuation ratios that fall as `1/√M` when the ensembles converge, at
temperatures from `T/t = 0.2` to `10`:

- **Free and repulsive gases** — the ensembles converge with size. On the tilted
  clusters the relative number fluctuation of the free gas falls as `M^-0.47`
  (R² = 1.000), and at high temperature every coupling gives exactly `M^-0.5`.
- **Attractive gas** — it doesn't. At `V/t = -3` the number fluctuation stops
  shrinking altogether (exponent ≈ 0, `σ_N/⟨N⟩ ≈ 0.96–1.00`) below a
  temperature close to the `T_c ≈ 1.70 t` at which the hopping-free gas, an Ising
  model, phase separates. Mapping the model onto an XXZ ferromagnet explains why
  this needs `V < -2t`: at `V = -2t`, the Heisenberg point, the low-temperature
  fluctuation is exactly `√((M+2)/3M)`, which the spectra reproduce to nine digits.

A side result worth stating: reading temperature off the microcanonical entropy
by finite differences is unreliable on spectra this small and this sharply
bounded, so equivalence is tracked through the fluctuations instead — which is
also what the saddle-point argument says to measure. The full derivation and
results are in [`paper/paper.pdf`](paper/paper.pdf).

## Layout

```
src/qlge/      the package: lattice, basis, hamiltonian, diagonalize,
               ensembles, observables, matching, scaling, benchmarks,
               cluster, symmetry, realspace, plotting, animate, app
scripts/       run_spectra, run_scaling, run_temperature_sweep,
               make_figures, make_animations
tests/         the validation + verification suite
theory/        physics derivations (start at theory/README.md)
paper/         the write-up (paper.tex, paper.pdf)
slides/        presentation deck (Beamer/Metropolis: talk.tex, talk.pdf)
figures/       generated figures
animations/    generated GIFs
```

## Running it

```bash
uv venv --python 3.14 .venv
uv pip install -e ".[dev]"            # add ,app for the dashboard, ,anim for Manim

.venv/bin/python -m pytest -q         # validation + verification suite

.venv/bin/python scripts/run_spectra.py --L 2 3 4 --V -3 -2 -1 0 1 2 3   # build and cache the spectra first
.venv/bin/python scripts/run_scaling.py      # finite-size discrepancy metrics
.venv/bin/python scripts/run_temperature_sweep.py  # the same, across temperature
.venv/bin/python scripts/make_figures.py --V -3 -2 -1 0 1 2 3  # regenerate figures/

# tilted bipartite clusters, M = 8..20 (symmetry-reduced; M=20 takes ~15 min per V)
.venv/bin/python scripts/run_spectra.py --clusters 8 10 16 18 20 --V -3 -2 -1 0 1 2 3
.venv/bin/python scripts/run_temperature_sweep.py --family tilted
.venv/bin/python scripts/make_figures.py --family tilted --V -3 -2 -1 0 1 2 3
.venv/bin/python scripts/make_animations.py  # regenerate animations/
.venv/bin/streamlit run src/qlge/app.py       # interactive dashboard (needs .[app])
```

Spectra are built once and cached in `data/`; everything downstream reads the
cache. Each cached file and figure records the configuration it came from.

## Authors

Prasang Das, Aryan Shakya, Dhruv Thakur.
