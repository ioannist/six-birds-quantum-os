# 05 — Implementation Plan

Ordered tasks. Do them in order; each task has acceptance tests that must pass before moving on. "MS" = 01_MATH_SPEC, "ARCH" = 02_ARCHITECTURE. Estimated sizes are guidance, not limits.

---

## T0 — Scaffolding (small)

Create the package skeleton per ARCH §2, `pyproject.toml` (name `sbqos`, deps per ARCH §1), empty modules with docstring headers, `tests/` with a trivial passing test, `.gitignore` for `artifacts/**` except `**/manifest.json`.

**Accept:** `pip install -e .` works; `pytest` green; `python -c "import sbqos"` ok.

## T1 — `linalg2.py` + `codes.py` (medium)

Implement per ARCH §4.1–4.2. Hard-code SURF(3) check supports with an ASCII lattice diagram in comments. Implement `canonical_rep` for REP (majority logic) and SURF(3) (BFS by weight over all 2^18 X/Z patterns is too big — instead BFS outward from weight 0 over errors up to weight 4, filling a 256-entry syndrome table; assert the table is complete).

**Accept (hand-computed):**
- REP(3): syndrome of e = X on qubit 2 is (1,1); `canonical_rep` returns X₂ for syndrome (1,1).
- SURF(3): every single-qubit X, Y, Z error has nonzero syndrome; `logical_flips` of X̄ = (1, 0) pattern flipping only the Z̄ pairing; `sympl(X̄, Z̄) = 1`, `sympl(X̄, X̄) = 0`, every check commutes with every logical and every other check (loop assert).
- `rank_f2` on the SURF(3) check matrix = 8.

## T2 — `noise.py` + `moments.py` (large, EXACT care)

Per MS §1.3, §2 and ARCH §4.3–4.4. Implement the closed-form mean with per-qubit factors; memoize on `bytes(a)`. Implement N3's conditioning branch and mode-conditioned engines for N4/N5.

**Accept (exact `Fraction` equalities, hand-derived):**
- N1(p=1/20), a = Z₁ (detects X on qubit 1): `mean(a) = 1 − 2/20 = 9/10`.
- N2(p=3/100), a = single-qubit Z: `mean = 1 − (4/100) = 24/25`. (1 − 4p/3 with p = 3/100.)
- σ-product property: for random a, b over 100 seeded draws, `mean` of a⊕b equals the moment of the product variable computed by brute-force enumeration on a 3-qubit model (enumerate all 4³ Pauli patterns with their probabilities). **This brute-force cross-check is the key correctness gate for everything downstream — do not skip.**
- Covariance blocks on REP(3)+N1(1/20) match brute-force enumeration over the 8 error patterns exactly.
- N3: brute-force check on a 3-qubit toy (enumerate the mixture).

## T3 — `xi.py` (medium)

Per MS §3, ARCH §4.5. Both paths (Fraction/float). Include `saturation_test` (a candidate is flagged saturated if its discharge value < 1e-12 float / = 0 exact).

**Accept:**
- `test_thm_chain_rule`: on REP(5)+N1, random L split into L₀ ∪ M (5 seeded splits): `Ξ(D|L) == Ξ(D|L₀) − discharge` exactly (Fraction) — [XI] chain rule.
- `test_thm_saturation`: duplicated check ⇒ discharge = 0 exactly.
- PSD: Ξ eigmin ≥ −1e−9 on 20 random families (float path).
- Brute-force MMSE cross-check on REP(3): tr Ξ(D|full checks, degree-2-complete family) equals the enumerated optimal MMSE of the logical bit given the syndrome (compute by conditioning over the 8 errors) to 1e−12. This validates the "top of the ladder = optimal decoder" identity used in E3b.

## T4 — `markov.py` + `closure.py` (large)

Per MS §4, ARCH §4.7–4.8. Build REP(3) model first and validate exhaustively; then SURF(3) (1024 states), N4/N5 variants (×2 states), broken decoder variant.

**Accept:**
- REP(3)+N1(1/20), τ=1: hand-compute the 8×8 kernel row for e = 0 (probabilities of each new error pattern) and assert equality; `stationary` residual ≤ 1e−12.
- `test_thm_TIC02_defect_le_retention`: δ ≤ ε on every built model (REP/SURF × N1/N2/N4/N5 × τ ∈ {1,2,4}) — [F1] T-IC-02.
- `test_thm_B5_lumpable_zero_deficit`: CD_τ ≤ 1e−12 on mode-free models with the decoded lens — [NG] B5 / [F3] Thm 8.
- Variational spot-check of CD (MS §4.4): loss at K* ≤ loss at 2 perturbed kernels.
- Broken decoder: δ = 0 exactly, multiplicity = 1.
- RM = 0 (≤ 1e−12) on an exactly lumpable toy chain built for the test (4 states, 2 blocks, within-block-identical rows).

## T5 — `quotients.py` (large, EXACT only, most subtle module)

Per MS §5, ARCH §4.9. Signatures are tuples of `Fraction`; classes are frozensets of history indices; **equality is exact — never compare floats here.** Implement `internalize_schedule` by constructing the lifted state set X × Φ and the single random-scan rational kernel.

**Accept:**
- Memoryless package (REP(3)+N1): witness count = 0, |Q| = |M|.
- Two-history toy with a designed hidden bit (build in-test: 2 states, 2 histories differing only on a coordinate no current event reads, one continuation that routes on it): witness count = 1, MaxFiber = 2, Δ^max computed by hand = the designed gap. This mirrors [HOL]'s memory-wheel shape at minimal size.
- Transport well-definedness assertion trips on a deliberately broken package (in-test negative case).
- Internalization of a 2-phase alternating toy kills its witnesses (the [PT] trap reproduced at unit scale).
- Currentization: adding the hidden-bit event to the toy passes with cardinality 1.

## T6 — `streams.py` (medium)

Per MS §3.5, ARCH §4.6. Stim only for N1/N2/N3 sampling; N4/N5 by internal loop. Empirical covariance = standard unbiased estimator on ±1 columns.

**Accept:** empirical blocks on 10^6 N2 shots match model blocks entrywise within 5σ binomial error (seeded); w1/w2 functions return calibrated nulls: on model-consistent shots, λ_max(Δ) exceeds Ω_stat in ≤ 2/100 seeded runs.

## T7 — `prices.py` (small)

Per MS §6, ARCH §4.10.

**Accept:** on REP(3), greedy V(b) equals exact enumeration V(b) for all b (small case); slack point exists; permuted-cost curve ≤ structural curve at every b in a seeded run (if not, that's fine — it's a registered prediction, not a test; the *test* only checks the machinery runs deterministically).

## T8 — `artifacts.py` + experiment runners E1–E6 (large)

Per ARCH §4.11, §5 and 03_EXPERIMENTS. Write configs with the frozen defaults. Implement experiments strictly as orchestration.

**Accept:** each `python -m sbqos.experiments.eN ... configs/eN.json` completes; rerun produces byte-identical `results.json`; manifests verify; every figure has its CSV; `reproduce_all` passes twice.

## T9 — REPORT.md (medium)

Per 04_CONTROLS §4 template. Fill the prediction table with verdicts; write the controls ledger; copy the scope fences verbatim; run and document the EXACT-path float audit (04_CONTROLS §5).

**Accept:** 04_CONTROLS §5 checklist fully ticked.

---

## Pitfalls (read twice; these are the predicted failure modes)

1. **Symplectic pairing direction.** ⟨a,e⟩ = a^x·e^z + a^z·e^x. A Z-check *detects X errors*. Getting this backwards makes every REP test fail confusingly. The T1 commutation loop-assert catches it early.
2. **σ_a are ±1, not 0/1.** Covariances are of ±1 variables. Mixing conventions breaks the product identity σ_a σ_b = σ_{a⊕b}. Convert syndromes to ±1 once, at the boundary (`streams.py`), and document it.
3. **Do not implement a global F_2 kernel test for adequacy** (MS §3.6 note): it trivially fails for every code and is not the theory's statement. The bounded-weight variant appears only inside T3/E1 sanity tests.
4. **Moments of hidden-mode models are per-mode** (ARCH §4.4). Asking `MomentEngine` for N4 moments without a mode is a design error — the API must make it impossible (constructor takes the conditioned submodel).
5. **Pseudoinverse rank tolerance.** K_LL is often singular (checks can be moment-degenerate). Use rcond=1e-12 consistently; in EXACT mode determine rank by exact elimination, never by float rounding of Fractions.
6. **Prototype choice is part of the package.** The recovery prototypes (canonical reps) are a declared choice ([F1]; [QM]); changing them changes δ and RM. Freeze them in the model constructor; never recompute differently between runs.
7. **Quotients: catalog discipline.** s⁺ uses only declared (continuation, event) pairs — do not "helpfully" close under composition ([HOL]'s explicit rule). Adding derived continuations silently changes M.
8. **Stationarity for CD.** CD_τ is defined under the stationary law. Burn-in rollouts do not substitute: compute π exactly from P. For N5 (absorbing latch), the chain is not irreducible — use the quasi-stationary regime instead: restrict CD reporting to a declared finite horizon with the initial distribution declared (mode 0, zero error), and label it `finite-horizon CD` in results; do NOT report stationary CD for N5.
9. **Seeds.** One seed per config, all generators derived from it (`rng.spawn()` or fixed offsets). Never call `np.random.*` module-level functions.
10. **Registered predictions are not tuning targets.** If P2.1's factor-4 fails at factor-2.5, the result is a `registered-negative` with the honest number, and it is still a good result. Do not move the goalposts in code.

## Suggested order-of-work summary

T0 → T1 → T2 (with its brute-force gate) → T3 → T4 → T5 in strict order; T6/T7 parallel after T3/T4; T8 after all; T9 last. The single most load-bearing test in the whole build is T2's brute-force enumeration cross-check — everything in E1–E3 and E6 reduces to those moments.
