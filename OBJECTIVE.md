# Quantum lattice gas: project proposal

The idea is to study interacting quantum particles hopping on a 2D lattice, then test how the microcanonical, canonical, and grand-canonical ensembles describe the same physical system.

A good starting point is the 2D hard-core Bose–Hubbard model. It is a simplified quantum lattice gas with a finite local Hilbert space, making exact numerical calculations possible on small lattices.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://www.mdpi.com\&sz=32)

MDPI

+1



## 1. What physical system are we modelling?

[Floquet Prethermalization in a Bose-Hubbard System | Quantum Optics Group](https://images.openai.com/static-rsc-4/84Gd-txWd-cw6yg9V1j9OwzHkL8zSs72GQ-Up2bLMFxpYrlZV_ibImWQr3CyCRT7tautnOLD0Z7kTmxc32C7d-9RYCISyO7OS7m-ZWtib1iRzrIxaBO9ndlF8bu2tLG0Rgpd929YrMtpBjdUY8q9XG9MBeqBT50eGuAiiPSI_ng?purpose=inline)

[quantum-munich.de](https://www.quantum-munich.de/187632/floquet-prethermalization-in-a-bose-hubbard-system?utm_source=chatgpt.com)

Imagine ultracold bosonic atoms trapped in a periodic optical lattice made by intersecting laser beams. Each lattice site can hold zero or one atom in the hard-core limit, and atoms can tunnel between neighboring sites.

The model captures three important effects:

- Hopping: atoms move between neighboring sites.
- Quantum superposition: a particle need not be localized to one definite site.
- Interactions: neighboring particles can attract or repel one another.

The optical-lattice realization is a well-established setting for studying quantum lattice models.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://qft.org\&sz=32)

QFT .org

+1



## 2. The Hamiltonian

For a square lattice, use

\\[ \boxed{ \hat H = -t\sum\_{\langle i,j\rangle} (\hat b_i^\dagger \hat b_j+\hat b_j^\dagger\hat b_i) +V\sum\_{\langle i,j\rangle}\hat n_i\hat n_j } \\]

where:

| Symbol                                  | Meaning                                                             |
| --------------------------------------- | ------------------------------------------------------------------- |
| \\(t\\)                                 | Hopping energy between neighboring sites                            |
| \\(V\\)                                 | Nearest-neighbor interaction energy                                 |
| \\(\hat b_i^\dagger,\hat b_i\\)         | Create a boson at site \\(i\\), subject to the hard-core constraint |
| \\(\hat n_i=\hat b_i^\dagger\hat b_i\\) | Particle-number operator at site \\(i\\)                            |
| \\(\hat N=\sum_i\hat n_i\\)             | Total particle-number operator                                      |

The hard-core constraint is

\\[ \hat n_i\in\\{0,1\\},\qquad \hat b_i^2=(\hat b_i^\dagger)^2=0. \\]

The Hamiltonian conserves total particle number, \\([\hat H,\hat N]=0\\), even though individual particles can move between sites.

We can initially set \\(V=0\\) to validate the ensemble calculations, then introduce \\(V\neq0\\) to study interactions.

## 3. How to construct all three ensembles

The crucial advantage is that we use exactly the same Hamiltonian in every ensemble. Only the constraints and statistical weights change.

## A. Microcanonical ensemble

Fix the total particle number \\(N\\), lattice size, and energy range.

Diagonalize the Hamiltonian in the fixed-\\(N\\) sector to obtain energy eigenvalues \\(E\_{N,\alpha}\\). Count states inside an energy window:

\\[ \Omega(E,N;\Delta E)= \\#\\{\alpha: E\le E\_{N,\alpha}\<E+\Delta E\\}. \\]

Then calculate

\\[ S(E,N)=k_B\ln\Omega(E,N;\Delta E). \\]

From the entropy, estimate temperature and chemical potential using finite differences:

\\[ \frac{1}{T}=\left(\frac{\partial S}{\partial E}\right)\_{N}, \qquad \frac{\mu}{T}=-\left(\frac{\partial S}{\partial N}\right)\_{E}. \\]

Because the spectrum is discrete, the energy-window choice and finite-difference method must be documented.

## B. Canonical ensemble

Fix \\(N\\) and temperature \\(T\\). Using the same fixed-\\(N\\) energy eigenvalues,

\\[ Z_N(\beta)=\sum\_\alpha e^{-\beta E\_{N,\alpha}}, \qquad \beta=\frac{1}{k_BT}. \\]

Calculate the mean energy:

\\[ \langle E\rangle_N=-\frac{\partial\ln Z_N}{\partial\beta}. \\]

Compare it with the microcanonical energy at the temperature inferred from the microcanonical entropy.

## C. Grand-canonical ensemble

Fix temperature \\(T\\) and chemical potential \\(\mu\\), allowing \\(N\\) to fluctuate.

\\[ \Xi(\beta,\mu)= \sum_N e^{\beta\mu N}Z_N(\beta). \\]

Calculate the mean particle number and mean energy:

\\[ \langle N\rangle= \frac{1}{\beta}\frac{\partial\ln\Xi}{\partial\mu}, \qquad \langle E\rangle= -\frac{\partial\ln\Xi}{\partial\beta} +\mu\langle N\rangle. \\]

Tune \\(\mu\\) so that \\(\langle N\rangle\\) matches the particle number used in the microcanonical and canonical calculations. Then compare the observables.

## 4. What will the actual computational project involve?

I'd structure it as a sequence of increasingly difficult tests.

1. Validate the code on a tiny lattice. Start with a \\(2\times2\\) square lattice and construct the Hamiltonian in each particle-number sector. Check that the Hamiltonian is Hermitian and particle number is conserved.
2. Compute exact energy spectra. Use numerical diagonalization to obtain the eigenvalues for each allowed \\(N\\). The hard-core constraint gives a Hilbert-space dimension of \\(2^{L^2}\\), with fixed-\\(N\\) sector dimension \\(\binom{L^2}{N}\\).
3. Calculate thermodynamic quantities. Obtain entropy, energy, heat capacity, and particle-number fluctuations in the relevant ensembles.
4. Match ensemble parameters. Infer \\(T\\) and \\(\mu\\) from the microcanonical data, then choose canonical and grand-canonical parameters that match the corresponding mean quantities.
5. Study finite-size effects. Compare several lattice sizes where feasible. Quantify differences between the ensemble predictions rather than assuming they are equal.

For larger systems, exact diagonalization becomes expensive, so start small and only scale up after validating the implementation. Exact diagonalization is a standard benchmark method for small Bose–Hubbard systems.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://alps.comp-phys.org\&sz=32)

ALPS Software Package

+1



## 5. What is the central research question?

I would formulate it as:

> How does the equivalence of microcanonical, canonical, and grand-canonical ensembles emerge in an interacting quantum lattice gas as system size increases, and how do quantum hopping and interparticle interactions affect the finite-size discrepancies?

That is stronger than simply calculating three partition functions. It gives you measurable comparisons, a controlled computational experiment, and a reason to vary the model parameters.

One important limitation: small quantum systems can have large finite-size discrepancies, and an exact microcanonical energy generally requires an energy window. You should report these choices and uncertainties explicitly.

My recommendation: start with the noninteracting hard-core model (\\(V=0\\)) as a validation case, then study \\(V/t\neq0\\). This keeps the project focused on ensemble equivalence while adding genuine interacting quantum physics in the main results.