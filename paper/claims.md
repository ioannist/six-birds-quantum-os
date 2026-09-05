# Paper Claim Inventory

Companion to `facts.md`. Every claim the paper is permitted to make appears here with its evidential
grade, its supporting fact rows, and the section where it lives. Compiled 2026-07-06,
at git HEAD `81dc25f0b9fdf16887bf195c7f126109e00b879d` (same extraction state as facts.md).

## Hard rules (binding on all paper prose)

1. **"Proves" / "proof" only for `theorem-anchored` claims.** Everything else uses: "computes exactly"
   (exact-finite), "measures" (measured), "held / failed as registered" (registered-±), "we read this
   as" (interpretation).
2. **Never blend grades in one sentence.** A sentence carries exactly one grade; if a result and its
   reading must appear together, split into two sentences.
3. **No number without a fact_id.** Every quantitative statement traces to `facts.md`; the LaTeX carries
   the fact_id in a comment on the same line.
4. **Registered-negatives are never softened, summarized away, or omitted** from any table or count that
   includes their sibling positives.
5. **Banned words/framings:** "proves" (outside rule 1), "optimal" (except the exact-MMSE result C-10,
   which literally attains the enumerated optimum), "significantly" (unless a computed SE backs it, cf.
   C-33), unqualified "outperforms", and all legal/patent framing ("invention", "claim" in the legal
   sense, "reduction to practice").

## Grade vocabulary (verbatim from `design/04_CONTROLS_AND_CLAIMS.md` §3)

> - `theorem-anchored` — the claim is an instance of a cited SBT theorem verified computationally (e.g., δ ≤ ε held on every model). The strongest grade the prototype can issue.
> - `exact-finite` — exact rational computation on a declared finite model (E1, E4-exact, E5 quotient results).
> - `measured` — seeded sampling with reported uncertainty (E2 latencies, E6 consequence test).
> - `registered-positive` / `registered-negative` — a frozen prediction that passed / failed. Failures are reported in their own section, never deleted, never re-run with tuned parameters (a tuned re-run is a NEW experiment labeled as such).
> - `interpretation` — connective prose (e.g., "this is the leakage signature"). Must be marked; carries no evidential weight.

(For infrastructure statements — test counts, hashes, reproducibility mechanics — this inventory uses
`count/meta`, matching facts.md.)

## Claim table

Sections refer to the paper plan: §1 Intro, §2 SBT primitives, §3 QEC instantiation, §4 Methods,
§5 Results I (certificates), §6 Results II (negatives), §7 Results III (diagnosis→correction arc),
§9 Limitations. Column `facts` lists fact_ids from `facts.md`.

### Thesis-level claims (§1, §7 close, abstract)

| id | claim | grade | facts | section |
|---|---|---|---|---|
| C-01 | Four of SBT's core primitives, instantiated on QEC, each yield a concrete, machine-checkable audit object (adequacy residual, existence certificate, predictive-quotient witness, protocol-trap classification); a fifth (pricing/shadow-prices) was implemented and produced working machinery but no positively-evidenced result; a sixth (transport/functoriality, "certified deformation bridges") was explicitly scoped out and never implemented. All of this is in one open, reproducible codebase. | interpretation (supported by the aggregate of §5–§7 claims) | F-146, F-147; design/00_OVERVIEW.md §1 (M5 deferral) | §1, abstract |
| C-02 | The framework's falsification discipline operated end-to-end: 25 + 14 predictions were frozen before implementation, and every one received a verdict against its frozen bar, including 14 failures in the original build reported unaltered. | count/meta | F-147, F-148, F-106..F-144 | §1, §4, abstract |
| C-03 | The framework's audit machinery is productive, not merely descriptive: one of its own registered failures (the deployable drift witness) was diagnosed *within the framework* by exact computation, corrected, re-registered (including a prediction of continued failure that held), and carried to circuit level and a closed control loop. | interpretation (supported by C-24..C-35) | F-075..F-097 | §1, §7, abstract |

### Instantiation and scope (§3)

| id | claim | grade | facts | section |
|---|---|---|---|---|
| C-04 | The prototype's Ξ certifies coverage only for the linear estimator class over the declared feature family; Ξ ≻ 0 does not assert that no nonlinear decoder exists. (Scope fence, quoted verbatim.) | non-claim / scope fence | REPORT.md §5 verbatim | §3 |
| C-05 | All evidence is classical simulation of stochastic Pauli / classical Markov models (plus Stim circuit-level sampling); no hardware, no Born-rule/Bell/coherent-dynamics claims, no asymptotic threshold claims. | non-claim / scope fence | REPORT.md §5 verbatim | §3, §9 |

### Certificates on ground truth (§5)

| id | claim | grade | facts | section |
|---|---|---|---|---|
| C-06 | The chain rule Ξ(D\|L) = Ξ(D\|L₀) − discharge holds exactly (Fraction arithmetic, identically zero discrepancy) on the tested models. | theorem-anchored | F-162 (test names); design/03 §E1 | §5 |
| C-07 | δ ≤ ε holds on every built model; lumpable models give zero closure deficit on the syndrome lens. | theorem-anchored | F-162 | §5 |
| C-08 | Full-check residual traces: REP(3) 0.0837, REP(5) 0.0740, SURF(3) 0.1754 (exact values in facts). | exact-finite | F-041 | §5 |
| C-09 | Dropping any single check strictly increases the residual; REP(5) end vs middle drops differ as recorded (held as registered). | registered-positive | F-002, F-042, F-107 | §5 |
| C-10 | The degree-2-complete family attains the enumerated optimal-decoder MMSE exactly: rung-2 trace equals 47291/1715000 with recorded difference 0.0. | exact-finite (and registered-positive as P3.2) | F-046, F-010, F-115 | §5 |
| C-11 | Greedy chain-rule selection is never worse than the tested baselines at any budget on SURF(3) (held as registered); the greedy order and full contraction curve are recorded. | registered-positive | F-009, F-044, F-045, F-114 | §5 |
| C-12 | Saturation controls: duplicated checks have exactly zero discharge/marginal value (held as registered, both E1 and E3 forms). | registered-positive | F-004, F-011, F-109, F-116 | §5 |
| C-13 | The existence certificate distinguishes the four statuses on ground truth: baseline REP(3)+N1 `certified` (δ=0.007144875, ε=0.00725, multiplicity 2), broken decoder `trivialized` (δ=0 exactly, multiplicity 1), and the p-sweep's defect-only rule flips the label to `degrading` at p=1/5 — where the full classifier would say `trivialized` (multiplicity 0, F-166); the paper must say so. | exact-finite | F-048, F-049, F-050, F-166 | §5 |
| C-14 | The trivialization guard catches the perfect-but-empty decoder (held as registered). | registered-positive | F-016, F-121 | §5 |
| C-15 | CD correlates with the out-of-sample predictive gap across the model/τ grid: Pearson r = 0.936 with N5 included (held as registered; the without-N5 value −0.171 is reported alongside). | registered-positive (r value: measured) | F-017, F-054, F-122 | §5 |
| C-16 | Predictive-quotient witnesses separate the model family exactly: memoryless 0 witnesses; N4 hidden 4 witnesses, MaxFiber 2, Δ^max = 112329952/1318359375; N5 latching 4 witnesses, Δ^max = 539/1250. | exact-finite | F-028, F-029, F-030 | §5 |
| C-17 | Currentization: adding the mode bit dissolves the predictive surplus at cardinality 1; no set of pure check bits does (held as registered). | registered-positive | F-021, F-126 | §5 |
| C-18 | Under a proper scoring rule (next-outcome NLL), memory has genuine measured value: the exact Bayes filter captures 18% of the oracle ceiling at frozen defaults and 62% at the loud-mode point; a declared 2-state run-length machine already captures a positive share (8% / 12% of the filter's gap), rising with K at the frozen defaults; in loud mode it rises to K=8 and sits slightly lower at K=16 (0.01036 vs 0.01052, F-038) — never say "grows with K" unqualified. | measured (percent readings: interpretation) | F-034..F-040 | §5 |
| C-19 | Naive per-step belief rounding is value-destroying below a resolution threshold (negative gaps at small K), negative at every frozen-default resolution (non-monotone, worst at K=4, F-036) and crossing to positive only at loud-mode K=16 (F-039) — a real packaging-cost effect, reported plainly including the loud-mode K=16 positive that contradicted the pre-stated all-negative expectation. | measured (threshold reading: interpretation) | F-036, F-039 | §5 |
| C-20 | The protocol-trap control is a negative result for the artifact hypothesis, not a positive trap demonstration: the registered expectation was that internalizing the frozen alternating schedule would dissolve its witnesses (classifying it as a schedule artifact); instead internalization preserved all 4 witnesses (`genuine_memory_after_internalization`), so that expectation failed as registered. The control mechanism itself (currentization/internalization) ran correctly — it is the "this is an artifact" hypothesis that was falsified, and the paper must state it that way, not as "the control worked." | registered-negative (classification: exact-finite) | F-020, F-032, F-070, F-125 | §5, §6 |
| C-21a | Pricing machinery runs and is exact where declared: V_exact and the λ curve (exact-finite); the greedy-vs-exact gap ≤ 0.00405 on REP(5) is a measured comparison (F-056) and must be sentenced separately. | exact-finite (curves) / measured (gap) | F-055..F-058 | §5 |
| C-21b | Every one of the registered slack/consequence/proxy predictions for pricing (P6.1-P6.4) failed at the frozen tolerances. | registered-negative | F-022..F-025, F-059, F-060 | §5, §6 |

### Negatives as first-class evidence (§6)

| id | claim | grade | facts | section |
|---|---|---|---|---|
| C-22 | 14 of 25 original registered predictions failed as frozen, and each failure has a recorded, specific reading; the paper presents three worked examples and the full table. | count/meta (readings: interpretation) | F-148, F-061..F-074 | §6 |
| C-23 | The failures decompose into three types — bound written at the wrong scale (e.g. P1.1), threshold frozen too strictly (e.g. P6.2's λ_tol below the smallest genuine marginal), and genuinely informative structure the prediction mischaracterized (e.g. P5.3, P2.1) — none required changing any frozen parameter to discover. | interpretation | F-061, F-072, F-070 | §6 |

### The diagnosis→correction arc (§7)

| id | claim | grade | facts | section |
|---|---|---|---|---|
| C-24 | The deployable witness W2 failed as registered in E2 (never detected in the frozen grid; oracle W1 detected at 500 vs baseline 1000). | registered-negative | F-005, F-026, F-063, F-110 | §7 |
| C-25 | Diagnosis finding 1: the centered-covariance statistic discards a nonzero exact mean-shift signal (‖Δmean_L‖² = 0.00115, concentrated on one check with exact value −331776/9765625). | exact-finite (mean shift; the energy is a float sum of exact entries) | F-075 | §7 |
| C-26 | Diagnosis finding 2: the A*-lift compresses the drift signal's energy ≈73× (0.00326 → 4.47e-05). | exact-finite inputs, float energies (ratio reading: interpretation) — never head a sentence with an unqualified exact-finite marker | F-076 | §7 |
| C-27 | Diagnosis finding 3: W2's threshold was borrowed from a differently-scaled statistic rather than its own null. | interpretation (mechanism confirmed by P7.1's measurement, C-29) | F-077, F-079 | §7 |
| C-28a | Diagnosis finding 4 (exact half): the full native-check syndrome pmf is exactly recoverable by Walsh–Hadamard inversion; the resulting per-shot syndrome-side KL divergences from the declared model, evaluated numerically from the exact pmfs, are 0.006151 / 0.010823 / 0.051352 for the three scenarios. | exact-finite (pmfs); KL values numerical | F-078 | §7 |
| C-28b | Diagnosis finding 4 (measured half): comparing those exact syndrome KLs against measured logical-failure-channel KLs gives ratios of 0.665 / 1.100 / 773.4, showing the frozen E2 scenario is structurally hard for any syndrome-only method while off-support drift is up to ~773× easier. Use F-078's diagnosis-phase logical-failure numbers for this ratio; F-078b's independently-seeded re-measurement (from the E7 artifact) gives different absolute logical-KL values from a different seed set and must never be substituted into this same table. | measured | F-078, F-078b | §7 |
| C-29 | The corrected-calibration prediction P7.1 failed as registered (measured ratio 1.33, not ≤0.10): the original O(p)/O(p²) reasoning described signal scale, not null-fluctuation scale. Reported as an honest surprise. | registered-negative (reading: interpretation) | F-079, F-131 | §7 |
| C-30 | On the off-support scenario the corrected ladder detects at N=1000 while both baselines never detect within the grid (held as registered, bar was ≥10×). | registered-positive | F-080, F-132 | §7 |
| C-31 | On the original E2 scenario, the pre-registered *prediction of continued failure* held: no corrected rung beats the baseline (baseline 1000 vs W2b/W2c 4000). | registered-positive (a predicted negative that held) | F-081, F-133 | §7 |
| C-32 | Naming: only 3/10 detecting seeds named a true-pair qubit (failed as registered) while the forward-mapped logical-direction overlap was 0.869 (above the 0.6 bar) — qubit-level naming on a 2-logical code is coarse. W2b's null FPR (6%) also failed its 2% bar; all other rungs passed. | registered-negative (readings: interpretation) | F-083, F-084, F-135, F-136 | §7 |
| C-33 | At circuit level (Stim, rotated d=3 memory), the corrected statistic detects a global 2× rate drift at N_det = 50 vs the pymatching baseline's 100 — meeting the pilot-frozen 2× bar exactly, i.e. at the thinnest grid-resolved margin; this sentence must always carry the margin caveat. | registered-positive (margin caveat mandatory) | F-086, F-088, F-138 | §7 |
| C-34 | Closed loop: witness-triggered recalibration lands ≈0.0014 above the oracle ceiling in post-drift logical error rate (F-091 exact gap 0.0014266…; bar 0.01) and beats a *genuinely per-seed budget-matched* blind schedule by 0.0185 (identical realized event counts per seed). Rounded presentations 0.0014 / 0.0185 are authorized; write "about 0.0014 above", never "within 0.0014" (the exact gap exceeds 0.0014). Always carry C-39's one-channel scope when summarizing E9. | registered-positive | F-091, F-092, F-093, F-141, F-142 | §7 |
| C-35 | The unmatched higher-budget schedule (≈5× the events) closes most of the gap: its 0.0016 deficit to the witness policy is smaller than the ≈0.002 paired SE at 10 seeds — statistically unresolved, and the paper must say so; the resolved contrast is against the budget-matched schedule (C-34). | measured (resolution caveat mandatory) | F-094, F-095, F-096, F-097 | §7 |

### Methods / infrastructure (§4, §10)

| id | claim | grade | facts | section |
|---|---|---|---|---|
| C-36 | The modules and code paths *labeled* exact (the moment engine's `exact=True` branch, `xi.py`'s pseudoinverse/discharge/chain-rule construction, all of `quotients.py`) are rational end-to-end (`Fraction`, no float) and are gated by a brute-force enumeration cross-check. This must **not** be generalized to "all exact-path computation" — `xi.py`'s blind-spot witness uses a float eigendecomposition and `chain_rule_check`'s reported discrepancy is a float comparison of exact matrices (both by design, not a violation, since the *inputs* stay exact); `markov.py`'s stationary distributions are float; §7's circuit-level modules (`circuit_level.py`) are float throughout because no closed-form model exists at circuit level (declared in `design/06_W2_PHASE2.md` §1). The precise, file-by-file audit is REPORT.md §8's float-audit paragraph — cite that, do not paraphrase it more broadly. | count/meta | F-162; REPORT.md §8 audit lines | §4 |
| C-37 | Every experiment regenerates byte-identically from committed configs; all nine manifests verify twice in a row; 149 prototype tests pass (plus, since 2026-09-04, 21 paper-figure-pipeline tests: 170 total; say "149 prototype tests" when the count is attributed to the prototype). | count/meta | F-145, F-146, F-149..F-159 | §4, §10 |
| C-38 | Circuit-level phases (E8/E9) replace closed-form pre-derivation with a declared pilot-then-freeze protocol (pilot seeds disjoint from scored seeds; bars frozen before the scored run); all deviations from frozen designs are logged in a public deviations file (8 entries). | count/meta | F-099..F-101b, F-102..F-105, F-138..F-144 | §4 |
| C-39 | E9's recalibration deliberately searches only the one channel known by construction to drift — it demonstrates timing/budget value, not drift identification (that is E7's naming step); the paper must state this scope plainly wherever E9 is summarized. | non-claim / scope fence | F-105 | §7, §9 |

## Non-claims checklist (must appear in §3/§9; the paper may never contradict these)

- No quantum-hardware validation of any kind (C-05).
- No claim that Ξ > 0 implies no decoder exists (C-04).
- No claim that the corrected witness beats failure-rate monitoring in general — only scenario-dependent
  advantage, with the original scenario an explicit counterexample (C-31).
- No claim that witness-triggering beats *frequent* blind recalibration (unresolved, C-35) — only
  budget-matched blind recalibration (C-34).
- No mechanism-novelty claim for detector-statistic drift tracking or decoder reweighting per se; the
  contribution is the certificate/audit framing plus the demonstrated falsification discipline (goes in
  §1 and §8 honestly).
- No claim that all six SBT primitives from the original mapping were implemented: transport/
  functoriality (M5, "certified deformation bridges") was explicitly deferred and never built (C-01).
- No claim that the protocol-trap experiment demonstrates the trap mechanism catching an artifact — the
  tested instance was found to be genuine memory, not an artifact; the control's value is that it did not
  misclassify, not that it caught something (C-20).
- No claim that the pricing/shadow-price component produced a positive result — the machinery is exact
  and runs correctly, but every registered prediction about it failed at the frozen tolerances (C-21a/C-21b).
- No generalization of any "exact" or "exact-finite" grade beyond the specific labeled modules/functions
  named in C-36 — always cite REPORT.md §8's file-by-file float audit rather than paraphrasing it more
  broadly.

## Provenance note (added 2026-07-06)

An external adversarial reviewer (given the SBT corpus + this repository, per `external_review/
REVIEW_PROMPT.md`) found four issues in an earlier draft of this file that are now fixed above: C-01
overclaimed "all six primitives... implemented" (transport was deferred); C-20 risked reading as "the
trap succeeded" rather than "the artifact hypothesis failed"; C-21 and C-28 each blended two evidential
grades in one row, violating this file's own hard rule 2; C-36 overgeneralized "exact-path" beyond the
specific modules that earn that label. The reviewer's other major findings (the since-removed INVENTION.md's overbroad
framing, environment pinning for reproduction, an under-surfaced E1 correction) are addressed directly in
INVENTION.md (removed 2026-09-05), `pyproject.toml`, and `design/DEVIATIONS.md` respectively, not in this file.
