"""Interactive dashboard over cached spectra (PLAN.md Phase 6.5).

View-only: all physics lives in the qlge modules; this app reads cached spectra
and recomputes only the cheap ensemble post-processing as sliders move. The
expensive diagonalization is never redone in the UI.

Run with:
    streamlit run src/qlge/app.py
(install the optional dependency first: `uv pip install -e ".[app]"`).
"""

from __future__ import annotations

import glob
import os

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

from qlge.diagonalize import Spectrum
from qlge.matching import find_mu, match_ensembles
from qlge.observables import canonical, grand

DATA_DIR = os.environ.get("QLGE_DATA", "data")


@st.cache_data(show_spinner=False)
def list_spectra() -> dict[str, str]:
    """Map a human label -> cache path for every spectrum in DATA_DIR."""
    out = {}
    for path in sorted(glob.glob(os.path.join(DATA_DIR, "spectrum_*.npz"))):
        spec = Spectrum.load(path)
        c = spec.config
        out[f"L={c.L}, V/t={c.V:+g}, {c.bc}"] = path
    return out


@st.cache_data(show_spinner=False)
def load(path: str) -> Spectrum:
    return Spectrum.load(path)


def main() -> None:
    st.set_page_config(page_title="Quantum Lattice Gas — Ensembles", layout="wide")
    st.title("Quantum lattice gas: ensemble explorer")
    st.caption(
        "Hard-core Bose–Hubbard model. Sliders recompute ensembles over cached "
        "spectra; diagonalization is never redone here."
    )

    spectra = list_spectra()
    if not spectra:
        st.error(
            f"No cached spectra in '{DATA_DIR}'. Build them first:\n\n"
            "`python scripts/run_spectra.py`"
        )
        return

    with st.sidebar:
        st.header("Controls")
        label = st.selectbox("Model (cached)", list(spectra))
        spec = load(spectra[label])
        M = spec.config.n_sites
        T = st.slider("Temperature T/t", 0.05, 6.0, 1.0, 0.05)
        beta = 1.0 / T
        N = st.slider("Particle number N", 1, M - 1, M // 2)
        mu = st.slider("Chemical potential μ/t", -8.0, 8.0, 0.0, 0.1)
        st.markdown(f"**M = {M} sites**, dim(N) = {spec.dim(N)}")

    col1, col2 = st.columns(2)

    # --- canonical heat capacity ------------------------------------------
    with col1:
        st.subheader("Canonical C_V(T)")
        Tg = np.linspace(0.05, 6.0, 300)
        res = canonical(spec, N, 1.0 / Tg)
        fig, ax = plt.subplots(figsize=(5, 3.2))
        ax.plot(Tg, res.heat_capacity, color="#d62728")
        ax.axvline(T, color="gray", ls="--", lw=1)
        ax.set_xlabel("T/t"); ax.set_ylabel("C_V"); ax.grid(alpha=0.25)
        st.pyplot(fig)

    # --- grand-canonical filling ------------------------------------------
    with col2:
        st.subheader("Grand-canonical filling ⟨N⟩(μ)")
        mug = np.linspace(-8, 8, 300)
        g = grand(spec, beta, mug)
        fig, ax = plt.subplots(figsize=(5, 3.2))
        ax.plot(mug, g.mean_N / M, color="#1f77b4")
        ax.axvline(mu, color="gray", ls="--", lw=1)
        here = grand(spec, beta, np.array([mu]))
        ax.plot([mu], [here.mean_N[0] / M], "o", color="#d62728")
        ax.set_xlabel("μ/t"); ax.set_ylabel("⟨N⟩/M"); ax.grid(alpha=0.25)
        st.pyplot(fig)
        st.metric("⟨N⟩ at this μ", f"{here.mean_N[0]:.3f}")

    # --- ensemble matching panel ------------------------------------------
    st.subheader("Three-ensemble comparison (matched ⟨N⟩ = N)")
    try:
        r = match_ensembles(spec, N, beta)
        mu_star = find_mu(spec, beta, float(N))
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("canonical ⟨E⟩", f"{r.energy_canonical:.3f}")
        c2.metric("grand ⟨E⟩", f"{r.energy_grand:.3f}", f"Δ/site {r.energy_discrepancy_per_site:.4f}")
        c3.metric("μ* (⟨N⟩=N)", f"{mu_star:+.3f}")
        c4.metric("⟨N⟩ grand", f"{r.mean_N_grand:.4f}")
        d1, d2 = st.columns(2)
        d1.metric("σ_E/|⟨E⟩|  (micro↔can)", f"{r.rel_energy_fluctuation:.4f}")
        d2.metric("σ_N/⟨N⟩  (can↔grand)", f"{r.rel_number_fluctuation:.4f}")
        st.caption(
            "Equivalence improves as these fluctuation ratios shrink with system "
            "size (~1/√M). Microcanonical finite-diff T, μ are omitted here: they "
            "are numerically brittle on small bounded spectra (see the paper)."
        )
    except Exception as e:  # noqa: BLE001 - surface any matching issue in-UI
        st.warning(f"matching unavailable for this selection: {e}")


# Streamlit executes this module top-to-bottom; run the app unconditionally.
main()
