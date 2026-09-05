# 03 — Experiments E1–E6

Each experiment specifies: purpose, setup, procedure, **registered predictions** (frozen now, before implementation — a failed prediction is reported, never tuned away), pass/fail criteria, controls, and outputs. Config values shown are the frozen defaults; they live in `src/sbqos/configs/eN.json`.

Common conventions: seed = 0 for headline runs plus a 10-seed robustness sweep {0..9} where sampling is involved (house style: [QM] robustness appendix); every figure ships its CSV; every claim in `results.json` carries a `claim_grade` field per 04_CONTROLS §3.

---

## E1 — Coverage audit sanity: Ξ = 0, Ξ > 0, witness correctness (EXACT)

**Purpose.** Establish the residual engine on ground truth: full check schedules cover; removing checks opens a priced, witnessed gap. This is the evidence anchor for mechanism 2 of the original motivation document §5 (removed 2026-09-05; see `REPORT.md` §6).

**Setup.** REP(3)+N1(p=1/20), REP(5)+N1(1/20), SURF(3)+N2(3/100). EXACT path (`Fraction`). D = logical family. Ω = 0.

**Procedure.**
1. Full schedule L_full: all checks. Compute Ξ(D|L_full), A_star.
2. Ablations: for each single check h dropped, L_drop(h); compute Ξ, witness (Ω=0), λ_max.
3. REP(3) exhaustive: compute Ξ for all 2^2 = 4 check subsets (REP(3) has 2 checks); REP(5): all 16 subsets.
4. Bounded-weight cross-check (unit-test grade): for REP(d) with errors restricted to weight ≤ ⌊(d−1)/2⌋, verify the linear decoder from A_star, thresholded, equals minimum-weight decoding on every restricted error (exhaustive loop).

**Registered predictions.**
- P1.1: For REP(d)+N1 with full checks, Ξ(D|L_full) = 0 **is NOT expected exactly** — the logical operator X̄ has zero syndrome, so a residual of order p^d survives. Registered: `0 < tr Ξ(D|L_full) ≤ 2·(binom(d, ceil(d/2))·p^{ceil(d/2)})²`-order; concretely tr Ξ ≤ 1e-2 at p=1/20, d=3, and tr Ξ(d=5) < tr Ξ(d=3) by at least 10× (distance suppression visible in the residual).
- P1.2: dropping any single check strictly increases tr Ξ (monotonicity, [XI] :: native coarsening); the increase for an end check differs from a middle check (REP(5)) — record the ordering.
- P1.3: the witness vector z for L_drop concentrates on the logical component whose minimum-weight uncovered error is enabled by the dropped check (for REP: always LX̄; for SURF(3) dropping an X-check vs a Z-check flips which logical the witness names). **Pass criterion:** |⟨z, expected logical axis⟩|² ≥ 0.9 in all ablations.
- P1.4: duplicated-check saturation: adding an existing check to any L gives discharge = 0 exactly (EXACT path).

**Controls.** Saturation null (P1.4); exact-vs-float agreement ≤ 1e-12 on all REP quantities.

**Outputs.** Table (code, subset, tr Ξ, λ_max, witness label); figure: tr Ξ vs subset size for REP(5) (all 16 subsets); figure: witness overlap bar chart.

---

## E2 — Drift blind-spot witness: named detection before error-rate detection

**Purpose.** Headline demonstration: an unmodeled channel is *named* by the witness (which logical direction, which checks) at fewer samples than logical-error-rate monitoring needs to merely *detect* a change. Grounds claim 2's runtime story.

**Setup.** SURF(3). Declared model: N2(p=3/100). Truth: N3(p=3/100, q=1/50, pair = the two data qubits shared by one weight-2 Z-logical path segment — fix indices in config). FLOAT path; shots via `streams`.

**Procedure.**
1. Model blocks from `MomentEngine` (declared N2). A_star from model.
2. For N ∈ {250, 500, 1000, 2000, 4000, 8000, 16000}: sample N shots from truth (seeded); compute W1 (oracle) and W2 (syndrome-only) witnesses with Ω_stat at 99th percentile (B = 200 null bootstraps, MS §3.5).
3. Baseline detector at matched false-positive rate 1%: two-sided binomial test on the logical error rate of the frozen `pymatching` decoder (configured with declared-model weights) vs its declared-model expectation (computed from 10^6 model-simulated shots, seeded).
4. Detection sample size N_det for each method = smallest N with detection in ≥ 9 of 10 seeds. Witness *naming* accuracy: overlap of W1/W2 witness vector with the true injected channel's logical action direction (computed analytically from N3 − N2 covariance difference).
5. Repeat with N5 (latching leakage, r=1/100) as the injected truth (drift grows over rounds; use round-indexed batches of 2000 shots and plot witness magnitude vs round window).

**Registered predictions.**
- P2.1: N_det(W1) ≤ N_det(baseline)/4; N_det(W2) ≤ N_det(baseline)/2. (Rationale: the injection perturbs specific syndrome covariances at O(q) while the logical error rate moves at O(q·p^{O(1)}) — the witness reads the covariance directly.)
- P2.2: witness naming overlap ≥ 0.8 (W1) / ≥ 0.6 (W2) at N = N_det.
- P2.3: under the *null* (truth = declared N2), witness false-positive rate ≤ 2% across 50 seeded null runs (calibration check).
- P2.4 (N5): witness magnitude is monotone in the round window index (Spearman ρ ≥ 0.9), i.e. the audit tracks accumulating drift.

**Controls.** Null calibration (P2.3); seed sweep; matched false-positive design (both detectors at 1%).

**Outputs.** Detection-latency curves (λ_max and p-values vs N, both methods, 10 seeds ribbons); witness-vector bar charts vs truth direction; N5 drift trace.

---

## E3 — Chain-rule check selection and the degree ladder

**Purpose.** Show the marginal-value machinery selects measurements as well as (or better than) static/random schedules at matched budget, with certified saturation. Grounds the adaptive-syndrome-economy claim.

**Setup.** (a) SURF(3)+N2, candidate family = all 8 checks, budget sweep b = 1..8, greedy per MS §3.4; baselines: random order (10 seeds), lexicographic order. Metric: tr Ξ(D|selected) vs b. (b) *Degree ladder* (E3b): REP(3)+N1, L₀ = full degree-1 checks; candidates = all degree-2 products; verify residual contraction down the ladder and compare tr Ξ at each rung with the exact optimal-decoder MMSE (computable by enumeration over the 8 errors: MMSE of logical bit given full syndrome).
- (c) SURF(5)+N2 scaling spot-check with the adjacency-capped degree-2 family (02_ARCHITECTURE §7).

**Registered predictions.**
- P3.1: greedy tr Ξ(b) ≤ every baseline's tr Ξ(b) at every b (greedy is optimal for b=1 by construction; for b>1 dominance over the tested baselines is the registered expectation, not a theorem — report any violation).
- P3.2 (ladder): tr Ξ decreases weakly at every rung (chain rule, theorem — must hold to 1e-12), and at the top of the declared ladder equals the enumerated optimal MMSE within 1e-10 for REP(3) (the full degree family generates all functions of the 2-bit syndrome).
- P3.3: every duplicated or F_2-linearly-dependent-and-moment-degenerate candidate flagged by `saturation_test` has value < 1e-12.
- P3.4: greedy stops (tol_stop) strictly before exhausting candidates on REP(3) (slack exists) — links to E6.

**Controls.** Saturation null; random-baseline seeds; exact-vs-float on REP(3).

**Outputs.** Coverage-vs-budget curves (greedy vs baselines); ladder plot tr Ξ vs degree with optimal-MMSE floor line; ranked-selection tables.

---

## E4 — Existence certificate: δ, ε, RM, CD_τ across noise regimes (EXACT for δ, ε)

**Purpose.** Demonstrate the objecthood certificate distinguishing `certified / degrading / non_closed / trivialized` on ground-truth models. Grounds claim 1's existence component.

**Setup.** Markov cycle models (MS §4.1): REP(3)+N1, SURF(3)+N2 (baseline, expect `certified`); N4 hidden-mode drift (expect `non_closed` via CD); N5 latching (expect RM signature + degrading); a deliberately broken decoder (recovery to fixed state |0⟩_L regardless of syndrome) as the `trivialized` control. τ ∈ {1, 2, 4}.

**Procedure.**
1. For each model: compute δ_{τ,f}, ε_{τ,f} (EXACT), assert δ ≤ ε (theorem anchor [F1] T-IC-02); prototype stabilities; multiplicity at ε_stable = 1/20.
2. RM_τ per MS §4.3 with both lenses (syndrome lens; decoded-frame lens).
3. CD_τ exact per MS §4.4 (lens = decoded frame; hidden coordinates excluded from lens). Also Δ_pred from a 10^5-step seeded rollout; record (CD, Δ_pred) pairs across all models/τ.
4. Assemble `ExistenceCertificate` per model; render the status table.

**Registered predictions.**
- P4.1: baseline models: CD_τ ≤ 1e-10, multiplicity = 2 (REP: two stable logical prototypes), status `certified` for p below a threshold sweep point; δ grows monotonically with p (sweep p ∈ {1/100, 1/20, 1/10, 1/5}) and status flips to `degrading` at the frozen δ_max.
- P4.2: N4: CD_τ > 0 (registered: ≥ 1e-3 nats at defaults), status `non_closed`, while per-mode conditional models each have CD ≈ 0 — the deficit is *entirely* the hidden mode ([CAST] decomposition).
- P4.3: N5: decoded-lens channel accuracy stays high while RM is large on the latched fiber — the "channel-perfect but RM large" leakage signature ([XOR]); registered: RM(N5) ≥ 10× RM(baseline) at matched p.
- P4.4: trivialized control: δ = 0 exactly, multiplicity = 1, status `trivialized` (the guardrail catches the perfect-but-empty decoder).
- P4.5: Pearson r(CD, Δ_pred) ≥ 0.9 across the model/τ grid ([CAST] benchmark r = 0.959).

**Controls.** Trivialized decoder (P4.4); lumpable-model zero checks; τ-sweep.

**Outputs.** Certificate table (model × τ × status with all diagnostics); δ vs p curves with status bands; (CD, Δ_pred) scatter with r.

---

## E5 — Decoder-memory witness and minimal decoder machine (EXACT)

**Purpose.** Decide decoder memory from first principles; synthesize the minimal machine; kill the scheduling artifact with the protocol trap. Grounds claim 3.

**Setup.** Quotient packages (MS §5) on REP(3): (a) N1 memoryless baseline; (b) N4 hidden-mode; (c) **trap**: no hidden mode, but noise alternates deterministically between p₀ and p₁ on odd/even rounds (external schedule — the artifact case); (d) N5 latching.

**Procedure.**
1. For each package: compute Q, M, π, witness count, MaxFiber, Δ^max (exact rationals).
2. (b): extract the minimal machine (M-classes + transports); compare its size with the naive history automaton (all distinct histories).
3. (c): compute witnesses on the naive package (schedule external), then apply `internalize_schedule` (MS §5.5, α = 1/2) and recompute. Classify per the [HOL] taxonomy: `artifact_trap` iff witnesses vanish after internalization.
4. (b), (d): currentization search over candidates = {mode bit, latch bit, each single extra check}; report minimal passing sets.
5. Decoder-payoff validation (float): simulate 10^5 rounds; compare logical accuracy of (i) memoryless decoder (function of current syndrome only), (ii) the minimal-machine decoder (function of M-class). Registered gap bound: accuracy(ii) − accuracy(i) ∈ (0, Δ^max] for (b); = 0 within statistical error for (a).

**Registered predictions.**
- P5.1: (a) witness count = 0 → memoryless decoding certified lossless; measured payoff gap consistent with 0.
- P5.2: (b) witness count ≥ 1, MaxFiber = 2, minimal machine ≅ (syndrome class × mode-belief coarsened to 2 states); payoff gap > 0 and ≤ Δ^max ([HOL] Δ^max bound).
- P5.3: (c) naive witnesses > 0 but internalization kills them → `artifact_trap` ([PT] theorem; [HOL] benchmark pair) — the schedule was masquerading as memory.
- P5.4: (b) currentization: {mode bit} passes with cardinality 1; no set of pure check bits passes (the mode is not a linear function of any current syndrome) — hiddenness is real, matching the [HID] exposure dichotomy: adding the exposing observable dissolves the predictive surplus.

**Controls.** Protocol trap (P5.3) is itself the control; same-support discipline: all comparisons on the declared history catalog only.

**Outputs.** Quotient tables per package; minimal-machine digraph figure; internalization before/after table; payoff bar chart with Δ^max line.

---

## E6 — Shadow prices and the slack certificate

**Purpose.** Demonstrate priced resource control: marginal values, slack point, and the registered do-nothing consequence of slack. Grounds the pricing claim (narrow form).

**Setup.** REP(5)+N1 and SURF(3)+N2. Candidates: all checks (cost 1) + degree-2 products (cost 2, REP only). Budget sweep to b_max = cost of full family. FLOAT.

**Procedure.**
1. V(b) via greedy; REP(5) also exact by enumeration (|𝒞| ≤ 12 rule); report greedy gap.
2. λ(b) = V(b+1) − V(b); slack point b* (λ_tol = 1e-9).
3. Consequence test: for budgets b ≥ b*, build the A_star linear decoder on the selected set; simulate 10^6 shots; registered: logical error rate at b and at b* differ by ≤ 2 standard errors, while at b*−1 vs b* differ by > 2 SE (the last unit of budget below slack is load-bearing).
4. Proxy null: permuted costs (10 seeds); compare coverage-per-budget curves.

**Registered predictions.**
- P6.1: λ(b) is nonincreasing after its max (diminishing returns; registered expectation, not theorem — report violations).
- P6.2: slack exists: b* < b_max for both codes (REP(5) reaches Ξ ≈ its floor before using all degree-2 products).
- P6.3: the consequence test passes as stated in step 3.
- P6.4: proxy costs give a strictly worse V(b) at ≥ 80% of budget points ([SPEND] proxy-failure signature).

**Outputs.** V(b) and λ(b) curves with b* marked; consequence-test table; proxy-vs-structural curves.

---

## Cross-experiment table stub (for REPORT.md)

| Mechanism (original motivation document §5, historical) | Experiments | Certificate anchors (tests) |
|---|---|---|
| Claim 1 (system/existence) | E4 (+E1) | test_thm_TIC02, test_thm_B5, status classifier tests |
| Claim 2 (coverage economy) | E1, E2, E3 | test_thm_chain_rule, test_thm_saturation, null calibration |
| Claim 3 (decoder memory) | E5 | quotient transport checks, protocol-trap test |
| Pricing (narrow) | E6, E3 | slack consequence test, proxy null |
