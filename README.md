# Quantum-Lattice-Gas-Ensembles

Codebase for a computational statistical-mechanics project: exact diagonalization
of the **2D hard-core Bose–Hubbard model**, used to test how the microcanonical,
canonical, and grand-canonical ensembles converge as lattice size grows.

## What "quantum lattice gas" means here

In this project, **"quantum lattice gas" = a gas of quantum particles on a
lattice** — a statistical-mechanics *model*. It is realized concretely by the
hard-core Bose–Hubbard Hamiltonian (hopping `t`, nearest-neighbor interaction
`V`, one particle max per site). See `OBJECTIVE.md`.

⚠️ Not to be confused with the **Quantum Lattice Gas Automaton (QLGA)** — an
unrelated *quantum algorithm* (cellular automaton with discrete unitary clock
steps, streaming + collision) used to simulate PDEs like the Dirac equation.
Same name, completely different thing. This repo does **not** do that.

## Layout

- `OBJECTIVE.md` — original project proposal (authoritative physics spec).
- `PLAN.md` — implementation plan, phases, and gates.
- `RESEARCHER.md` — research-mindset operating guide.
- `theory/` — physics derivations (start at `theory/README.md`).
- `src/qlge/` — the package. `CLAUDE.md` lists commands and current status.
