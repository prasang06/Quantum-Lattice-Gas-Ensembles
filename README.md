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
sites, we measure equivalence through fluctuation ratios that fall as `1/√M` when
the ensembles converge:

- **Free and repulsive gases** — the ensembles converge with size; the relative
  number fluctuation and per-site energy gap follow clean power laws near the
  expected `M^(-1/2)`.
- **Attractive gas** — they don't. The number fluctuation stays large, and for
  `V/t = -3` its finite-size exponent is *positive*: the canonical-to-grand
  mismatch grows with the lattice. That is the finite-size shadow of phase
  separation, and it lives specifically in the particle-number channel.

A side result worth stating: reading temperature off the microcanonical entropy
by finite differences is unreliable on spectra this small and this sharply
bounded, so equivalence is tracked through the fluctuations instead — which is
also what the saddle-point argument says to measure. The full derivation and
results are in [`paper/paper.pdf`](paper/paper.pdf).

## Layout

```
src/qlge/      the package: lattice, basis, hamiltonian, diagonalize,
               ensembles, observables, matching, scaling, realspace,
               plotting, animate, app
scripts/       run_spectra, run_scaling, make_figures, make_animations, run_app
tests/         the validation + verification suite
theory/        physics derivations (start at theory/README.md)
paper/         the write-up (paper.tex, paper.pdf)
figures/       generated figures
animations/    generated GIFs
```

## Running it

```bash
uv venv --python 3.14 .venv
uv pip install -e ".[dev]"            # add ,app for the dashboard, ,anim for Manim

.venv/bin/python -m pytest -q         # validation + verification suite

.venv/bin/python scripts/run_spectra.py     # build and cache the spectra first
.venv/bin/python scripts/run_scaling.py      # finite-size discrepancy metrics
.venv/bin/python scripts/make_figures.py     # regenerate figures/
.venv/bin/python scripts/make_animations.py  # regenerate animations/
.venv/bin/streamlit run src/qlge/app.py       # interactive dashboard (needs .[app])
```

Spectra are built once and cached in `data/`; everything downstream reads the
cache. Each cached file and figure records the configuration it came from.

## Authors

Prasang Das, Aryan Shakya, Dhruv Thakur.
