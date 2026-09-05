# 06 — W2 Follow-Up: Corrected Syndrome-Only Witness, Circuit-Level Noise, Closed-Loop Control

Frozen design addendum, written by the manager, same discipline as `00_OVERVIEW.md`–`05_IMPLEMENTATION_PLAN.md`:
The implementation engineer implements, does not derive; a genuine disagreement between this document and running code is a
deviation to log in `DEVIATIONS.md`, never a silent edit here. This document does not reopen E2 — its
registered verdicts (`P2.1`–`P2.4`, including the `registered-negative` on W2) stand as committed history.
Everything here is additive: three new experiments, E7/E8/E9.

**Terminology note:** this document and everything built from it use experimental/scientific language
(hypothesis, method, mechanism, empirical demonstration) — not legal/patent framing — because the
repository and a paper are the primary output, not a filing. This is a documented shift from the framing
in the original motivation document (`INVENTION.md`, since removed) and `00_OVERVIEW.md`/`04_CONTROLS_AND_CLAIMS.md`, which are historical record and are
**not** being rewritten by this document.

---

## 0. Status and motivation

E2 (`design/03_EXPERIMENTS.md`) registered `P2.1` as `registered-negative`: the deployable, syndrome-only
witness W2 never detected the frozen drift injection within the tested sample grid, while the oracle
witness W1 achieved only a 2× latency improvement over the matched baseline, short of the registered 4×.
That result is honest and stands. This document designs the follow-up investigation:

1. **Diagnose** concretely why W2 underperformed (§2) — this turns out to be partly an implementation
   defect and partly a genuine structural fact about the specific drift scenario E2 froze, discovered
   below with exact computation, *before* any new code is written.
2. **Build a corrected syndrome-only statistic ladder** (§3, experiment E7) and test it honestly across a
   *range* of drift scenarios — not only the one E2 froze — because §2's own exact analysis shows that
   scenario sits close to the worst case for any syndrome-only method. The registered predictions in §3
   are conditioned on drift-scenario type and were derived from exact/measured numbers *before* writing
   the ladder's implementation, per house discipline.
3. **Extend to circuit-level noise on a larger code** (§4, experiment E8) — the realism the original E2
   setup did not have (E2 is code-capacity only, SURF(3), per `02_ARCHITECTURE.md` §9's own reserved
   "phase 2" hook).
4. **Close the loop with a demonstrated control action** (§5, experiment E9): witness fires → named drift
   → targeted decoder recalibration → measured logical-fidelity gain per unit recalibration budget,
   compared honestly against a periodic blind-recalibration alternative and against oracle/static bounds.

None of this is guaranteed to "win." §2's own math already shows the answer is scenario-dependent. The
registered predictions below say so explicitly, including one *registered expected negative* (§3, P7.3) —
a prediction of failure, committed in advance and backed by exact computation, is itself a rigor
demonstration, not a weakness, per this project's honesty-before-cleverness discipline.

## 1. Scope, non-negotiables, relaxed-exactness declaration

All non-negotiables from the build playbook (not part of this repository) and `00_OVERVIEW.md` §2 continue unchanged: no
hardware/Born-rule/Bell-theorem claims, no `Fraction`/`float` mixing inside one EXACT computation, no
dependency outside the frozen list, clean-room rule for the other `six-birds-*` repositories, manager-gated commits, no tuning
registered predictions to pass, no silent caps.

**Dependency clarification (not a new dependency):** Phase 2/3 (§4–§5) use `stim`'s built-in circuit
generator (`stim.Circuit.generated(...)`) and `pymatching.Matching.from_detector_error_model(...)`. Both
are standard, documented usage of the two dependencies already approved in `02_ARCHITECTURE.md` §1 — this
is not "vendoring" reference code; it is calling library APIs the way they are meant to be called. The
clean-room rule concerns the other `six-birds-*` repositories only.

**Declared scope relaxation (log to `DEVIATIONS.md` when Phase 2 lands):** Phase 0/1 (§2–§3) stay entirely
in the EXACT `Fraction` regime, exactly like E1–E6. Phase 2/3 (§4–§5) operate on circuit-level noise, where
no closed-form exact moment engine exists (a circuit has many distinct per-location error mechanisms, not
one simple per-qubit iid model) — "exact derivation before the run" is not available. It is replaced by:
**pilot-then-freeze**. A declared pilot seed range (disjoint from the frozen main-run seed range) is used
to estimate effect sizes; registered predictions are written down and frozen into the config *before* the
main run executes, exactly mirroring the existing discipline (predictions frozen before implementation) but
sourced from simulation instead of closed-form algebra. This is a scope fence to state plainly in
`REPORT.md`, not a silent downgrade.

This document does not modify E1–E6, their configs, or their committed artifacts.

---

## 2. Phase 0 — Diagnosis (EXACT, no new registered predictions)

Setup is identical to E2's (`design/03_EXPERIMENTS.md` §E2 "Setup"): SURF(3), declared = N2(p=3/100),
truth = N3(p=3/100, q=1/50) with a configurable injection pair. All computation here is EXACT
(`Fraction`), using `MomentEngine` and `xi_residual` exactly as E2 already does — nothing new is added to
the moment engine itself.

The manager has already run these computations directly against the installed package (same
pre-derivation discipline used for the E5 payoff-v2 study). The Phase 0 implementation packet **reproduces these as
pinned, tested values** — this is a verification task, not open research. If the implementation's numbers disagree with
the ones below, that is reported immediately as a discrepancy, never silently reconciled.

### Finding 1 — mean-shift discard

`streams._cov_hat` (`src/sbqos/streams.py:254`) centers before computing covariance
(`A0 = Af - Af.mean(axis=0)`), so `w2_witness` (built entirely from centered covariance blocks) is
structurally blind to any signal in the *mean* of the native checks. For the frozen E2 injection
(pair=(0,3)), the exact mean-shift vector Δmean_L = mean_L(truth) − mean_L(declared) is:

```
h0..h4: 0
h5:     -331776/9765625  (≈ -0.033974)      [h5 = the X-type check on qubits {3,4,6,7}]
h6, h7: 0
```

Exactly one of the eight native checks carries any first-moment signal, and today it is discarded whole.
‖Δmean_L‖² ≈ 0.001154 (Fraction-exact) — a real, currently-unused signal budget.

### Finding 2 — A*-lift compression

The second-moment signal ΔK_LL = K_LL(truth) − K_LL(declared) has ‖ΔK_LL‖_F² ≈ 0.003263 (Fraction-exact;
concentrated on h5's row/column). `w2_witness` (`src/sbqos/streams.py:159-168`) lifts this through the
coverage-optimal linear map A* (`A_star` from `xi_residual`, shape 2×8) via
`Delta_D = A_star @ Delta_LL @ A_star.T`. The lifted signal's energy drops to ‖Delta_D‖_F² ≈ 0.0000447 — a
**≈73× reduction**. A* was fit to minimize logical-*prediction* residual variance given L, not to preserve
*drift sensitivity*; the two objectives are different, and the current W2 conflates them by reusing A*.

### Finding 3 — mis-scaled null

`omega_stat` (`src/sbqos/streams.py:123-145`) calibrates Ω from the 99th percentile of the **W1**
statistic's λ_max (`blind_spot_witness(Xi_emp, Xi_model, ...)`, natural scale set by Ξ, an O(p)-order
quantity) under the declared-model null. `w2_witness` then thresholds a structurally different, far
smaller statistic (built from centered second moments of an O(p²)-order injection) against this same
borrowed Ω. Phase 0 must measure both statistics' own null 99th-percentile scales under the *identical*
null bootstrap shots and report the ratio directly.

### Finding 4 — drift-scenario dependence (drives §3's registered-prediction design)

The frozen E2 pair (0,3) is not a generic drift direction: qubits {0,3} are 2 of the 3 qubits in the
Zbar logical support ({0,3,6}) — i.e. the injection sits close to a minimum-weight logical failure by
construction. Using an exact technique — **the full 2⁸-outcome joint pmf of the native-check syndrome is
exactly recoverable via Walsh–Hadamard inversion**: evaluate `MomentEngine.mean()` at all 2⁸ XOR-combinations
of the 8 check vectors (each such XOR-combination is itself a valid `PauliVec`, and its mean is exactly the
corresponding Fourier/WHT coefficient of the syndrome-bit pmf; no sampling required) — the per-shot KL
divergence between the truth and declared full syndrome distributions is exactly computable, and comparable
against the per-shot KL divergence of the **logical-failure Bernoulli** (measured via seeded Monte Carlo
through the same `pymatching`-based adapter E2 already uses, `e2_drift_witness._MatchingAdapter`):

| Injection (ZZ pair) | Relation to logical support | syndrome KL/shot (exact) | logical-failure KL/shot (MC, N=2×10⁶, declared) | ratio (syndrome / logical) |
|---|---|---|---|---|
| (0,3) — the frozen E2 scenario | 2 of 3 qubits of Zbar | 0.006151 | 0.009247 | 0.665 |
| (2,5) | 1 qubit (2) touches Xbar; neither on Zbar | 0.010823 | 0.009841 | 1.100 |
| (4,8) | neither qubit on Xbar or Zbar | 0.051352 | 0.000066 | **773.4** |

This is a structural fact, not an artifact of implementation: drift that already sits near a minimum-weight
logical-failure path is inherently easier for the **logical-failure channel** to see (the failure channel
only fires when correction fails, and this drift directly feeds that failure mode), while the **syndrome
channel** is comparatively blind to exactly the low-weight combinations the code is built to correct. Drift
located away from minimum-weight failure paths is dramatically easier for the syndrome channel — up to
≈773× more per-shot information in this small grid. **The frozen E2 scenario was, by structural accident,
close to the worst realistic case for any syndrome-only method.** This fully explains, quantitatively, why
W2 registered negative — independent of, and in addition to, Findings 1–3's implementation defects.

### Phase 0 deliverable

A new module `src/sbqos/w2_diagnosis.py` (or a private submodule under `experiments/`, manager's call at
dispatch time) exposing:
- `signal_budget(declared_model, truth_model, L, D) -> dict` — returns Δmean_L, ‖Δmean_L‖², ΔK_LL,
  ‖ΔK_LL‖_F², the A*-lifted Delta_D and its ‖·‖_F², all EXACT (`Fraction` in, `float` only for the norms).
- `own_null_scale(code, model, L, D, N, B, rng, statistic) -> float` — 99th percentile of an arbitrary
  witness-statistic callable's value under declared-model null bootstrap shots (generalizes the existing
  `omega_stat` pattern in `streams.py` to accept a pluggable statistic instead of hard-coding W1's).
- `full_syndrome_pmf(engine, L) -> dict[tuple[int,...], Fraction]` — the Walsh–Hadamard inversion described
  in Finding 4 (2^len(L.vecs) keys; must assert probabilities sum to exactly `Fraction(1)` and are all
  `>= 0` — both are theorem-level sanity checks, add as asserts, not silent).
- `syndrome_kl(declared_pmf, truth_pmf) -> float` and a small helper computing the logical-failure Bernoulli
  KL from two measured rates.

**Tests (pinned, no new registered predictions — this is diagnostic, not a scored experiment):**
`test_w2_diagnosis_signal_budget` pins Finding 1/2's numbers to the values above (abs tol 1e-6 on the
floats; exact equality on the `Fraction`s). `test_w2_diagnosis_syndrome_kl` pins the three KL rows in
Finding 4's table (abs tol 1e-4, since the logical-failure KL depends on a seeded Monte Carlo — pin the
seed and shot count exactly as used above: `rng` seeds 123/456/hash-derived per scenario name, N=2,000,000,
reuse `sbqos.rng` and `e2_drift_witness._MatchingAdapter` directly — do not reimplement the adapter).
`test_w2_diagnosis_pmf_sums_to_one` is a property test over all three scenarios.

No independent-review checkpoint is required for Phase 0 alone (it is diagnostic, not a kernel or a scored experiment);
it is folded into the Phase 1 (checkpoint 8) review together with E7, since Phase 1's design depends on it.

---

## 3. Phase 1 — corrected syndrome-only statistic ladder + E7

### 3.1 The unifying object: the degree-≤2 Fourier/WHT vector

`moments.degree2_family(L)` already exists and already returns exactly what's needed: `L`'s native checks
plus all pairwise XOR products (36 probes total for SURF(3)'s 8 checks: 8 + 28). Each probe's mean under a
model is exactly a Walsh–Hadamard coefficient of the syndrome pmf for a subset of size ≤ 2 (Finding 4's
technique, restricted to weight ≤ 2). This single object subsumes both of today's defects:

- it includes the 8 degree-1 (mean-shift) coefficients that centered-covariance W2 discards (fixes
  Finding 1), and
- it is used **directly**, with no A*-style lift, so no compression happens (fixes Finding 2).

Let `F = degree2_family(L)` (36 probes). Define:
- `theta_model = [MomentEngine(declared, exact=True).mean(v) for v in F.vecs]` (36 exact `Fraction`s).
- The **estimator covariance** `Sigma_theta[i,j] = Cov(sigma_{F_i}, sigma_{F_j}) / N` (exact under the
  declared model via `MomentEngine.cov`; this is the standard sample-mean covariance of an iid vector of
  ±1 observables over N shots — valid because per-shot Pauli errors are iid across shots for N1–N3).
- The **observed vector** `theta_hat` = per-column empirical mean (no centering) of shots sampled with `F`
  passed as the `L`-role argument of the existing `sample_shots(code, model, F, D, N, rng)` — this requires
  no new sampling code. (Commutation note: since all native checks pairwise-commute and commute with the
  logicals, and symplectic pairing is F2-bilinear, `sympl(h_i ^ h_j, h_k) = sympl(h_i,h_k) ^ sympl(h_j,h_k)
  = 0` for any checks/logicals — the full 36+2-probe family still pairwise commutes, so the fast Stim MPP
  path in `sample_shots` applies unchanged for non-hidden models.)

### 3.2 Statistic ladder

- **W2a — same statistic, own-null calibration.** Unchanged `Delta_D = A_star @ (K_LL_emp − K_LL_model) @
  A_star.T` from today's `w2_witness`, but Ω calibrated as the 99th percentile of *this same statistic's*
  λ_max under declared-model null bootstrap (using Phase 0's `own_null_scale` helper), not W1's borrowed Ω.
  Isolates how much of the E2 negative was pure miscalibration (Finding 3) versus information (Findings
  1/2/4).

- **W2b — degree-≤2 quadratic (GLR-style) statistic.** `T = (theta_hat − theta_model)^T @ pinv(Sigma_theta)
  @ (theta_hat − theta_model)`, using `xi._pinv` (already exists, already handles the exact/float duality
  the project uses elsewhere) for the pseudo-inverse. Threshold calibrated via null bootstrap (same B,
  99th-percentile pattern as `omega_stat`) rather than an asymptotic chi-square table — consistent with the
  project's existing calibration style and avoids introducing an unverified asymptotic-normality claim.
  This statistic is a strict generalization containing degree-1 (mean-shift) and degree-2 (covariance)
  information in one full-rank object — no lift, no discard.

- **W2c — matched-filter dictionary (naming).** Build a small dictionary of physical drift directions: for
  each qubit q in 0..8, the exact directional derivative of `theta_model` with respect to a small Fraction
  perturbation of qubit q's total error rate (finite difference at a small exact `Fraction` step is
  sufficient — no need for symbolic derivatives). This gives 9 dictionary vectors d_q in the same 36-dim
  space as `theta_hat`. Detection stays W2b's `T`; **naming** is: whiten `(theta_hat − theta_model)` and
  each `d_q` by `Sigma_theta` (or its pinv square root), take the inner product, report `argmax_q`, and
  forward-map q to the logical direction whose Ξ is most sensitive to qubit q's rate (via
  `xi_residual`'s existing A*/Ξ machinery — reuse, do not reimplement). This replaces the old A*-lift naming
  mechanism (shown lossy by Finding 2) with a naming step that operates in the same full-rank space as
  detection.

- **W2d — sequential (CUSUM) version.** Convert W2b (and, symmetrically, the baseline) into a running
  test at a matched false-alarm rate: maintain `g_t = max(0, g_{t-1} + increment_t)`, alarm when `g_t`
  crosses a threshold calibrated via null Monte Carlo to a target false-alarm rate over the run length
  (not an asymptotic ARL formula — simulate the null and pick the threshold empirically, same house style).
  `increment_t` for the syndrome side is the per-shot contribution implied by W2b's quadratic form (e.g. a
  windowed recomputation, or an online running mean/covariance update — the implementer's choice,
  documented, as long as the null-calibration step is honest and matched between the two sides). The
  baseline gets the **same upgrade**: a CUSUM on the per-shot Bernoulli log-likelihood-ratio of logical
  failure at the declared rate. Both sides sequential, matched false-alarm rate — this is the honest
  apples-to-apples frame; a win here is attributable to information content, not test-design asymmetry.

### 3.3 Experiment E7 — corrected witness ladder across a drift-scenario grid

**Purpose.** Test the corrected syndrome-only ladder (§3.2) honestly across drift scenarios that span the
range Finding 4 already shows exists — including the original E2 scenario, where a *negative* result is the
registered, pre-derived expectation.

**Setup.** SURF(3). Declared = N2(p=3/100). Truth = N3(p=3/100, q=1/50) at three frozen injection pairs,
matching Finding 4's table exactly: `(0,3)` (on-support, the original E2 scenario), `(2,5)` (near-parity),
`(4,8)` (off-support). Reuse `e2_drift_witness._MatchingAdapter` for the baseline decoder unchanged.

**Procedure.**
1. For each of the three scenarios and each rung (W2a, W2b, W2c-detection, W2d): sweep the same `n_grid`
   as E2 (`[250, 500, 1000, 2000, 4000, 8000, 16000]`), 10 seeds each, compute `N_det` at
   `detect_seeds_required = 9` exactly as E2 does.
2. Baseline: both the original fixed-window binomial test (E2's, unchanged, for continuity) and its CUSUM
   upgrade (§3.2, W2d's baseline side).
3. Naming: at `N_det` for W2c, report the dictionary argmax and its forward-mapped overlap with the true
   injected logical direction (same `_naming_overlap` helper style as E2).
4. Null calibration: 50 seeded null runs (truth = declared) per rung, false-positive rate at the calibrated
   threshold.

**Registered predictions** (frozen from Finding 4's exact/measured numbers, before this packet is written):
- **P7.1** (own-null magnitude, quantifies Finding 3 directly): W2a's own-null 99th-percentile threshold is
  ≤ 10% of the borrowed Ω1 threshold used by today's `w2_witness`, measured on identical null bootstrap
  shots.
- **P7.2** (off-support scenario, pair (4,8)): `N_det(best rung among W2b/W2c/W2d) ≤ N_det(baseline)/10`.
  (Finding 4's exact KL ratio is ≈773×; the bar is set far more conservatively at 10× to leave slack for
  the gap between an asymptotic KL-based rate and finite-sample sequential-test behavior on a small grid —
  a report of the actual ratio achieved is required regardless of whether the 10× bar is cleared.)
- **P7.3** (the original E2 scenario, pair (0,3)) — **registered expected negative, stated in advance**:
  `N_det(any W2 rung)` is **not** expected to be ≤ `N_det(baseline)`; the registered prediction is that the
  ratio `N_det(W2)/N_det(baseline) ≥ 1` at this scenario, consistent with Finding 4's syndrome/logical KL
  ratio of 0.665 (< 1). If a rung unexpectedly beats baseline here, that is reported as a registered
  positive surprise, not quietly folded into P7.2's framing.
- **P7.4** (near-parity scenario, pair (2,5)): descriptive only — report `N_det` ratios for all rungs; no
  pass/fail bar (Finding 4's KL ratio ≈1.1 predicts near-parity, and "near" has no principled numeric bar
  without a bigger pilot; this keeps the registration honest rather than inventing a threshold post hoc).
- **P7.5** (naming): on the off-support scenario (where detection is expected to succeed, P7.2), W2c's
  dictionary argmax names a qubit within the true injection pair in ≥ 8/10 seeded detecting runs, and the
  forward-mapped logical-direction overlap is ≥ 0.6 (same bar E2 used for W2's naming target).
- **P7.6** (null calibration): false-positive rate ≤ 2% across 50 seeded null runs, for every rung, matching
  P2.3's existing bar.
- **P7.7** (sequential vs. fixed-window symmetry, descriptive): report `N_det` for W2d and the CUSUM
  baseline alongside their fixed-window counterparts; no pass/fail bar — this is a sanity report confirming
  the sequential upgrade was not applied asymmetrically.

**Controls.** Null calibration (P7.6) is the null battery item; same-scenario-grid discipline (no scenario
added or dropped after seeing results); E2's original scenario is retained unchanged as a scenario, not
replaced, specifically so P7.3's registered-negative is directly comparable to E2's own P2.1 verdict.

**Outputs.** Detection-latency curves per scenario (3 panels, same style as E2's single panel); a
scenario × rung table of `N_det` and ratio-to-baseline; the KL table from Finding 4 reprinted alongside the
measured ratios for direct comparison; naming overlap bar chart for the off-support scenario.

---

## 4. Phase 2 — circuit-level noise on a bigger code (E8)

This is the "phase 2" hook `02_ARCHITECTURE.md` §9 already reserved. Registered predictions here are
**pilot-then-freeze** (§1's declared relaxation) — this section specifies the architecture and procedure
precisely; the manager will fill in frozen numeric bars from a pilot run before E8's main run executes, and
log that pilot→freeze step in `DEVIATIONS.md`.

**Setup.** Use `stim.Circuit.generated("surface_code:rotated_memory_z", distance=d, rounds=T,
after_clifford_depolarization=p, before_round_data_depolarization=p, after_reset_flip_probability=p,
before_measure_flip_probability=p)` for d ∈ {3, 5}, T rounds (T on the order of a few×d, pilot-determined).
This is standard-library stim usage (§1's dependency clarification), not a new dependency. "Declared" =
this circuit at frozen parameters. "Truth" = the identical circuit topology with one drift injected
partway through the round count: either (a) one specific qubit's `after_clifford_depolarization` scaled up,
or (b) one specific measurement's `before_measure_flip_probability` scaled up — both are physically
motivated, standard circuit-level drift scenarios. Detector outcomes come from
`circuit.compile_detector_sampler().sample(shots=N)` (boolean array, columns = detectors); convert to ±1
via `1 - 2*bits`, exactly as `streams.sample_shots` already does for code-capacity detectors.

**Statistic generalization.** The degree-≤2 WHT/GLR object from §3.1 generalizes directly: build
`F = detectors ∪ (pairwise XOR of detectors)`, but **locality-sparsify** the pairwise part to detector pairs
that are graph-neighbors in the circuit's matching graph (spatially/temporally close) — an unrestricted
pairwise family over O(d²·T) detectors is not the scaling story this experiment wants, and the no-silent-
caps rule requires logging exactly how many pairs were dropped and why (graph-distance cutoff, declared in
config). No closed-form `MomentEngine.mean()` is available at circuit level (no simple per-qubit iid
model), so `theta_model` and `Sigma_theta` are themselves estimated from a large declared-model calibration
sample (mirroring `omega_stat`'s existing bootstrap-calibration pattern, just estimating the mean/covariance
instead of assuming it closed-form) — this replaces exact derivation with measured calibration, per §1's
declared relaxation.

**Baseline.** `pymatching.Matching.from_detector_error_model(circuit.detector_error_model(decompose_errors=True))`
— standard pymatching usage, replacing E2's hand-built SURF(3)-specific `_MatchingAdapter` (which doesn't
generalize past code-capacity). Logical error rate per shot, same binomial/CUSUM detection framing as E7.

**Procedure.** Mirror E7's structure: a small drift-scenario grid (at least one "near a logical failure
path" and one "away from it," by analogy with Finding 4, now defined via detector-graph distance to the
logical observable's support rather than qubit-membership in a fixed logical row/column); `N_det` sweep for
best-rung-W2′ vs. upgraded pymatching baseline, both at matched false-alarm rate; null calibration; naming
(which physical location, forward-mapped to which detector-graph region is most Ξ-sensitive).

**Predictions.** To be frozen from a pilot run (declared pilot seed range, e.g. seeds 500–509, disjoint
from the main run's seeds 0–9) before the main E8 run executes; template mirrors P7.1–P7.6 but with
pilot-derived numeric bars instead of exactly-derived ones. This pilot→freeze step and its resulting
numbers are logged verbatim in `DEVIATIONS.md` when this phase lands — this is the honest replacement for
"pre-derive from closed form" when closed form does not exist.

**Cost/scaling report (measured, not asserted).** Report actual wall-clock and detector-pair counts for
d=3 vs d=5, with and without locality-sparsification, so the scaling claim in any eventual paper is a
measurement, not an assumption.

---

## 5. Phase 3 — closed-loop control (E9)

**Purpose.** The single result that would matter most for a paper's practical-impact section: witness
fires → names a drift → triggers a *targeted* decoder recalibration → measured end-to-end gain in logical
fidelity per unit recalibration budget, compared against the obvious alternative (periodic blind
recalibration) and bracketed by static/oracle bounds.

**Setup.** Circuit-level surface code (matching E8's main configuration, e.g. d=3), a long round stream
with a single drift injected partway through (same injection style as E8). Four decoder policies, compared
over the post-drift window:

1. **Static** (floor): the pre-drift `pymatching.Matching`, never updated.
2. **Oracle** (ceiling): `pymatching.Matching` rebuilt immediately at the drift point from the *true*
   post-drift DEM (requires knowing the injected drift exactly — not deployable, defines the ceiling only).
3. **Scheduled** (the honest competitor): `pymatching.Matching` rebuilt every K rounds from a moving-window
   empirical recalibration — refit per-edge weights from the standard detector-pair-correlation estimator
   (`weight_ij = log((1 − p_ij)/p_ij)` from the empirical pairwise flip-correlation in the window; this is
   established practice for DEM calibration, implemented from scratch here, not sourced from a sibling
   repo). This is the control that keeps the whole exercise honest: if (3) matches (4) at equal budget, the
   witness mechanism is not what delivers the value, and that must be reported plainly.
4. **Witness-triggered** (ours): the E8 witness runs on a sliding window; when it fires, run the *same*
   recalibration procedure as (3), but only then, and — because the witness names a location — restricted
   to reweighting only the edges implicated by the named drift rather than the full matching graph. This
   targeting (few edges, from few post-trigger shots) is the mechanism that should let (4) approach (2)
   while spending less budget than (3).

**Metric.** Logical error rate per round in the post-drift window (primary), plotted against
**recalibration budget** = total number of shots consumed by any recalibration fit across the window
(this is the resource both (3) and (4) spend; (1) spends none, (2) is unconstrained/oracle). The registered
endpoint is comparative: **(4) achieves logical fidelity within X% of (2)'s ceiling while spending ≤ Y% of
(3)'s budget to do so** — X and Y pilot-derived and frozen before the main E9 run, per §1's relaxation, and
logged in `DEVIATIONS.md`.

**Controls.** (3) at *matched* budget to (4) is the mandatory comparison (not just (3) at its own natural
schedule) — this isolates whether targeting, not just recalibration itself, is doing the work. A "do
nothing extra" null (1) sets the floor. Report the case where (3) matches (4) as plainly as the case where
it does not — this experiment's honest value is in showing which one holds, not in assuming the answer.

**Outputs.** Logical-error-rate-vs-round curves for all four policies through the drift point; a
budget-vs-fidelity frontier plot (all four policies as points/curves); a table of the registered X/Y bars
and the measured values.

---

## 6. Architecture additions (summary; full contracts inline above per phase)

New modules: `src/sbqos/w2_diagnosis.py` (Phase 0, §2), and additions to `src/sbqos/streams.py` for the
degree-≤2 statistic family, own-null calibration generalization, and CUSUM helpers (Phase 1, §3) — these
are additive functions, not edits to existing E1–E6-facing signatures (`w1_witness`, `w2_witness`,
`omega_stat` keep their current signatures; new functions sit alongside them). New experiment runners:
`src/sbqos/experiments/e7_witness_ladder.py`, `e8_circuit_level.py`, `e9_control_loop.py`, each following
the existing `main(config_path) -> None` / `main_template` convention (`02_ARCHITECTURE.md` §5). New
configs: `src/sbqos/configs/e7.json`, `e8.json`, `e9.json`. New `CONFIG_SCHEMAS` entries in `artifacts.py`
for `"e7"`, `"e8"`, `"e9"` (follow the existing literal-schema-dict pattern exactly — see `e2`'s entry for
the closest analog). Formulas stay in modules, procedures in experiments, thresholds in configs — same
layering rule as `02_ARCHITECTURE.md` §5.

`e7.json` schema sketch (fill exact keys at packet time): `experiment`, `seed`, `surf3_p`, `inject_q`,
`inject_pairs: [[int,int]]` (the three scenarios), `n_grid: [int]`, `n_seeds: int`, `bootstrap_B: int`,
`null_runs: int`, `detect_seeds_required: int`, `baseline_model_shots: int`, `cusum_null_runs: int`.

`e8.json`/`e9.json` schemas are written at their own packet time once pilot numbers exist (§4/§5's
pilot-then-freeze step is itself part of the packet, not pre-work the manager does alone this time, since
it requires running the not-yet-built circuit-level sampling code).

---

## 7. Implementation plan

Sequential, same discipline as `05_IMPLEMENTATION_PLAN.md`. Continues the existing independent-review checkpoint numbering
(1–7 already closed at the original T9 final close).

### T10 — Phase 0 diagnosis (small)

Build `w2_diagnosis.py` per §2's deliverable. Reproduce Findings 1–4 as pinned tests. No experiment runner.

**Accept:** `test_w2_diagnosis_signal_budget`, `test_w2_diagnosis_syndrome_kl`,
`test_w2_diagnosis_pmf_sums_to_one` all pass with the pinned values in §2. Manager independently spot-checks
at least one pinned value by re-running the manager's own script before accepting.

### T11 — Phase 1 statistic ladder + E7 (large)

Build §3.1's degree-≤2 vector machinery (reusing `degree2_family`, `MomentEngine`, `xi._pinv`), the four-rung
ladder (§3.2), and `e7_witness_ladder.py` (§3.3). This is the load-bearing packet of the whole document —
consider splitting into two implementation packets (ladder machinery in `streams.py`; then the E7 runner) at the
manager's discretion, same as the original T8 splitting convention.

**Accept:** all of §3.3's registered predictions P7.1–P7.7 computed and given a verdict (including P7.3's
expected negative — verify it is reported as `registered-negative` or `registered-positive` honestly,
whichever the run actually produces, not forced); `reproduce_all` includes e7; manifests verify.

**Independent-review checkpoint 8** — after T10+T11 together (diagnosis + corrected ladder + E7; the single largest and
most novel piece of this document, reviewed as one unit since T10 directly justifies T11's design).

### T12 — Phase 2 circuit-level (E8) (large)

Build circuit-level sampling (`stim.Circuit.generated`, detector streams), the locality-sparsified
degree-≤2 generalization, the pymatching-DEM baseline, and `e8_circuit_level.py` per §4. Includes the
pilot→freeze step (run pilot seeds, derive numeric bars, freeze into `e8.json`, log to `DEVIATIONS.md`) as
part of this packet.

**Accept:** pilot→freeze step documented in `DEVIATIONS.md` with the pilot seed range and resulting frozen
bars; main E8 run's registered predictions given verdicts against those frozen bars; cost/scaling numbers
reported (d=3 vs d=5, with/without sparsification).

**Independent-review checkpoint 9** — after T12.

### T13 — Phase 3 closed-loop control (E9) (large)

Build the four decoder policies, the recalibration procedure (edge-weight refit from empirical pairwise
detector correlations), the witness-triggered targeting, and `e9_control_loop.py` per §5. Includes its own
pilot→freeze step for the X/Y bars.

**Accept:** all four policies compared at matched budget where required (the (3)-vs-(4) matched-budget
control is mandatory, not optional); registered X/Y bars given verdicts; the honest outcome reported either
way (targeting helps, or scheduled recalibration matches it — both are acceptable results, only a skipped
comparison is not).

**Independent-review checkpoint 10 — final close for this document.** Whole-addendum pass before proposing a commit;
update `REPORT.md` with a new section covering E7/E8/E9 (using scientific, not patent, framing per §0);
update `DEVIATIONS.md` with both pilot→freeze entries; confirm `reproduce_all` covers e7/e8/e9 alongside
e1–e6 and passes twice in a row.

---

## 8. Acceptance checklist (mirrors `04_CONTROLS_AND_CLAIMS.md` §5, scoped to this document)

- [ ] `pytest` green including all new T10–T13 tests; `w2_diagnosis` tests pass with pinned values matching
  §2 exactly.
- [ ] `python -m sbqos.reproduce_all` regenerates e7/e8/e9 artifacts with matching manifests, twice in a row.
- [ ] Every registered prediction P7.1–P7.7 (and E8/E9's pilot-frozen equivalents) has a verdict in
  REPORT.md, including P7.3's registered-expected-negative reported honestly regardless of outcome.
- [ ] Null battery items reused/extended: protocol-trap N/A here (no schedule to internalize in these
  experiments), same-family saturation N/A, null-model calibration (P7.6 + E8/E9 equivalents) — present,
  proxy failure N/A, slack regime N/A, no-silent-caps (E8's locality-sparsification drop count logged),
  trivialization guard N/A, same-support discipline (E7's fixed three-scenario grid, no post-hoc edits).
- [ ] No dependency outside the frozen list; `stim.Circuit.generated`/`pymatching.Matching.
  from_detector_error_model` usage confirmed as standard library calls, not vendored code.
- [ ] EXACT paths (Phase 0, Phase 1's `theta_model`/`Sigma_theta` construction) contain no float arithmetic
  before the point where FLOAT is declared to begin (the null-calibration/bootstrap steps, same as existing
  E2 FLOAT scope) — grep audit documented in REPORT.md alongside the existing EXACT-path audit.
  DEVIATIONS.md has two new entries: Phase 2 pilot→freeze, Phase 3 pilot→freeze — both complete with pilot
  seed ranges and resulting frozen numbers.
