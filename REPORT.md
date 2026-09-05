# SBQOS Prototype Report

## 1. Summary table

Artifact scan note: the experiment artifacts contain 25 registered prediction entries (P1.1-P6.4, including P4.5). Every entry has exactly one grade and a verdict. (A later follow-up investigation added experiments E7-E9 with their own registered predictions, P7.1-P9.4 — see §7.)

| id | short statement | grade | verdict | artifact |
|---|---|---:|---:|---|
| P1.1 | REP full-check residual bound and distance suppression | `registered-negative` | `registered-negative` | `artifacts/e1_default/c573063b/results.json` |
| P1.2 | single-check ablations strictly increase residual, with REP(5) end/middle distinction recorded | `registered-positive` | `registered-positive` | `artifacts/e1_default/c573063b/results.json` |
| P1.3 | witness overlap threshold and directional naming | `registered-negative` | `registered-negative` | `artifacts/e1_default/c573063b/results.json` |
| P1.4 | duplicated-check saturation gives zero discharge | `registered-positive` | `registered-positive` | `artifacts/e1_default/c573063b/results.json` |
| P2.1 | witnesses detect earlier than matched baseline | `registered-negative` | `registered-negative` | `artifacts/e2_default/54f074ca/results.json` |
| P2.2 | witness direction names the injected logical direction | `registered-negative` | `registered-negative` | `artifacts/e2_default/54f074ca/results.json` |
| P2.3 | null false-positive rate at N=4000 is at most 2 percent | `registered-positive` | `registered-positive` | `artifacts/e2_default/54f074ca/results.json` |
| P2.4 | N5 drift witness trace has Spearman rho at least 0.9 | `registered-negative` | `registered-negative` | `artifacts/e2_default/54f074ca/results.json` |
| P3.1 | greedy residual is no worse than tested baselines at every budget | `registered-positive` | `registered-positive` | `artifacts/e3_default/bfb9ffc6/results.json` |
| P3.2 | degree ladder is monotone and top rung equals exact MMSE | `registered-positive` | `registered-positive` | `artifacts/e3_default/bfb9ffc6/results.json` |
| P3.3 | duplicate candidates have zero marginal value when passed over | `registered-positive` | `registered-positive` | `artifacts/e3_default/bfb9ffc6/results.json` |
| P3.4 | greedy stops before exhausting duplicate-containing candidate list | `registered-positive` | `registered-positive` | `artifacts/e3_default/bfb9ffc6/results.json` |
| P4.1 | baseline CD near zero, multiplicity 2, certified default, delta monotone | `registered-negative` | `registered-negative` | `artifacts/e4_default/09b97eb7/results.json` |
| P4.2 | N4 non-closed while per-mode models have zero deficit | `registered-negative` | `registered-negative` | `artifacts/e4_default/09b97eb7/results.json` |
| P4.3 | N5 finite-horizon RM at least 10x baseline | `registered-negative` | `registered-negative` | `artifacts/e4_default/09b97eb7/results.json` |
| P4.4 | broken decoder trivialization guard | `registered-positive` | `registered-positive` | `artifacts/e4_default/09b97eb7/results.json` |
| P4.5 | Pearson correlation between CD and Delta_pred is at least 0.9 | `registered-positive` | `registered-positive` | `artifacts/e4_default/09b97eb7/results.json` |
| P5.1 | memoryless package has no witnesses and no payoff gap | `registered-positive` | `registered-positive` | `artifacts/e5_default/941e4f34/results.json` |
| P5.2 | N4 witness and MaxFiber are nontrivial, with positive bounded payoff | `registered-negative` | `registered-negative` | `artifacts/e5_default/941e4f34/results.json` |
| P5.3 | protocol-trap witnesses vanish after internalization | `registered-negative` | `registered-negative` | `artifacts/e5_default/941e4f34/results.json` |
| P5.4 | mode-bit currentization passes at cardinality 1 while pure checks do not | `registered-positive` | `registered-positive` | `artifacts/e5_default/941e4f34/results.json` |
| P6.1 | lambda is nonincreasing after its maximum | `registered-negative` | `registered-negative` | `artifacts/e6_default/7857bdd9/results.json` |
| P6.2 | slack point occurs before the examined budget maximum | `registered-negative` | `registered-negative` | `artifacts/e6_default/7857bdd9/results.json` |
| P6.3 | consequence test separates b*-1 from b* by more than two standard errors | `registered-negative` | `registered-negative` | `artifacts/e6_default/7857bdd9/results.json` |
| P6.4 | proxy cost permutations are strictly worse at at least 80 percent of budget points | `registered-negative` | `registered-negative` | `artifacts/e6_default/7857bdd9/results.json` |

## 2. Headline results

### E2 drift latency (`measured`)

| method | detection threshold |
|---|---:|
| W1 oracle witness | 500 shots |
| W2 deployable-shaped witness | not detected in frozen grid |
| matched pymatching baseline | 1000 shots |

W1 gives a measured 2x latency improvement over the matched baseline. The registered 4x bar fails, and W2 does not detect at the required 9/10 seeds. Null calibration passed at the frozen N=4000 setting: W1 false-positive rate 0.0, W2 false-positive rate 0.02.

### E5 decoder memory (`exact-finite`, payoff `measured`)

| package | Q | M | witnesses | MaxFiber | delta max | classification/status |
|---|---:|---:|---:|---:|---:|---|
| N1 memoryless | 4 | 4 | 0 | 1 | 0 | no memory witness |
| N4 hidden | 4 | 8 | 4 | 2 | 112329952/1318359375 | real predictive witness |
| protocol trap naive | 4 | 8 | 4 | 2 | 46/625 | schedule has predictive content |
| protocol trap internalized | 4 | 8 | 4 | 2 | 2438/78125 | `genuine_memory_after_internalization` |
| N5 latching | 4 | 5 | 4 | 2 | 539/1250 | latching memory witness |

The N4 packaged belief automaton has 8 nodes but is degenerate at the frozen defaults: the belief coordinate never flips. Payoff is therefore nil: N4 syndrome-only accuracy 0.49929, machine accuracy 0.49929, memory-only comparator accuracy 0.48944.

**Post-registration payoff v2 (`measured`).** Hard-decision accuracy cannot show a memory advantage on this model family: for REP(3) under X-only noise the mode-conditional MAP correction picks the same coset representative in every mode for any `p < 1/2`, so accuracy-scored decoders tie by construction (exactly what the frozen `payoff` block above shows). The v2 study instead scores predictors on next-round negative log-likelihood (NLL) of the 8-way outcome (2 syndrome bits + logical increment), where memory has room to show a real, non-tautological advantage. Two parameter points: the frozen N4 defaults (p0=1/50, s=1/50) and a declared "loud-mode" point (p0=1/10, s=1/100) with a stronger hidden signal.

| predictor | frozen defaults gap (nats/round) | loud-mode gap (nats/round) |
|---|---:|---:|
| oracle (ceiling; not deployable) | +0.010611 | +0.058336 |
| exact Bayes filter | +0.001956 (18% of ceiling) | +0.036150 (62% of ceiling) |
| run-length machine, K=2 | +0.000150 | +0.004289 |
| run-length machine, K=8 | +0.000805 | +0.010518 |
| run-length machine, K=16 | +0.000913 | +0.010356 |

Three findings. (1) Memory has genuine, growing-with-signal-strength predictive value: the exact filter captures 18% of the information-theoretic ceiling at the frozen (weak-signal) defaults and 62% at the louder point. (2) A tiny **declared, finite** machine — as small as 2 states — already recovers a real, positive share of that value (K=2 captures 8% of the exact filter's gap at the frozen defaults and 12% at loud-mode), rising to 41-47% (defaults) and 29% (loud-mode) by K=8-16; this is the packaging claim's headline demonstration. (3) Naively rounding the *continuous* belief coordinate to a coarse grid at every step is a genuine **negative** result at small grids — worse than no memory at all (e.g. K=2 rounding: −0.0047 at defaults, −0.070 at loud-mode) — because throwing away resolution on a moving quantity discards more than it packages. This is not noise: scanning K shows a clean, monotonic crossover from negative to positive as the grid refines and the rounding machine converges toward the exact filter — at the loud-mode point the crossover falls between K=8 and K=16 (K=16 measures +0.0301); at the quieter frozen defaults it falls later, between K=32 and K=48 (not part of the frozen K grid, confirmed in a follow-up scan). The practical reading: naive per-step quantization of a continuous belief has a **resolution threshold** below which it destroys value, and that threshold is lower when the hidden signal is stronger — a genuine packaging-cost effect the run-length machine avoids entirely by summarizing *observable history* (run length) rather than *quantizing an internal belief*.

This whole block is `measured`, post-registration (added after T9 close-out at the project owner's direction), and leaves P5.1-P5.4's verdicts untouched — see `design/DEVIATIONS.md`'s fourth entry.

### E1/E3 coverage (`exact-finite`, chain-rule items `theorem-anchored`)

E1 full traces: REP(3) 0.08367977099236641, REP(5) 0.07397290990602258, SURF(3) 0.17538887995719527. P1.2 now records all single-drop deltas; every drop is positive and REP(5) end/middle means differ (`end_larger`, 0.059310257340118334 vs 0.02035316343546449).

E3 SURF(3) greedy order is `h0, h4, h6, h3, h5, h1, h2, h7`, contracting trace from 0.434484420608 to 0.17538887995719527. REP(3) degree ladder: degree-1 trace 0.08367977099236641; degree-2-complete trace 0.027574927113702623; exact optimal-decoder MMSE is `47291/1715000`, and the artifact records `rung2_minus_mmse = 0.0`.

**Bounded-weight cross-check (`exact-finite`; corrected during the post-close audit).** E1 step 4's check ("the thresholded A_star linear decoder equals minimum-weight decoding on every weight ≤ ⌊(d−1)/2⌋ error") was originally computed with an uncentered estimator (`A·σ_L` instead of the affine `mean_D + A(σ_L − mean_L)` that the A_star decoder actually is — the same affine form E6 uses) and its failing outcome (3/4, 11/16) was recorded in the artifact but not surfaced here. With the corrected estimator: **REP(3) passes 4/4** (the affine linear decoder reproduces minimum-weight decoding exactly at d=3), **REP(5) passes 14/16** — the two weight-2 failures (supports {0,1} and {1,2}) are genuine: a single linear functional of the four syndrome bits cannot represent the majority-logic minimum-weight rule at d=5. This is the same linear-class limitation P1.1's negative already reads out at the residual level, now visible error-by-error (`interpretation`).

### E4 existence (`exact-finite` for REP rows, `measured` for stream proxy)

Baseline REP(3)+N1 at tau=1: delta 0.007144875, epsilon 0.00725, multiplicity 2, status `certified`, decoded-lens CD 0.014804630357312679, syndrome-lens CD 0.0. Broken decoder: delta 0.0, multiplicity 1, status `trivialized`. N4 decoded CD is 0.013490507923045155. N5 finite-horizon RM ratio peaks at 7.277429692683143 over the registered grid, below the frozen 10x threshold.

### E6 slack and pricing (`measured`)

REP(5) exact value curve has max greedy gap 0.0040472505228161815. Slack point at lambda_tol 1e-9 is b*=16=b_max for REP(5), and SURF(3) also exhausts the checked budget. Consequence test: logical error rate 0.007101 at budget 15 and 0.007236 at budget 16, combined SE 0.00011930723407656385, so the registered load-bearing clause fails. Proxy strict-worse fraction is 0.36875.

## 3. Negative results

Negative registered predictions are first-class prototype results: they identify where the frozen hypotheses were too strong, underspecified, or aimed at a different scale than the implemented diagnostic. The artifacts contain 14 registered-negative entries.

- **P1.1** (`interpretation`): The registered bound was written at logical-error-probability scale; tr Xi is the linear-estimator MMSE of a +/-1 observable and is not that quantity. Values: REP(3) 0.08367977099236641, REP(5) 0.07397290990602258, ratio 1.1312218364625066 vs registered 10.
- **P1.3** (`interpretation`): Some SURF(3) overlaps miss the frozen 0.9 threshold, while every Z-type drop names Zbar and every X-type drop names Xbar. Failures: h2, h6, h7.
- **P2.1** (`interpretation`): W1 detected at N=500 vs baseline N=1000, a real 2x improvement below the registered 4x bar; W2 never detected within the frozen grid.
- **P2.2** (`interpretation`): W1 overlap is 0.9979865795417403; W2 overlap is undefined because W2 never reaches the frozen detection criterion.
- **P2.4** (`interpretation`): At r=1/100 with 2000-shot windows, latching is essentially complete within the first window; Spearman rho is -0.41818181818181815 despite elevated witness magnitude from window 0 onward.
- **P4.1** (`interpretation`): The <=1e-10 CD clause holds for the syndrome lens, not the frozen decoded lens. Decoded CD at tau=1 is 0.014804630357312679.
- **P4.2** (`interpretation`): Per-mode decoded-lens CD is nonzero; the zero-deficit reading is true on the syndrome lens. Per-mode decoded CDs: 0.005091968255440196 and 0.01265221432352372.
- **P4.3** (`interpretation`): RM is several-fold above baseline and grows with horizon, but saturates below the frozen 10x threshold. Max ratio: 7.277429692683143.
- **P5.2** (`interpretation`): The predictive witness is real, but the coarsened belief coordinate is frozen at these defaults, so the machine decoder collapses to the syndrome-only MAP and payoff gap is nil.
- **P5.3** (`interpretation`): Pure internalization leaves witnesses: deterministic p0-vs-3p0 alternation carries real predictive content because current phase predicts next-round observable statistics. The frozen schedule was registered as artifact-shaped, but this package behaves as genuine state memory.
- **P6.1** (`interpretation`): Mixed costs create sawtooth marginal values at budget parities where cost-2 candidates unlock.
- **P6.2** (`interpretation`): The frozen lambda_tol is below the smallest genuine marginal in both families; REP(5) b*=16=b_max and SURF(3) b*=8=b_max.
- **P6.3** (`interpretation`): The sampled last-unit consequence did not separate b*-1 from b* by more than two standard errors: delta rate -0.00013500000000000057, combined SE 0.00011930723407656385.
- **P6.4** (`interpretation`): Proxy permutations are strictly worse on 36.875 percent of budget comparisons, below the frozen 80 percent threshold.

## 4. Controls ledger

| null battery item | where implemented | outcome |
|---|---|---|
| 1. Protocol trap / schedule internalization | E5c, `artifacts/e5_default/941e4f34/results.json` | Implemented. Outcome is a negative result for the artifact hypothesis, not a positive trap catch: the registered expectation was that internalization would dissolve the frozen schedule's witnesses (classifying it as a schedule artifact); instead internalization preserves all 4 witnesses, and the package classifies as `genuine_memory_after_internalization`. The control mechanism ran correctly; it is the "this is an artifact" prediction that failed as registered. |
| 2. Same-family saturation | E1 P1.4, E3 P3.3, unit tests | Duplicate-check discharge is zero; duplicate candidates have zero marginal value when passed over. |
| 3. Null-model calibration | E2 P2.3 | W1 false-positive rate 0.0, W2 false-positive rate 0.02 at N=4000; registered-positive. |
| 4. Proxy failure | E6 P6.4 | Implemented; proxy strict-worse fraction 0.36875. The registered >=80 percent clause failed honestly. |
| 5. Slack regime | E6 P6.2/P6.3, E3 P3.4 | Implemented. E3 stops before duplicate exhaustion; E6 frozen lambda_tol is too strict and b*=b_max. |
| 6. No silent caps | E3 SURF(5), currentization | SURF(5) logs 62 kept adjacent pairs and 214 dropped pairs out of 276 total degree-2 pairs; currentization candidate list is declared and <=12. |
| 7. Trivialization guard | E4 P4.4 | Broken decoder gives delta 0.0, multiplicity 1, status `trivialized`; registered-positive. |
| 8. Same-support discipline | E5 packages, T5 quotient machinery | Quotient comparisons use declared history catalogs; no post-hoc catalog edits in report artifacts. |
| 9. Memory-only comparator | E5 payoff | N1 memory-only accuracy 0.49714 vs machine/syndrome 0.50549; N4 memory-only accuracy 0.48944 vs machine/syndrome 0.49929. It does not reproduce a positive machine gap because the machine gap is itself 0.0 at frozen defaults. |

## 5. Scope fences and nonclaims

From `design/00_OVERVIEW.md` §2:

> 1. **No quantum hardware access.** Everything is classical simulation of stochastic Pauli / classical Markov models (plus Stim sampling).
> 2. **No claim that Ξ > 0 implies no decoder exists.** The prototype's Ξ is computed over a declared feature family (degree-1 ±1 syndrome observables, optionally degree-2); Ξ = 0 certifies coverage *by the linear estimator class over that family*; Ξ > 0 certifies a coverage gap *for that class* (see 01_MATH_SPEC §4.6). This scope fence comes from the Xi paper's own discipline (`six-birds-papers/Tsiokos_2026_Adequacy_Residuals_and_Blind_Spot_Currency.tex`, scope fences: "no generic exact adequacy").
> 3. **No Born-rule, no Bell, no coherent-dynamics claims.** All noise models are stochastic Pauli (a standard, declared restriction). The SBT quantum paper itself works at exactly this packaging level (`six-birds-papers/Tsiokos_2026_A_Six_Birds_Eye_View_of_Quantum_Theory_...tex`, §Discussion "Limitations").
> 4. **No asymptotic threshold theorem claims.** All results are finite-carrier, per the corpus's "diagnosis grade" discipline.
> 5. **No fitted proxies as evidence.** Fitted macro models are diagnostic only; theorem-grade quantities are computed exactly on declared finite models (cf. `Tsiokos_2026_Six_Birds_No_Go_Theorems_for_Audited_Emergence.tex`, scope remarks on "proxy" objects).

From `design/01_MATH_SPEC.md` §3.6:

> The prototype's Ξ is the conditional covariance of logical ±1 observables given scheduled-check ±1 observables (optionally augmented with degree-2 products). Ξ = 0 certifies exact coverage by the linear estimator class over the declared feature family; Ξ ≻ 0 certifies a coverage gap for that class and prices it. It does **not** assert that no nonlinear decoder covers the gap. The degree ladder (E3b) shows the residual contracting as feature degree grows, which is the framework's own account of what nonlinear decoding buys ([XI] chain rule; [CAST] budgeted-randomness curve).
>
> Additional note the agent must not "fix": for any stabilizer code at code capacity, there exist zero-syndrome errors with nontrivial logical action (the logical operators themselves), so a naïve F_2 kernel-inclusion test Ker L ⊆ Ker D always fails. The meaningful statement is the noise-weighted one above — logical operators are high weight, hence exponentially suppressed in the covariances. Do not implement a global kernel test; a *bounded-weight* kernel test (errors of weight ≤ t) is used only as a unit-test sanity (05_IMPLEMENTATION_PLAN, task T3 tests).

## 6. Mechanism-to-experiment evidence map

Each proposed mechanism (as enumerated in `design/00_OVERVIEW.md` §1) mapped to the experiments and
certificate anchors that demonstrate it. (This section was retitled when the project's deliverable became the paper; the mechanism list is unchanged.)

| Mechanism | Experiments | Certificate anchors (tests) | artifact paths | status |
|---|---|---|---|---|
| Claim 1 (system/existence) | E4 (+E1) | `test_thm_B5_lumpable_zero_deficit_for_syndrome_lens`, status classifier tests | `artifacts/e4_default/09b97eb7/results.json`, `artifacts/e1_default/c573063b/results.json` | Existence diagnostics implemented; default REP certificate certified, broken decoder trivialized, decoded-lens CD negatives reported. |
| Claim 2 (coverage economy) | E1, E2, E3 | `test_thm_chain_rule_rep5_seeded_splits_exact`, saturation tests, null calibration | `artifacts/e1_default/c573063b/results.json`, `artifacts/e2_default/54f074ca/results.json`, `artifacts/e3_default/bfb9ffc6/results.json` | Adequacy residual, witness, chain-rule selection, drift witness, and degree ladder reduced to practice; E2 latency partial negative reported. |
| Claim 3 (decoder memory) | E5 | quotient tests, protocol-trap test | `artifacts/e5_default/941e4f34/results.json` | Predictive quotient witnesses and currentization reduced to practice; protocol-trap frozen instance classified as genuine memory after internalization; post-registration NLL payoff v2 demonstrates measured memory value. |
| Pricing (narrow) | E6, E3 | slack consequence test, proxy null | `artifacts/e6_default/7857bdd9/results.json`, `artifacts/e3_default/bfb9ffc6/results.json` | Value curves, shadow prices, slack points, consequence test, and proxy-cost control implemented; registered slack/proxy clauses negative at frozen defaults. |

## 7. Follow-up: corrected syndrome-only witness, circuit-level generalization, closed-loop control (E7-E9)

This section reports a follow-up investigation into E2's `registered-negative` P2.1 (the deployable
syndrome-only witness W2 never detected the frozen drift injection). It does not reopen or edit E2's
verdicts — those stand as committed history. The design is frozen in `design/06_W2_PHASE2.md`; the full
development trail, including two scope simplifications and three correctness fixes found *before* results
were frozen, is recorded in `design/DEVIATIONS.md`. All new work here uses experimental framing
(hypothesis, method, empirical demonstration) rather than legal framing, per current project direction —
unlike section 6 above, nothing in this section is being positioned as a legal filing basis.

### Why W2 registered negative (`w2_diagnosis.py`, exact + measured)

Four findings, computed exactly against the installed package by the project's own designer/reviewer role
and independently re-verified against the committed test suite, before any new correction code was written
(pinned as tests in `tests/test_w2_diagnosis.py`, not merely asserted in prose). (1) The existing W2
statistic centers its covariance before comparing to the model,
discarding a real, nonzero mean-shift signal (exact: `delta_mean_L_norm_sq = 0.0011542233263741337` for
the frozen E2 injection, concentrated entirely on one of eight native checks). (2) Lifting the drift signal
through the coverage-optimal linear map A* — built for logical-value prediction, not drift sensitivity —
compresses its energy roughly 73x (`delta_K_LL_frobenius_sq = 0.0032632199622995104` vs.
`delta_D_lifted_frobenius_sq = 4.470316641917462e-05`). (3) W2's threshold was borrowed from a differently-
scaled statistic (W1's), rather than calibrated against its own null. (4) Most importantly: the frozen E2
injection (a ZZ error on 2 of the 3 qubits making up the Zbar logical support) sits close to a minimum-
weight logical-failure path by construction — an exact Walsh-Hadamard-inversion technique recovers the
full native-check syndrome pmf and its per-shot KL divergence from the declared model exactly; comparing
this to the logical-failure channel's KL divergence (measured) shows the frozen scenario is structurally
disadvantageous to *any* syndrome-only method (KL ratio 0.665, syndrome-vs-logical), while drift away from
minimum-weight failure paths is up to ~773x easier for a syndrome-only statistic in this small grid. The E2
negative is fully explained by this combination — independent of, and in addition to, findings (1)-(3).

### E7 — corrected witness ladder across a drift-scenario grid (`measured`)

A degree-≤2 Walsh-Hadamard/GLR-style quadratic statistic (fixing findings 1-2 at once, no lift, no
discard), a whitened matched-filter naming dictionary, and a CUSUM sequential wrapper, scored against an
upgraded (fixed-window + CUSUM) baseline across three scenarios spanning finding (4)'s range.

| id | statement | verdict | key values |
|---|---|---:|---|
| P7.1 | W2a's own-null threshold ≤ 10% of the borrowed W1-derived threshold | `registered-negative` | measured ratio 1.33x, not ≤0.10x — the O(p) vs O(p²) reasoning described the *injected signal's* scale, not the *null-fluctuation* scale Omega actually calibrates; both statistics reduce to eigenvalues of a 2x2 matrix, so comparable null scales aren't surprising in hindsight |
| P7.2 | off-support scenario (4,8): best corrected rung detects ≥10x earlier than baseline | `registered-positive` | witness N_det=1000 (W2b/W2c), baseline never detects within the frozen grid (up to N=16000) — the dramatic effect Finding 4's KL ratio (~773x) predicted |
| P7.3 | original E2 scenario (0,3): registered **expected negative** — no W2 rung beats baseline | `registered-positive` (i.e. the predicted failure held) | baseline N_det=1000; W2b/W2c=4000, W2d=16000, W2a never detects — consistent with the 0.665 KL ratio favoring the failure channel here |
| P7.4 | near-parity scenario (2,5) | `measured`, no bar | baseline N_det=1000; W2b/W2c=2000, W2d=8000 |
| P7.5 | off-support naming: ≥8/10 seeds name a true-pair qubit, overlap ≥0.6 | `registered-negative` | 3/10 seeds named a true-pair qubit; mean forward-mapped logical-direction overlap 0.869 (comfortably above 0.6) — SURF(3) has only 2 logical operators, so direction-overlap is a coarse, near-binary check that can't fully discriminate between qubits, even though detection and direction-naming both work |
| P7.6 | null false-positive rate ≤2% for every rung | `registered-negative` | baseline 0%, baseline_cusum 0%, W2a 2%, W2d 2% (all pass); W2b 6% (fails) — plausibly small-sample calibration noise in a higher-dimensional whitened statistic, not evidence the statistic is unreliable |
| P7.7 | sequential vs. fixed-window N_det reported symmetrically | `measured`, no bar | reported per scenario; both sides got the same sequential-testing upgrade |

### E8 — circuit-level generalization (`measured`; phase-2 hook reserved in `02_ARCHITECTURE.md` §9)

Scope simplified from a multi-scenario grid to a single global noise-rate drift (2x), `distance=3` only, no
sequential rung — logged as a deviation with reasoning (circuit-level detectors lack SURF(3)'s clean
on/off-logical-support structure; `distance=5` deferred). Predictions were frozen from a pilot (seeds
500-504) before the main run (seeds 0-9) executed.

| id | statement | verdict | key values |
|---|---|---:|---|
| P8.1 | witness detects ≥2x earlier than the pymatching baseline | `registered-positive` | N_det(witness)=50, N_det(baseline)=100, ratio exactly 2.0 — **at the thinnest margin the discrete grid (`[10,20,50,100,250,500,1000,2000]`) allows**, not a comfortable win; the pilot's ~5x was a smaller-sample estimate and should not be read as the headline number |
| P8.2 | null false-positive rate ≤2% | `registered-positive` | 0% for both witness and baseline |

### E9 — closed-loop witness-triggered decoder recalibration (`measured`)

Four decoder policies (static floor, oracle ceiling, scheduled blind recalibration, witness-triggered
targeted recalibration) on an epoch-discretized timeline. Two scope corrections were made *before* any
result was frozen (full account in `DEVIATIONS.md`): the drift scenario had to be changed from a uniform
global rescale (verified to give MWPM decoding nothing to do — matching decisions are invariant to a
uniform rescaling of equal edge weights) to a heterogeneous one (`before_measure_flip_probability` elevated
20x, other channels fixed), and the witness policy's self-correction mechanism needed two rounds of pilot-
driven fixes (a one-shot design that could permanently blind itself on a false alarm; then a noisy-reference
bug once fixed to be self-correcting) before it worked as intended.

| id | statement | verdict | key values |
|---|---|---:|---|
| P9.1 | witness-triggered control is within 0.01 of oracle post-drift error | `registered-positive` | witness 0.0930, oracle 0.0916, absolute gap 0.0014 |
| P9.2 | witness-triggered control beats **genuinely budget-matched** scheduled recalibration | `registered-positive` | witness 0.0930 vs. scheduled 0.1115 (gap 0.0185) — budgets matched exactly per seed (identical realized recalibration-event counts, e.g. `[1,1,2,2,1,1,3,2,1,2]` for both policies, not just matched on average; an earlier draft compared against a fixed-period schedule averaging a similar but not identical budget, caught and fixed before this checkpoint closed) |
| P9.3 | higher, unmatched-budget scheduling reported descriptively | `measured`, no bar | scheduled-frequent (~5x the budget) scores 0.0946, between witness and scheduled-matched; the gap to witness (0.0016) is smaller than the estimated paired standard error at 10 seeds (~0.002) — **statistically unresolved**, not a clean win either way. The resolved comparison is scheduled-frequent vs. scheduled-matched: spending several times the budget on a blind schedule closes most, not all, of the gap to witness/oracle |
| P9.4 | pre-drift trigger rates reported descriptively | `measured`, no bar | witness 0.0 on this seed set (0.2 in the pilot — both honest measurements of a probabilistic event over a 15-epoch window); scheduled rates are scheduled events, not false alarms, and are reported separately |

The recalibration procedure in E9 deliberately only ever searches over the one noise channel known (by
construction of this experiment) to be drifting — it does not attempt to identify *which* channel changed.
That identification is what E7's naming step (W2c) demonstrates separately; E9 isolates the timing/budget
question from the naming question.

## 8. Reproduction

**Known-good environment** (exact versions all numbers in this report were measured against; added after
an external review flagged that `pyproject.toml` previously had no version floors and a full-suite
reproduction attempt on an unspecified environment did not complete — a targeted re-run of the specific
test in question completed in 1.24s on the environment below, so the discrepancy is believed to be
environment-specific rather than a defect in the suite, but exact-version reproduction is the safest path):

| component | version |
|---|---|
| Python | 3.10.12 |
| numpy | 2.2.6 |
| scipy | 1.15.3 |
| stim | 1.16.0 |
| pymatching | 2.4.0 |
| matplotlib | 3.10.8 |
| pytest | 9.0.2 |

Setup command:

```bash
pip install -e .
```

Test and reproduction commands:

```bash
pytest -q
python -m sbqos.reproduce_all
python -m sbqos.reproduce_all
```

Observed `pytest -q` (T0-T9 build, 6 experiments):

```text
127 passed in 173.60s (0:02:53)
```

Observed `pytest -q` (current, after the E7-E9 follow-up in §7):

```text
149 passed in 183.85s (0:03:03)
```

Observed first `reproduce_all` run (T0-T9 build, e1-e6):

```text
e1.json: running
e1.json: manifest ok
e2.json: running
e2.json: manifest ok
e3.json: running
e3.json: manifest ok
e4.json: running
e4.json: manifest ok
e5.json: running
e5.json: manifest ok
e6.json: running
e6.json: manifest ok
WALL_CLOCK 5:03.04
```

Observed second `reproduce_all` run (T0-T9 build, e1-e6):

```text
e1.json: running
e1.json: manifest ok
e2.json: running
e2.json: manifest ok
e3.json: running
e3.json: manifest ok
e4.json: running
e4.json: manifest ok
e5.json: running
e5.json: manifest ok
e6.json: running
e6.json: manifest ok
WALL_CLOCK 6:52.63
```

The second run's manifest hashes were byte-identical to the first; no PNG nondeterminism was observed.

Observed `reproduce_all`, twice, after the E7-E9 follow-up (all nine experiments; e7-e9 add circuit-level
Stim sampling and the E9 closed-loop timeline, hence the longer wall clock):

```text
e1.json: manifest ok   e2.json: manifest ok   e3.json: manifest ok
e4.json: manifest ok   e5.json: manifest ok   e6.json: manifest ok
e7.json: manifest ok   e8.json: manifest ok   e9.json: manifest ok
reproduce_all_wall_clock_seconds 768.05   (run 1)
reproduce_all_wall_clock_seconds 826.10   (run 2)
```
Both runs verified all nine manifests; `results.json` byte-identity was additionally spot-checked directly
for e7/e8/e9 (each experiment's own smoke test also asserts this on every `pytest` run).

Manifest SHA-256 roots (hash of `manifest.json` itself):

| manifest path | sha256 |
|---|---|
| `artifacts/e1_default/c573063b/manifest.json` | `23bd212b623b6936c9a9e95f960aa14b1e505c617b567a1842981006bf59d1e9` |
| `artifacts/e2_default/54f074ca/manifest.json` | `9c964f8ff65bbde89efc577215448fbe7901a047b5816cf5adada909b84519b2` |
| `artifacts/e3_default/bfb9ffc6/manifest.json` | `375da2852a7349ced7076b2a11375b9af7386bee1b6cec256469800d5305b3b4` |
| `artifacts/e4_default/09b97eb7/manifest.json` | `d0e2d926803647bb2d70e03bdfe40fbc9ff835f92c50b8aac353ba1257a72905` |
| `artifacts/e5_default/941e4f34/manifest.json` | `f3c0940a1fcdd84022064e53dd1b176167c5dbe80e8eb70dc29b66c5c569d374` |
| `artifacts/e6_default/7857bdd9/manifest.json` | `2088c7b8f3dac740f9fd22fd8528ecd12733a30b0f838d0bf45fb4f81821a2aa` |
| `artifacts/e7_default/ab6885e6/manifest.json` | `d2797a3d5651c0f8763478620717fccf5279a6f6023b418944e8089f6678ee37` |
| `artifacts/e8_default/cf7094d8/manifest.json` | `da2b38f9d11288c6fb258b8f33186b07b9331d223129dd6f5af24c795184b77d` |
| `artifacts/e9_default/f24323a0/manifest.json` | `32d69ee04e12640c5c9161ea6c4f4cb21453af2c19e65794b35a535402d1fbec` |

Acceptance checklist outcomes:

- `pytest` green: yes, 149 tests passed (127 from the T0-T9 build plus 22 from the E7-E9 follow-up).
  Theorem-anchor tests present and passing: `test_thm_chain_rule_rep5_seeded_splits_exact`,
  `test_thm_top_ladder_rep3_mmse_matches_bruteforce_exact`, `test_thm_B5_lumpable_zero_deficit_for_syndrome_lens`.
- `python -m sbqos.reproduce_all` twice: yes, both runs reported manifest ok for all nine experiments;
  manifest hashes were unchanged across runs.
- Every experiment directory complete: yes. Each directory contains `config.json`, `results.json`,
  `manifest.json`, `environment.json`, PNG figure(s), and CSV twin(s).
- Every registered prediction has a verdict: yes. The T0-T9 build's 25/25 entries (§1) plus the E7-E9
  follow-up's P7.1-P7.7, P8.1-P8.2, P8.cost, P9.1-P9.4 (§7) all have exactly one grade and verdict.
- Null battery ledger complete: yes, 9/9 items recorded in §4 for the T0-T9 build; §7's follow-up reuses
  the same null-calibration and matched-budget-control discipline (P7.6, P8.2, and E9's mandatory
  matched-budget comparison for P9.2) without adding new battery categories.
- Dependency audit: AST import audit found only stdlib plus frozen dependencies (`numpy`, `scipy`, `stim`, `pymatching`, `matplotlib`, `pytest`) and `sbqos`. `rg "six-birds|sys\\.path|PYTHONPATH|\\.\\./six-birds" src tests pyproject.toml` returned no dependency/import hits (checked again after §7's additions).
- EXACT-path float audit: `quotients.py` is clean for `float(` and `np.`. In `moments.py`, `float(` appears only in the `exact=False` branch; exact mode keeps `Fraction`. In `closure.py`, `float`/`np` uses are documented FLOAT operations (KL/log stream proxy, stationary/finite-horizon weights, conversion for certificate record fields) or branch-specific helpers; exact δ/ε/RM paths use `Fraction` arithmetic where `model.exact` is true. `w2_diagnosis.py`'s `full_syndrome_pmf` (§7) is exact end to end (Fraction), confirmed by grep; §7's circuit-level modules (`circuit_level.py`) are FLOAT throughout by design (no closed-form model exists at circuit level, per `06_W2_PHASE2.md` §1's declared relaxation).
- `DEVIATIONS.md`: present and complete with 8 entries: 3 from the original T0-T9 build (finite-horizon RM
  for N5 in E4; predictive-gap finite-horizon stream-length caveat; E5 packaged belief automaton replacing
  impossible exact transport closure on real mixing kernels), 1 post-close audit fix (E1's bounded-weight
  cross-check used an uncentered estimator, corrected before the E7-E9 follow-up began), 1 post-
  registration measurement (E5 payoff v2, a separately labeled measured NLL study), and 3 from §7's
  follow-up (E7's shared-per-N null-calibration granularity; E8's scope simplification and pilot-then-
  freeze account; E9's drift-scenario correction, epoch-discretization, and two pilot-driven witness-policy
  fixes, including the checkpoint-10 budget-
  matching correction).
