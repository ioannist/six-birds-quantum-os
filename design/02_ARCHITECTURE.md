# 02 — Architecture and Interfaces

Normative for package layout, data structures, and module contracts. Formulas live in `01_MATH_SPEC.md` (cited here by section, e.g. "MS §3.1").

---

## 1. Ground decisions

- **Language:** Python ≥ 3.10 (this machine has 3.10.12 only, no 3.11+ interpreter available; nothing in this spec requires 3.11-only syntax, so the floor is set to match the actual toolchain rather than carrying an unmet requirement). **Dependencies (exhaustive):** `numpy`, `scipy`, `stim`, `pymatching`, `matplotlib`, `pytest`. Standard library `fractions.Fraction` for EXACT paths. **No other dependencies.** No sympy (Fraction suffices), no pandas (write CSVs with `csv`), no jupyter.
- **Clean-room rule:** the other Six Birds repositories (e.g. `six-birds-quantum`, `six-birds-carrier`, `six-birds-currency`, `six-birds-logic`) contain the papers' reference code. They may be **consulted read-only** to cross-check expected values when writing unit tests (e.g., the Markov packaging defect in `six-birds-quantum`, the exact-rational quotient machinery in `six-birds-carrier`). **Never import from them, never copy code from them, never add them to `sys.path`.** This prototype is a from-scratch, purpose-built implementation; provenance cleanliness matters for the paper's clean-room claim.
- **EXACT vs FLOAT paths:** modules marked EXACT accept a flag `exact: bool`. When `exact=True`, all arithmetic is `Fraction`; when `False`, `float64`. E1/E5 headline numbers use EXACT; E2/E3/E4/E6 may use FLOAT except where MS says otherwise. Never mix types inside one computation.
- **Determinism:** single global entry `sbqos.rng(seed)` returning `numpy.random.Generator(numpy.random.PCG64(seed))`; every stochastic function takes an explicit `rng` argument. Stim samplers are seeded from the same config seed. Sort every dict before JSON dump (`sort_keys=True`); serialize floats with `repr`.

## 2. Repository layout

```
six-birds-quantum-os/
  design/                  # these documents (frozen)
  src/sbqos/
    __init__.py
    linalg2.py             # F2 linear algebra: rank, solve, row-reduce (uint8 matrices)
    codes.py               # Code dataclass; REP(d), SURF(3), SURF(5) constructors
    noise.py               # NoiseModel dataclass; N1..N5 constructors; sampling
    moments.py             # MomentEngine (EXACT-capable)          MS §2
    xi.py                  # xi_residual, witness, discharge, greedy   MS §3
    streams.py             # stim circuits, samplers, empirical covariances, W1/W2   MS §3.5
    markov.py              # explicit-state Markov models of QEC rounds   MS §4.1
    closure.py             # CycleOperator, δ, ε, RM, CD_τ, Δ_pred, ExistenceCertificate   MS §4
    quotients.py           # exact predictive-quotient engine (EXACT only)   MS §5
    prices.py              # V(b), shadow prices, slack point, proxy null   MS §6
    artifacts.py           # config loading, result writing, manifest hashing
    experiments/
      __init__.py
      common.py            # shared runners, plotting helpers
      e1_coverage.py
      e2_drift_witness.py
      e3_check_selection.py
      e4_existence.py
      e5_decoder_memory.py
      e6_slack.py
    configs/               # frozen JSON configs, one per experiment run
  tests/
    test_linalg2.py  test_codes.py  test_moments.py  test_xi.py
    test_markov.py   test_closure.py  test_quotients.py  test_prices.py
    test_artifacts.py
  artifacts/               # generated output (gitignored except manifests)
  REPORT.md                # written last, per 04_CONTROLS_AND_CLAIMS §4
```

## 3. Core data structures (dataclasses; all frozen/immutable)

```python
@dataclass(frozen=True)
class Code:
    name: str                 # "REP3" | "REP5" | "SURF3" | "SURF5"
    n: int                    # data qubits
    k: int                    # logical qubits
    checks: tuple[PauliVec]   # stabilizer generators, symplectic (2n,) uint8 vectors
    logicals: tuple[PauliVec] # 2k logical representatives, order [X̄1, Z̄1, ...]
    meta: dict                # layout info (row/col supports for SURF), for figures

@dataclass(frozen=True)
class NoiseModel:
    name: str                          # "N1".."N5"
    per_qubit: tuple[QubitDist]        # each QubitDist = (pI, pX, pY, pZ) as Fractions
    injection: Optional[Injection]     # N3: (prob q, PauliVec zz) | None
    hidden: Optional[HiddenSpec]       # N4: (switch_prob s, mode_models) ; N5: (latch_prob r, qubit ℓ) | None

@dataclass(frozen=True)
class ProbeFamily:
    role: str                 # "native" | "logical" | "candidate"
    vecs: tuple[PauliVec]
    labels: tuple[str]        # e.g. ("Zcheck_0_1", ...) / ("LX", "LZ")

@dataclass(frozen=True)
class CovBlocks:              # produced by MomentEngine; all same dtype (Fraction or float)
    K_LL: Matrix; K_DL: Matrix; K_DD: Matrix
    labels_L: tuple[str]; labels_D: tuple[str]
```

`PauliVec` is `np.ndarray` dtype uint8 shape (2n,), layout `[x_1..x_n | z_1..z_n]`. `sympl(a,e) = (a[:n]@e[n:] + a[n:]@e[:n]) % 2`.

## 4. Module contracts

Each bullet is a public function the tests call. Anything else is private. Docstrings carry `Ref:` lines per 00_OVERVIEW §4.3.

### 4.1 `linalg2.py`
- `rank_f2(M) -> int`; `row_reduce_f2(M) -> (R, pivots)`; `in_span_f2(M, v) -> bool`. Pure F_2 (uint8, mod-2). Needed for: duplicated-check detection, bounded-weight sanity tests, SURF coset bookkeeping.

### 4.2 `codes.py`
- `rep_code(d) -> Code`, `surface_code(d) -> Code` (d ∈ {3,5}; check supports hard-coded literal lists with a comment diagram).
- `syndrome(code, e) -> np.ndarray`; `logical_flips(code, e) -> np.ndarray` (both via `sympl`).
- `canonical_rep(code, s) -> PauliVec`: minimum-weight error for syndrome s (precomputed lookup by BFS over weight; cache per code). For SURF(5) allow `pymatching`-based representative with a note that canonicality choice is declared, not unique (MS §4.1 prototype remark).

### 4.3 `noise.py`
- `n1(p, n) / n2(p, n) / n3(p, q, n, pair) / n4(p0, s, n) / n5(p, r, n, leak_qubit) -> NoiseModel` (probabilities passed as `Fraction` strings in configs, e.g. `"1/20"`).
- `sample_error(model, rng, mode_state=None) -> (PauliVec, new_mode_state)`.

### 4.4 `moments.py` (EXACT-capable) — MS §2
- `MomentEngine(model, exact: bool)` with:
  - `.mean(a: PauliVec)` — closed-form product MS §2.2, including N3 conditioning branch; for N4/N5 the engine takes a **mode-conditioned** submodel (`engine_for_mode(m)`) — moments of hidden-mode models are only defined per mode; the drift experiments use mode-0 as the declared model.
  - `.cov(a, b)`; `.cov_blocks(L: ProbeFamily, D: ProbeFamily) -> CovBlocks`; `.extend_blocks(blocks, M: ProbeFamily) -> CovBlocksExt` (adds K_MM, K_DM, K_ML).
- `degree2_family(L) -> ProbeFamily` (all pairwise XORs, labels `"h_i^h_j"`) — MS §2.4.

### 4.5 `xi.py` — MS §3
- `xi_residual(blocks) -> (Xi, A_star)`; `psd_check(Xi, tol)`.
- `blind_spot_witness(Xi, Omega) -> Witness(lam_max, z, labels)`.
- `discharge(blocks_ext, M_indices) -> (D_matrix, value)`; `chain_rule_check(blocks, M) -> residual_diff_norm` (test helper).
- `greedy_select(engine, L0, D, candidates, costs, budget, tol_stop) -> SelectionLog` (ranked lists per round; MS §3.4).

### 4.6 `streams.py` — MS §3.5
- `build_stim_circuit(code, model, rounds) -> stim.Circuit` (code-capacity: single round of iid Pauli errors then perfect measurement of all checks; for N3 add the correlated ZZ with prob q via `CORRELATED_ERROR`; N4/N5 are sampled by our own loop calling `sample_error`, not Stim, since Stim has no hidden-mode state — document this in the module docstring).
- `sample_shots(..., N, rng) -> ShotTable` (columns: syndrome bits ±1, logical flips ±1 [oracle], mode [oracle]).
- `empirical_blocks(shots, L, D) -> CovBlocks`; `w1_witness(shots, model_blocks, Omega_stat)`; `w2_witness(shots, model_blocks, A_star, Omega_stat)`; `omega_stat(model, L, D, N, B, rng, quantile=0.99)` — MS §3.5.

### 4.7 `markov.py` — MS §4.1
- `qec_markov_model(code, model, decoder) -> MarkovModel` with `MarkovModel = (states: list[StateLabel], P: Matrix, lens_syndrome: array, lens_decoded: array, lens_mode_hidden: bool)`. EXACT: P entries are `Fraction`. Size guard: raise if |states| > 20000. REP(3): 8 states (·2 with mode). SURF(3): 256 syndromes × 4 logical classes = 1024 (·2 with mode). REP/SURF state update: coset ⊕ fresh error; recovery composes with `canonical_rep`.
- `stationary(P) -> pi` (float; exactness not required, verify residual ≤ 1e−12).

### 4.8 `closure.py` — MS §4.2–4.5
- `CycleOperator(mm: MarkovModel, lens, prototypes, tau, exact)` with `.apply(mu)`, `.idem_defect()`, `.retention_error()`, `.prototype_stability()` (per-label), `.multiplicity(eps_stable)`.
- `route_mismatch(mm, lens, tau, weights='stationary')` — MS §4.3.
- `closure_deficit(mm, lens, tau)` and `predictive_gap(stream, holdout=0.5)` — MS §4.4 (`stream` = macro-label sequence from a seeded rollout).
- `existence_certificate(...) -> ExistenceCertificate` — MS §4.5 (first-match status priority; thresholds from config).

### 4.9 `quotients.py` (EXACT only) — MS §5
- `Package(interfaces, states, histories, continuations, events)` — all `Fraction`.
- `QuotientPair.compute(pkg, iface) -> (Q, M, pi_map, witnesses, max_fiber, delta_max)` by exact signature equality (MS §5.2).
- `transport_check(pkg, M) -> machine` (MS §5.3; raise on ill-defined transport).
- `currentization_search(pkg, candidates) -> minimal_sets` (MS §5.4).
- `internalize_schedule(pkg, phases, alpha) -> Package` (MS §5.5 protocol-trap lift; random-scan composition of phase tick and state update as one rational kernel).

### 4.10 `prices.py` — MS §6
- `value_curve(engine, L0, D, candidates, costs, b_max) -> V` (greedy; plus `value_curve_exact` by subset enumeration when |candidates| ≤ 12).
- `shadow_prices(V) -> lam`; `slack_point(lam, tol) -> b_star`; `proxy_costs(costs, rng) -> permuted`.

### 4.11 `artifacts.py`
- `load_config(path) -> dict` (validates against a literal schema dict; unknown keys are an error).
- `Run(config, out_dir)` context manager: writes `config.json` (copy), `results.json`, `manifest.json` = `{filename: sha256}` for every file in the run dir, plus `environment.json` (python version, package versions, git SHA of this repo).
- Figures: every `savefig` is paired with a CSV of the plotted arrays (same basename).

## 5. Experiment runner convention

Each `experiments/eN_*.py` exposes `main(config_path: str) -> None` and is invoked `python -m sbqos.experiments.e1_coverage configs/e1.json`. Each writes to `artifacts/eN_<name>/<config_hash8>/`. Experiments never contain formula logic — they only orchestrate module calls, per the layering rule: **formulas in modules, procedures in experiments, thresholds in configs.**

## 6. Testing strategy

- Unit tests with hand-computed expected values (listed per task in 05_IMPLEMENTATION_PLAN §tests). EXACT modules are tested with exact equality of `Fraction`s; FLOAT with `abs tol 1e-10` unless stated.
- Property tests (plain pytest loops, no hypothesis): σ_a·σ_b = σ_{a⊕b} on random vectors; Ξ PSD on random families; chain rule identity; δ ≤ ε on random small chains; CD ≥ 0 and CD = 0 on lumpable chains.
- Theorem-anchor tests: each SBT theorem the design relies on gets one test named `test_thm_<name>` (e.g. `test_thm_TIC02_defect_le_retention`, `test_thm_saturation_zero_discharge`, `test_thm_B5_lumpable_zero_deficit`, `test_thm_chain_rule`). These are the machine-checkable certificate anchors of the prototype (Lean formalization is phase 2).

## 7. Performance budget

Everything must run on one laptop core. Precomputed tables: SURF(3) canonical reps (256 entries), moment products cached by tuple(a). E3 on SURF(5) is the only heavy case: cap candidate degree-2 family to checks with adjacent supports (declare the cap in config; log dropped candidates per the no-silent-caps rule — see 04_CONTROLS §2.6). Target: full artifact regeneration < 30 min.

## 8. Artifact and reproduction discipline

`make reproduce` (or `python -m sbqos.reproduce_all`) regenerates every artifact from `configs/` and checks the manifests against the committed ones, failing on any hash mismatch (excluding `environment.json`). This mirrors the corpus's frozen-evidence-pack house style ([SPEND] evidence pack; [QM] Appendix "Reproducible experiments").

## 9. Phase-2 hooks (do not implement now)

- `certificates/` directory reserved for Lean export: each theorem-anchor test will emit a JSON "certificate object" (inputs, claimed inequality, margins) in a schema to be defined in phase 2.
- `bridges.py` reserved for transport records (original motivation document §4.5, removed 2026-09-05).
- W2 witness generalization to circuit-level noise (measurement errors) is phase 2; the code-capacity restriction is declared in every E2 artifact.
