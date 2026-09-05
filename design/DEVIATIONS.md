# Deviations from the frozen design

One dated entry per deviation, with reason. Per `00_OVERVIEW.md`'s rule: the implementing agent must not
deviate from the frozen design docs without recording a note here.

---

## 2026-07-05 — `route_mismatch`'s absorbing-model guard blocks a mandatory N5 deliverable (deferred to T8/E4)

**What happened.** During the T4-fix round (checkpoint 3c), `route_mismatch` was guarded to raise
`ValueError` for any `model.is_absorbing` model (alongside `closure_deficit` and
`full_existence_certificate`), on the reasoning that RM_τ's definition (`01_MATH_SPEC.md` §4.3) uses
stationary fiber weights, and N5's true stationary distribution is degenerate (near-100% absorbed into the
latched mode) — the same problem `05_IMPLEMENTATION_PLAN.md` Pitfall #8 identifies for CD_τ.

**The conflict.** `01_MATH_SPEC.md` §4.3 itself (not just an experiment doc) states the report *must*
exhibit "a decoder lens that is channel-accurate but RM ≈ max under N5" as the signature leakage result,
and `03_EXPERIMENTS.md` E4/P4.3 registers this as a prediction (`RM(N5) ≥ 10× RM(baseline) at matched p`,
both lenses). The blanket guard makes this deliverable currently impossible to produce — no finite-horizon
(or otherwise non-degenerate-weighted) RM variant exists yet. Manager-independent analysis also suggests
that even an *un-guarded* RM computed under N5's true stationary law would likely give a misleadingly *low*
RM (not the promised RM ≈ max): true stationary weight is almost entirely on the latched-mode fiber members,
which washes out exactly the mode-0-vs-mode-1 heterogeneity RM is meant to detect. A correct fix needs a
weighting scheme (e.g., finite-horizon, matching `closure_deficit_finite_horizon`'s pattern) chosen with the
same care as the rest of T4's absorbing-model fixes — this requires E4's actual procedure (which horizon,
which "matched p" baseline) in hand, not a guess made outside that context.

**Decision.** Leave `route_mismatch`'s guard as-is for now (T4 close). Design and build a finite-horizon (or
equivalent) RM variant as part of T8/E4, when the full P4.3 procedure is being implemented and the right
horizon/comparison choices are being made directly against the registered prediction — not before.

**Why this is safe to defer.** T4's own acceptance bar (`05_IMPLEMENTATION_PLAN.md` §T4) is the certificate
machinery working correctly on the declared models with the diagnostics as currently specified; it does not
require every noise model's finite-horizon variant of every diagnostic to exist yet. Nothing in T4 claims
N5's RM story is finished — this note exists precisely so that claim is never made by omission.

---

**Addendum 2026-09-05 (paper sign-off review, independent-review pass R5): weighting convention.** `01_MATH_SPEC.md` §4.3 writes
the outer sum as `Σ_x Σ_{z∈B_x} w_z ·‖R_τ(z,·) − K_τ(x,·)‖₁` with the parenthetical "w = stationary weights,
renormalized per fiber". `closure.py::_route_mismatch_for_lens` applies the renormalization inside the
fiber average K_τ (weights `w/fiber_mass`) and uses the global stationary weight `π(z)` in the outer sum, so
RM_τ = Σ_x Σ_{z∈B_x} π(z)‖R_τ(z,·) − K_τ(x,·)‖₁ with K_τ(x,·) = Σ_{z∈B_x} π(z|x) R_τ(z,·). This is the reading
consistent with the CD_τ decomposition (Σ_x π(x) Σ_z π(z|x) = Σ_z π(z)) and is the formula the paper's
Appendix E now states; the spec's parenthetical is ambiguous, not contradicted. No number changes.

## 2026-07-05 — `predictive_gap_finite_horizon`'s stream length can wash out the declared horizon for fast-absorbing models

**What happened.** `predictive_gap_finite_horizon(model, tau_stream_length, seed, horizon, initial_state)`
draws the simulated stream's *first* state from the horizon-evolved distribution, then evolves the sampled
stream stochastically for `tau_stream_length` further rounds before fitting/evaluating the order-1/order-2
predictors. For `rep3_n5_model()`'s default parameters, the manager independently confirmed the mode-0 mass
decays from the declared horizon's starting point to below 1e-4 by ~1000 further rounds and below 1e-9 by
~2000 further rounds (via direct matrix-power computation). Any `tau_stream_length` much larger than this
(the current test uses 20000; `03_EXPERIMENTS.md` E4 step 3 specifies a 10^5-step rollout for Δ_pred) means
the sampled stream itself re-absorbs into the same near-degenerate regime the finite-horizon fix exists to
avoid, long before the stream ends — so the `horizon` parameter's effect on the reported value is real but
small, dominated by a brief prefix rather than reflecting a genuinely horizon-conditioned process throughout.

**Decision.** No code change now — the function is not incorrect (it computes exactly what it documents:
a real, deterministic NLL gap starting from the declared horizon), but its practical use for N5-scale
absorption timescales needs a stream length chosen relative to the model's own absorption rate (or an
episodic/multi-restart sampling scheme instead of one long trajectory) to stay meaningfully horizon-limited.
This will be designed as part of T8/E4's actual Δ_pred(N5) measurement (P4.5), where the right choice can be
made against the real procedure instead of guessed now.

**Why this is safe to defer.** Nothing in T4 relies on `predictive_gap_finite_horizon` giving a
horizon-sensitive answer at any particular `tau_stream_length` — the T4-fix packet's own acceptance bar only
asked for "finite, deterministic, and sensitive to horizon at *some* choice of parameters," which is met.

---

## 2026-07-05 — E5's minimal decoder machine is extracted as an exact packaged belief automaton, not via `transport_check` on a linear-kernel Package

**What the design says.** `01_MATH_SPEC.md` §5.3 defines the minimal machine as the predictive quotient M
with transport maps, asserted computationally via `transport_check`; the checkpoint-4 clarification to §5.3
already records that audit-purpose catalogs are not transport-closed and that the checkpoint-4 independent review
moved the obligation to E5: "when the experiment needs a real minimal decoder machine, it must build or
freeze a purpose-designed transport-closed catalog and verify transport_check succeeds there."

**What the manager found when designing that catalog.** For a mixing QEC chain, *no* finite catalog of
distribution-valued histories is exactly transport-closed under the real `one_round` kernel: pushed
distributions converge toward stationarity without ever exactly recurring, so exact signature matching
(the only equality `quotients.py` admits, correctly) fails for any declared finite catalog — verified
computationally at checkpoint 4 down to the finest possible catalog. Furthermore, an observation-driven
belief catalog is also never exactly closed: Bayes updates produce an infinite orbit of exact rationals.

**Decision.** E5 extracts the minimal machine for the N4 package as an **exact packaged belief automaton**:
nodes = (syndrome value, coarse belief), where the belief coordinate is coarsened to two *declared
prototype* values with a declared tie-breaking rule, and the transition map is "exact Bayes update, then
reinstate to the nearest prototype." This is a deterministic, exactly-computable finite machine — and the
coarsen-then-reinstate step is itself an instance of the framework's own packaging pattern ([F1]'s
`U_f∘Q_f`: coarse-grain, then prototype lift), declared as part of the package rather than hidden.
`transport_check`'s succeeding-case demonstration remains the T5 unit-scale toy (where linear-kernel
closure genuinely holds); it is not run on the real-model machine, because the object it checks (exact
linear-kernel transport closure) provably cannot exist there.

**Also recorded ahead of the run (manager pre-derivation).** At N4's frozen defaults (p0=1/50, s=1/50),
the one-step mode evidence is weak: from a mode-0 point belief, no single syndrome observation moves the
posterior above 1/2 (max ≈ 0.152 at s=3), so the 2-state coarsened machine is degenerate (belief never
flips) and the MAP correction is mode-independent — P5.2's "payoff gap > 0" clause is expected to come out
`registered-negative`, with the honest reading that the predictive witness is real (exact, catalog-level)
while its *decoding payoff* at these parameters is nil: witnesses certify a predictive distinction, not
its economic value — exactly the separation [HOL] and `04_CONTROLS_AND_CLAIMS.md` §1 insist on.

---

## 2026-07-05 — E1's bounded-weight cross-check used an uncentered estimator (post-close audit finding)

**What happened.** E1 step 4's unit-test-grade sanity check (`05_IMPLEMENTATION_PLAN.md` T3: "the
thresholded A_star linear decoder equals minimum-weight decoding on every restricted error") was originally
implemented with an uncentered estimator, `A @ outcomes`, rather than the affine form the A_star decoder
actually is: `mean_D + A @ (outcomes - mean_L)` — the same affine form E6's consequence test already uses
correctly. With the uncentered estimator, the check's own artifact recorded a failing outcome (REP(3) 3/4,
REP(5) 11/16), but this failure was not surfaced in `REPORT.md` at T9 close — the report described the
check as passing without noting the artifact's own recorded failures.

**Decision.** Found and fixed during a self-initiated post-close audit (commit `2157539`, "fix E1
bounded-weight estimator (affine, was uncentered)"), before any of the E7-E9 follow-up work began.
Corrected to the affine estimator; regenerated E1's artifacts deterministically. The corrected outcome is
genuinely different, not merely restored: **REP(3) now passes 4/4** (the affine linear decoder reproduces
minimum-weight decoding exactly at d=3); **REP(5) passes 14/16**, and the two remaining failures (weight-2
errors on supports {0,1} and {1,2}) are a real, structural finding — a single linear functional of the four
syndrome bits cannot represent the majority-logic minimum-weight rule at d=5. This is the same
linear-estimator-class limitation P1.1's registered-negative already reads out at the aggregate residual
level, now visible error-by-error. `REPORT.md` §2 ("Bounded-weight cross-check") documents the corrected
values but — per an external review's finding — did not, until this entry, log the fix in this deviations
ledger, where every other correction of this kind is tracked.

**Why this is safe.** The check is explicitly unit-test-grade sanity (`05_IMPLEMENTATION_PLAN.md` T1 accept
bullets), not a registered prediction with a frozen pass bar — its correction does not change any of
P1.1-P1.4's verdicts. Nothing about the original E1 residual (`tr Ξ`) computation was affected; only the
bounded-weight decoder-equivalence check itself was uncentered.

---

## 2026-07-05 — E5 payoff v2 is a post-registration measured NLL study, not a change to P5.1-P5.4

**What happened.** After T9 close-out, the project owner authorized an additional E5 payoff measurement to
demonstrate a genuine operational value for memory in the paper narrative. The original hard-decision
accuracy payoff remains nil at the frozen N4 defaults because REP(3)'s mode-conditional MAP correction is
mode-independent for every p < 1/2. The memory value instead appears under a proper scoring rule: per-round
negative log-likelihood of the next 8-way syndrome/logical-increment outcome.

**Decision.** Add a separately labeled `measured`, post-registration `payoff_v2` block to E5. P5.1-P5.4's
registered verdicts, values, and interpretations are unchanged. The loud-mode point is a declared second
point, not a replacement for the frozen defaults. The per-step rounding-machine control was registered in
the implementation packet before coding as an expected negative outcome and is reported plainly from the
actual run.

**Why this is safe.** The new block does not alter any quotient, currentization, protocol-trap, or registered
prediction result. It is an additional reduction-to-practice measurement of predictive value under NLL,
with its post-registration status explicit in both artifacts and `REPORT.md`.

---

**Addendum 2026-09-05 (paper sign-off review, independent-review pass R3).** Two properties of the payoff-v2 predictors were
under-described in prose and are recorded here so the paper states them exactly. (1) The run-length
machines are driven by `outcome & 3`, i.e. the two low-order bits of the 3-bit round outcome; with the
basis order `(check_1, check_2, logical)` and MSB-first indexing in `_delta_distribution`, those bits are
the second syndrome bit and the simulator-known logical increment — the machines are therefore not
syndrome-only predictors, and no syndrome-only operational claim may rest on F-035/F-038. (2) The
run-length gaps are scored on the second half of each trajectory (lookup table trained on the first half),
whereas the oracle, exact-filter and rounding gaps are scored on the full trajectory; cross-predictor
magnitude comparisons are qualitative. Neither property changes any recorded number or verdict.

## 2026-07-05 — E7's W2a/W2b own-null thresholds are calibrated once per shot count N, not once per (N, seed) cell

**What the packet asked for.** `design/06_W2_PHASE2.md` §3.3 specifies E7's detection sweep mirroring E2's
own per-(N, seed) recalibration style verbatim, for direct comparability with E2's P2.1.

**What happened.** Recalibrating W2a's and W2b's own-null thresholds fresh for every one of the
3 scenarios × 7 grid points × 10 seeds cells (210 cells, each needing its own `bootstrap_B=200` null
bootstrap) made the frozen run impractically slow. Since both thresholds are calibrated purely from the
**declared** model (independent of which truth scenario or which seed is being scored), the implementer instead
calibrated one threshold per `N` in `n_grid` (shared across all 3 scenarios and all 10 seeds at that N).

**Why this is safe.** The baseline detector (`_baseline_detector`/`_baseline_truth_result`, reused verbatim
from `e2_drift_witness.py`) is completely unaffected, so P7.3's comparison to E2's own P2.1 verdict stays
apples-to-apples on the side that matters for that comparison (the baseline). Sharing one declared-model-
only threshold across seeds at fixed N is, if anything, a more realistic model of a deployed witness (a
threshold calibrated once and then applied consistently) than recalibrating it independently per seed. No
registered prediction's bar was loosened or tightened to accommodate this — the same 99th-percentile
bootstrap convention is used, just computed at 7 points (one per N) instead of 210.

**What this does not excuse.** P7.6's null calibration check still ran fresh, independent null trials
against these shared thresholds (not against themselves), so the reported false-positive rates (W2a 2%,
W2b 6%, baseline 0%) are honest measurements of the shared thresholds' real behavior, not circular.

---

## 2026-07-05 — E8 (Phase 2, circuit-level) scope simplified from `design/06_W2_PHASE2.md` §4, and its
predictions are pilot-then-freeze rather than exactly derived

**What the design doc describes.** §4 envisions a multi-scenario drift grid (on/off logical-support
analog), `distance` 3 **and** 5 with a cost/scaling comparison, locality-sparsified pairwise detector
features, and a CUSUM sequential rung, generalizing E7's full ladder to circuit-level noise.

**What was actually built (manager's scope decision, made when dispatching T12a).** A single global
uniform noise-rate drift scenario (`p0 -> p1 = 2*p0`, applied identically to all four of
`stim.Circuit.generated`'s noise parameters), `distance=3` only, the full (non-sparsified) degree-≤2
detector feature family (40 detectors -> 820 features, confirmed tractable without sparsification at this
scale), and fixed-window detection only (no CUSUM rung).

**Why.** Circuit-level detectors from a rotated-surface-code memory circuit don't have SURF(3)'s clean
"which qubits sit on which logical row" structure, so Finding 4's on/off-logical-support dichotomy (E7's
organizing idea) doesn't carry over cleanly — a single, honest global-drift scenario is the right scope for
first establishing that the corrected witness generalizes past code-capacity noise at all. `distance=5` and
locality-sparsification are deferred as documented future work rather than attempted under an already large
addendum's time budget. Sequential (CUSUM) testing was already demonstrated at the code-capacity level in
E7 (W2d) and does not need re-proving at circuit level to support this phase's claim (that the corrected
statistic generalizes). A global drift also has no single "named" qubit, so W2c-style naming/localization
is not attempted here — it would need a localized (not global) injection to be meaningful.

**Pilot-then-freeze (per `06_W2_PHASE2.md` §1's declared relaxation).** T12a built the circuit-level
infrastructure and ran an internal pilot (seeds 500-504, small grid, `distance=3, rounds=5, p0=1/200,
p1=2*p0`): 40 detectors, declared/truth logical error rates ≈2.75%/≈9.1%, corrected witness detected at the
pilot's smallest tested N (50, in 5/5 seeds) while the baseline needed N=250 — roughly a 5x latency ratio
at pilot scale. The manager froze the main run's grid (`[10, 20, 50, 100, 250, 500, 1000, 2000]`, `n_seeds
=10`, `bootstrap_B=200`) and P8.1's bar (`N_det(witness) <= N_det(baseline)/2`, a conservative 2x — well
below the pilot's ~5x — to leave slack for seed variance and finer grid granularity) from these pilot
numbers, before T12b built the frozen runner. No prior-art or theorem anchors exist here (there is no
closed-form model at circuit level), so this whole phase's claim grade is `measured`, not `exact-finite`.

**Result.** The frozen main run (10 seeds, full grid) landed at exactly the registered boundary:
`N_det(witness)=50`, `N_det(baseline)=100`, ratio exactly `2.0` — P8.1 registered-positive, but by the
thinnest possible margin the discrete grid allows (the true continuous-N ratio could be anywhere the grid
can't resolve between the adjacent points 50 and 100). This is reported plainly in `REPORT.md` rather than
read as a comfortable win — the honest headline is "the corrected statistic clearly separates from the
baseline at circuit level, by at least ~2x," not "by ~5x" (that was the pilot's smaller-sample estimate).
P8.2 (null false-positive rate, both witness and baseline) passed cleanly at 0% for both.

**Why this is safe.** Nothing about E1-E7's verdicts is touched. The scope reductions are declared up front
(this entry), not discovered after an attempted broader run failed — T12a's packet stated them as scope
decisions before any code was written, and this entry is the required record.

---

## 2026-07-06 — E9 (Phase 3, closed-loop control): drift scenario corrected before any code was frozen,
epoch-discretized timeline instead of a continuous multi-round stream, two pilot-driven correctness fixes

**Drift scenario correction (found before T13a's packet was even written).** `06_W2_PHASE2.md` §5 implies
reusing E8's drift scenario for the control-loop demonstration. The manager checked this numerically first
and found it would not work: E8's drift is a **uniform** rescaling of all four noise channels, which gives
every edge in the pymatching decoding graph the same weight regardless of the specific rate — and
minimum-weight perfect matching's decision depends only on the *relative* weights across edges, so a
decoder rebuilt for the "correct" drifted rate (oracle) produces essentially the same predictions as a
stale one (manager measured a ~0.02% differing-prediction rate on a uniform 2x drift — no real gap to
demonstrate). Recalibration cannot show a benefit under a uniform drift, independent of witness quality.
**Fix:** E9 drifts one specific channel (`before_measure_flip_probability`, elevated 20x) while holding the
other three fixed, which does create heterogeneous edge weights; the manager verified this gives a genuine,
reproducible decoding gap (~11.75% vs ~9.25% logical error, static vs. oracle, at N=50000) before any E9
code was written.

**Epoch-discretized timeline instead of a continuous drifting round-stream.** `06_W2_PHASE2.md` §5's
"continuous round stream with a temporal drift point" would require hand-editing Stim circuit instructions
mid-stream (Stim's circuit generator has no native support for noise that changes partway through a
`rounds=` parameter). E9 instead discretizes time into `E_total` epochs, each an independent batch of
`shots_per_epoch` circuit-level shots drawn from the declared circuit (epochs before `drift_epoch`) or the
drifted circuit (epochs from `drift_epoch` on) — reusing T12a's existing per-shot sampling machinery
directly. This is declared as a simplification of "continuous stream," not an attempt at it; recalibration
still operates on real, physically meaningful noise-channel drift, just on a discretized clock.

**Recalibration model class is declared, not discovered.** The recalibration procedure (both "scheduled"
and "witness" policies) only ever searches over candidate values of the one channel known (by construction
of this experiment) to be drifting; it does not attempt to identify *which* channel changed. That
identification is what E7's naming step (W2c) already demonstrated separately — E9 isolates the *timing/
budget* question (when to recalibrate, at what cost) from the *naming* question, deliberately.

**Two pilot-driven fixes, both found and resolved before `e9.json` was frozen (logged for the record, not
because they represent an open issue).** (1) The witness policy's first design permanently disarmed itself
after its first trigger; 2 of 10 pilot seeds had a pre-drift false alarm (an expected ~13% whole-run false
alarm probability compounding from a per-epoch 1% rate over 15 pre-drift epochs — the same run-length vs.
per-test false-alarm-rate distinction E7's CUSUM machinery exists to handle, reintroduced in a new form
here) and would have stayed blind to the real drift for the rest of the run. Fixed to self-correcting:
recalibrate and keep monitoring, updating the comparison reference each time. (2) The first self-correcting
fix used a single noisy epoch's feature mean as the new reference, which — being far higher-variance than
the original `N_cal`-calibrated reference — caused near-constant spurious re-triggering (mean 26.7 recal
events per run). Fixed by properly re-calibrating the full `(theta_model, sigma, threshold)` triple from a
fresh `N_cal`-shot sample of the newly-adopted candidate circuit at every actual recalibration event
(cached per candidate value, since it is declared-model-conditional, not seed-conditional — the same
pattern already established for E7/E8's shared null-threshold calibrations).

**Pilot-then-freeze (per `06_W2_PHASE2.md` §1).** Pilot seeds 500-509 (`distance=3, rounds=9, p0=3/1000,
measure_multiplier=20, E_total=40, drift_epoch=15, shots_per_epoch=300`) gave: static post-drift error
0.11764, oracle 0.09284, witness 0.09329 (near-identical to oracle), scheduled at a *fixed-period* ~1-event
budget 0.10971, scheduled at higher unmatched budget (~8 events) 0.09639. P9.1's bar (witness within 0.01
absolute of oracle) and P9.2's bar (witness beats matched-budget scheduling) were frozen from these numbers
before `e9_control_loop.py` was written.

**Checkpoint-10 correction (independent review).** The first frozen run's `scheduled_matched` used a fixed global
period chosen to *average* about one recalibration event, but the witness policy's realized event count is
itself stochastic (occasional pre-drift false alarms add extra events) — the frozen run showed witness
averaging 1.6 events against scheduled_matched's fixed 1.0, a real ~60% budget mismatch that undermined
P9.2's "matched-budget" claim. Fixed: `scheduled_matched` now draws, per seed, exactly that same seed's
witness-policy realized event count of epochs (uniformly at random from the timeline, via that seed's own
RNG), giving an exact seed-by-seed event-count match (confirmed identical, e.g. `[1,1,2,2,1,1,3,2,1,2]` for
both policies on the frozen run) rather than a matched mean.

With this fix, the frozen main run (seeds 0-9, disjoint from the pilot range) gives: witness 0.0930 vs.
oracle 0.0916 (gap 0.0014, well inside the 0.01 bar — P9.1 registered-positive); scheduled-matched (now
genuinely budget-equal to witness, not just aggregate-mean-equal) 0.1115 (P9.2 registered-positive, gap
0.0185 — a real win for event-triggered timing over blind timing at truly equal recalibration budget);
scheduled-frequent (unmatched, ~5x witness's typical budget) 0.0946, reported descriptively (P9.3, no bar).
**Honest reading of P9.3, corrected per the independent review**: the gap between scheduled-frequent and witness
(0.0016) is smaller than the estimated paired standard error at 10 seeds (~0.002) — this is *not* a
resolved "witness still wins" result, it is statistically thin. The clean, resolved contrast is
scheduled-frequent vs. scheduled-matched (0.0946 vs 0.1115): spending several times the recalibration
budget on a blind schedule gets most of the way to witness/oracle performance, but this comparison does not
establish that witness beats a frequently-scheduled blind policy — only that it beats one at *equal*
budget (P9.2), which is the actually-registered, resolved claim. Pre-drift false-alarm rate on this seed
set came out 0.0 for witness (compare pilot's 0.2 — both are honest measurements of a genuinely
probabilistic event over a 15-epoch pre-drift window, not a contradiction) — reported descriptively (P9.4).

**Why this is safe.** No E1-E8 verdict is touched. The drift-scenario and epoch-discretization
simplifications are declared before code was written (this entry), not discovered after a broader attempt
failed. Both pilot-round fixes were resolved before `e9.json` existed — nothing frozen or reported rests on
the broken intermediate designs.
