# SBQOS Prototype — Design Document Set: Overview

**Project:** Closure-Certified Logical Qubit — simulation prototype ("SBQOS", Six Birds Quantum OS)
**Parent document:** the original motivation document (`INVENTION.md`, removed 2026-09-05 when the project became paper-only). *Note (2026-09-05): this project is paper-only; references below to that document are historical.*
**Status:** design frozen for implementation hand-off. The implementing agent must not deviate from these documents without recording a deviation note in `design/DEVIATIONS.md` (create it on first deviation; one dated entry per deviation, with reason).

---

## 1. Mission

Build a fully deterministic, simulation-only prototype that demonstrates, with registered predictions and controls, the five audit mechanisms of the Closure-Certified Logical Qubit:

| ID | Mechanism | Experiment | Novelty status (original motivation document §8, historical) |
|----|-----------|-----------|----------------------------------|
| M1 | Coverage audit: adequacy residual Ξ, blind-spot witness, chain-rule check selection | E1, E2, E3 | Appears novel — **headline** |
| M2 | Existence audit: idempotence defect δ, retention error ε, closure deficit CD_τ, route mismatch RM | E4 | Partial overlap; certificate construct novel |
| M3 | Memory audit: predictive quotient, decoder-memory witness, minimal decoder machine | E5 | Appears novel — **headline** |
| M4 | Price audit: budgeted check selection, dual variables, slack certificate | E6 | Partial overlap; slack certificate novel |
| M5 | Transport audit: certified deformation bridges (Lean) | — | **Deferred to phase 2.** Hooks only (see 02_ARCHITECTURE §9). Do not implement. |

The prototype serves three purposes simultaneously: (a) proof of concept, (b) evidence for the mechanism-to-experiment map in `REPORT.md` §6, (c) the experimental section of a paper. Therefore every experiment must produce **frozen, hash-manifested, reproducible artifacts** (see 02_ARCHITECTURE §8) in the house style of the SBT corpus (deterministic seeding, frozen configs, exact rational arithmetic where specified, claim-grade labels).

## 2. What we are NOT building (standing nonclaims)

These are binding. Repeat them in the final report verbatim.

1. **No quantum hardware access.** Everything is classical simulation of stochastic Pauli / classical Markov models (plus Stim sampling).
2. **No claim that Ξ > 0 implies no decoder exists.** The prototype's Ξ is computed over a declared feature family (degree-1 ±1 syndrome observables, optionally degree-2); Ξ = 0 certifies coverage *by the linear estimator class over that family*; Ξ > 0 certifies a coverage gap *for that class* (see 01_MATH_SPEC §4.6). This scope fence comes from the Xi paper's own discipline (`six-birds-papers/Tsiokos_2026_Adequacy_Residuals_and_Blind_Spot_Currency.tex`, scope fences: "no generic exact adequacy").
3. **No Born-rule, no Bell, no coherent-dynamics claims.** All noise models are stochastic Pauli (a standard, declared restriction). The SBT quantum paper itself works at exactly this packaging level (`six-birds-papers/Tsiokos_2026_A_Six_Birds_Eye_View_of_Quantum_Theory_...tex`, §Discussion "Limitations").
4. **No asymptotic threshold theorem claims.** All results are finite-carrier, per the corpus's "diagnosis grade" discipline.
5. **No fitted proxies as evidence.** Fitted macro models are diagnostic only; theorem-grade quantities are computed exactly on declared finite models (cf. `Tsiokos_2026_Six_Birds_No_Go_Theorems_for_Audited_Emergence.tex`, scope remarks on "proxy" objects).

## 3. Document map

| Doc | Contents | Read before |
|-----|----------|-------------|
| `00_OVERVIEW.md` | this file | everything |
| `01_MATH_SPEC.md` | every mathematical object, exact formulas, citations, notation table | writing any code |
| `02_ARCHITECTURE.md` | package layout, module interfaces, data structures, artifact system, dependencies | writing any code |
| `03_EXPERIMENTS.md` | experiments E1–E6: procedures, registered predictions, pass/fail, plots | implementing `experiments/` |
| `04_CONTROLS_AND_CLAIMS.md` | the null battery (controls), claim-grade vocabulary, acceptance checklist | writing the report |
| `05_IMPLEMENTATION_PLAN.md` | ordered task list with per-task acceptance tests and pitfalls | starting work |

## 4. Ground rules for the implementing agent

1. **Determinism is absolute.** Every run takes `--seed` and `--config`; identical inputs must produce byte-identical result JSONs (floats serialized via `repr` at full precision). No wall-clock, no unseeded RNG, no dict-ordering dependence (sort all keys).
2. **Exact rational arithmetic where specified.** Modules marked EXACT in 02_ARCHITECTURE use `fractions.Fraction` end to end. No floats may enter those code paths. This mirrors the corpus's exact-finite evidence discipline (e.g., `Tsiokos_2026_Marking_Erasure_and_Recombination_on_Fixed_Support_...tex`).
3. **Cite in code.** Every function implementing a paper formula carries a docstring line `Ref: <paper file> :: <concept name>` copied from 01_MATH_SPEC.
4. **Tests before experiments.** Each module ships unit tests with hand-computable expected values (given in 05_IMPLEMENTATION_PLAN). Experiments only run after `pytest` is green.
5. **Registered predictions are frozen.** The predictions in 03_EXPERIMENTS are written down *before* implementation. If an experiment fails a prediction, the failure is a first-class reportable result (house norm — the Institutions paper published reversed hypotheses); do not tune parameters to force a pass. Record it in the report under "Negative results."
6. **No scope creep.** If a mechanism is not in these documents, do not build it.

## 5. Deliverables

1. `src/sbqos/` — the package (02_ARCHITECTURE).
2. `tests/` — green pytest suite.
3. `artifacts/` — frozen results: one directory per experiment, containing `config.json`, `results.json`, `manifest.json` (SHA-256 of every file), figures as PNG + the exact data behind each figure as CSV.
4. `REPORT.md` — results write-up per 04_CONTROLS_AND_CLAIMS §4 template, with claim-grade labels on every claim.
5. `design/DEVIATIONS.md` — only if deviations occurred.

## 6. Glossary (SBT term ↔ QC term ↔ code name)

| SBT term (paper) | QC meaning here | Code identifier |
|---|---|---|
| Carrier Z / substrate | error space of a code under a noise model | `ErrorSpace` |
| Lens f | syndrome map / decoder coarse-graining | `Lens` |
| Packaging endomap E_{τ,f} = U_f∘Q_f∘P^τ (Foundations I) | QEC cycle: noise τ, syndrome extraction, recovery | `CycleOperator` |
| Prototype u_x | canonical coset representative distribution used by recovery | `prototypes` |
| Idempotence defect δ | logical-layer stability defect of the cycle | `idem_defect` |
| Retention error ε | prob. of leaving the correctable coset in τ steps | `retention_error` |
| Closure deficit CD_τ (Foundations III Thm 8; Cast-a-Stone) | non-Markovianity of the logical/syndrome description | `closure_deficit` |
| Route mismatch RM (XOR paper) | evolve-then-decode vs decode-then-evolve disagreement | `route_mismatch` |
| Native probes L | scheduled syndrome checks (as ±1 observables) | `ProbeFamily` (`role="native"`) |
| Dissolving probes D | logical action observables (as ±1 observables) | `ProbeFamily` (`role="logical"`) |
| Audit energy C / noise-weighted metric | noise model second-moment structure | implicit in `MomentEngine` |
| Adequacy residual Ξ_C(D\|L) (Xi paper) | logical covariance unexplained by scheduled checks | `xi_residual` |
| Blind-spot witness z (Xi paper) | worst uncovered logical direction | `blind_spot_witness` |
| Chain rule / discharge (Xi paper) | exact marginal value of a candidate added check | `discharge` |
| Same-family saturation (Xi paper) | provable redundancy of a duplicated/linear check | `saturation_test` |
| Current quotient Q, predictive quotient M, witness (Holonomy paper) | syndrome-visible classes vs future-logical classes; decoder-memory certificate | `QuotientPair`, `predictive_witnesses` |
| Currentization (Holonomy paper) | added checks that expose hidden decoder memory | `currentization_search` |
| Protocol trap (Protocol-Trap paper; Foundations I T-AOT-02) | scheduling artifact masquerading as memory/drive | `protocol_trap_control` |
| Shadow price λ, slack collapse (Spend paper) | dual value of a resource budget; λ=0 ⇒ over-provisioned | `shadow_price`, `slack_certificate` |
