# Mathematics and mechanization audit

This audit reviews the mathematics and executable certificates behind SBQOS.
The manuscript and its supporting files under `paper/` are deliberately unchanged.
The mathematical and executable review is complete for the declared finite
models and frozen E1–E9 configurations. Corrections needed in the later
paper-editing phase are recorded below rather than applied to the manuscript.

The starting worktree was clean at `98e09d7`. Commit `52c0aa9` records the
requested checkpoint before review. There are no Lean sources, Lake project,
or Lean toolchain in this repository; the mechanizations here are Python exact
computations and floating or sampled experiments. This is a self-review, not an
independent-agent review.

## Mathematical premises and verified constructions

The moment engine represents Pauli detection characters on a finite error
space. Their product is the character of the XOR of the two Pauli vectors.
Independent qubit probabilities give the product formula for expectations;
an independent correlated injection multiplies it by its own character
expectation. Existing brute-force tests independently enumerate the error law
and compare first and second moments in rational arithmetic.
The SURF(3) and SURF(5) distances are now checked by exhaustive pure-X and
pure-Z support searches below the declared distance. For CSS codes, any
undetected mixed logical error has an undetected logically nontrivial pure
component of no greater weight, so this proves the full Pauli lower bound.
The declared logical representatives attain the matching upper bounds. REP(d)
protects the X sector at distance d; as a quantum stabilizer code its
unprotected Z sector has distance 1. The experiments correctly restrict their
protected REP+N1 target to the Zbar detection character.

For centered random vectors L and D, joint covariance is a Gram matrix in
the finite weighted L2 space. Consequently its off-diagonal block satisfies
the range condition required for a singular Schur complement. Projection of
D onto the span of L gives

`Xi = K_DD - K_DL K_LL^+ K_LD`.

This is the covariance of the best **affine estimator's residual**. It is not
generally the conditional covariance given L. Zero Xi means almost-sure affine
coverage under the declared law. Nonzero positive semidefinite Xi means some
direction has a gap; positive definiteness is a stronger assertion. Product
features can remove gaps that singles cannot. On REP(3), the two syndrome bits
and their product, together with the affine intercept, span all functions on
the four syndrome values. Thus the complete ladder's residual equals the
conditional-mean MMSE, rather than the binary MAP error probability. Both
quantities in the MMSE comparison are `47291/1715000` at the frozen defaults.

Residualizing an extension M against L and projecting onto that residualized
span proves the chain rule. Repeating an existing feature adds no span and
discharges zero. The singular projection, optimal residual, and chain-rule
statements were checked against the actual definitions and theorem discussion
in the local `Adequacy Residuals and Blind Spot Currency` source, not just its
theorem names. The pseudoinverse tests now check all four Penrose identities
as rational equalities before doing the secondary NumPy comparison.

For row distributions, the cycle is `E = P^tau Agg Expand`. `Agg` is the
deterministic lens and `Expand` is the declared prototype lift. Its corrected
prototypes lie in the corresponding lens fibers; for hidden models they start
in mode 0. That reset is a declared mathematical completion, not a physical
procedure for clearing leakage. The noise kernel itself accumulates errors; recovery/prototype
packaging occurs in E. It should not be identified with continuous recovery
after every step of P. If w is the macro distribution after one cycle, then
the next defect is a convex mixture of prototype defects. Stochastic lifting
contracts total variation, yielding `delta <= epsilon`. The maximum over
point masses suffices by convexity. This is the finite specialization of the
actual retention theorem T-IC-02 in `Foundations of Emergence Calculus`.
Multiplicity is a separate condition, correctly needed by the broken-decoder
control.

Closure deficit uses micro-to-macro rows R and their conditional fiber averages.
For a weighting law mu, its KL loss is `I_mu(X; Y_next | Y_now)`. Decomposing
loss against any macro kernel K gives the deficit plus the mu-weighted KL
divergence from the fiber average to K. This proves the variational minimum.
Zero deficit or route mismatch gives equal rows **on mu's support**. A
full-state lumpability conclusion additionally requires full support. Finite
horizon weighting is a law at a declared time; it does not create a stationary
law or a stationary stream estimate for the latching process.

The Markov signature coordinates are independent symplectic linear forms.
Nondegeneracy of the symplectic pairing therefore makes the signature map
surjective: every represented signature has a physical Pauli preimage. The
builder now rejects dependent coordinates, wrong dimensions, and tracked
logicals that fail to commute with checks, before constructing a model.

For pricing, projection onto a larger feature span cannot increase the exact
residual trace. Nested budget-feasible sets make the exhaustive optimum V(b)
monotone. The reported lambda is a discrete finite difference, not a continuous
KKT multiplier, and these finite set functions need not be concave. Once the
budget covers all candidates the exhaustive curve saturates. Such saturation
does not mean Xi is zero or binary decoding is perfect. The greedy curve is a
computed feasible lower bound; the SURF(3) comparison is a finite experiment,
not a universal greedy approximation guarantee.

## Repairs and regression evidence

| Issue | Repair | Evidence |
|---|---|---|
| Pricing enumeration rounded every residual and cost before optimizing. Marginals could disappear, and an infeasible cost `1 + 10^-30` could round to 1. | Exact engines retain Fraction values through traces, costs, maxima, and shadow-price differences. E6 exports rational twins and numeric copies. | Exact rational value curve, budget-boundary, small-marginal, and E6 rational-serialization tests. |
| Greedy selection ranked exact discharges and accumulated costs through floats. | Keep the argmax, stopping comparison, and budget accumulation rational on exact engines; convert only display logs. | Unequal exact signals with equal float values select the truly better candidate; costs `1/2 ± 10^-30` remain jointly feasible at budget 1. Default E3/E6 order and verdicts remain unchanged. |
| Chain-rule discrepancy subtracted already-rounded float matrices. | Subtract and take the maximum in rational arithmetic on the exact path. | An injected `10^-30` fault must be detected exactly. |
| E3's exact-MMSE verdict compared rounded floats at a tolerance. | Compare rational trace directly to independently enumerated rational MMSE and export the trace fraction. Ignore probability-zero syndrome cells in conditional enumeration. | Frozen fraction equality and deterministic endpoint tests. |
| E1's exact saturation assertion cast the discharge to float first. | Check every exact matrix entry directly. | Existing saturation and experiment tests. |
| Exact stationary weights were inferred from an approximately uniform floating eigenvector. | Prove uniform stationarity by exact column sums. | Identity-chain and `10^-30` nonuniformity tests. |
| Closure loss indexed macro rows with raw label numbers. Prototype lifting did the same with micro states. | Map labels to rows and locate corrected prototypes by their declared syndrome and decoded label. | Reversing and renaming labels to 10 and 20 leaves all four audits invariant. |
| KL was evaluated even at zero-weight fibers, where the conditional law is undefined. | Skip zero-weight states; return infinite loss for positive mass outside candidate support. | Horizon-zero closure and infinite variational-loss tests. |
| Finite future catalogs do not automatically satisfy the refinement premise of the predictive-quotient theorem. | Expose a checked canonical M-to-Q comparison map; retain the existing Q-to-incident-M diagnostic as `pi_map`. | An erasure continuation separates the two claims. The local Holonomy with Memory source uses identity continuations to establish refinement. |
| Quotient calculations could accept truncated vectors, invalid probability laws, invalid effects, or nonstochastic kernels. | Validate exact package dimensions, mass, positivity, effect range, and catalog references. Validate phase kernels and alpha before internalization. | Invalid-package and invalid-phase regression cases. |
| Transport could be asked to certify an arbitrary supplied partition. | Require the supplied partition to be the actual declared predictive quotient. | Incorrect-partition rejection and existing genuine transport tests. |
| Hidden transition and injection probabilities outside [0,1] were accepted. | Reject nonstochastic parameters at construction. | Negative and greater-than-one probability tests. |
| Artificial signature states could be built from dependent or noncentral coordinates. | Validate signature independence, dimensions, and tracked logical commutation. | Three invalid-coordinate tests; existing brute-force transition cross-checks still pass. |
| Identity probes were legal mathematically but the commuting Stim path could not measure them. | Use classical character sampling when a constant probe is present. | Identity outcomes and empirical covariance are exactly constant and zero respectively. |
| A zero-variance test used a nonzero cross covariance, violating joint covariance positivity. | Give the test a realizable zero cross covariance. | Correct zero-variance residual regression. |

## E5 repairs and measured results

The sensor mismatch was repaired by marginalizing the least-significant
logical signature bit. On cumulative-error trajectories, successive syndrome
XOR gives the actual fresh-noise syndrome supplied to the Bayesian update;
the known initial state is not treated as an emission. The orbit diagnostic
starts at the known mode-0 prototype, and impossible observations do not
manufacture a posterior. Hand-derived syndrome probabilities and a directly
enumerated two-observation Bayes calculation independently test these bridges.

N5's originally omitted identity tests caused an actual refinement failure:
its latched histories from different current cells merged under future bit
marginals. Adding explicit identity/current tests restores the canonical map
in the hidden-model packages. N5's M count is now 8 rather than 5, while its
four witness pairs, MaxFiber 2, and `Delta^max = 539/1250` are unchanged. All
five E5 quotient packages now export a defined M-to-Q map. The exported
unavoidable uniform prediction error lower bound is `Delta^max / 2`, not the
full separation. A common midpoint predictor shows why the factor 1/2 is
necessary.

The eight-node product automaton is not minimal for future prediction. Exact
partition refinement now supplies a minimal automaton for the declared
**quantized** next-syndrome predictions: two states across the two possible
initial prototypes, and one reachable predictive state at the frozen initial
prototype. The last-syndrome coordinate is redundant for that output. This is
a substantive finite-machine certificate with an explicit readout, not an
application of the exact-HMM predictive-quotient theorem to a rounded belief.
A control changing a transition while preserving immediate outputs requires
additional predictive classes, testing the future-behavior part of the
construction. The old universal no-finite-catalog assertion is false; a
stationary singleton is a counterexample. No general obstruction is assumed
by the repaired machine.

The rounding grid is fitted on the first half of each trajectory, and all
predictors are scored on the same held-out second half. The unrounded Bayesian
filter uses the generator's known initial mode. Future outcomes cannot change
the fitted grid; a suffix-replacement test checks this. These measured
numbers replace the old mixed-window, full-trajectory-fitted scores:

| Operating point | Bayes filter NLL gain | Mode-oracle NLL gain | Run-length K=8 NLL gain | Rounding K=16 NLL gain |
|---|---|---|---|---|
| Frozen defaults | 0.001899330369036667 | 0.0109105513868889 | 0.0008050817401397681 | -0.004430769225456321 |
| Loud mode | 0.036477072500171515 | 0.05823578044354516 | 0.010518443617859585 | 0.028088355247030794 |

The gains are nats per scored round. Memory payoff remains positive, small-K
rounding remains negative, and the loud K=16 point remains positive. All
predictors here read the declared full round signature, including the logical
increment; they are not syndrome-only deployable decoders. The analytic oracle
ceiling is a stationary information-theoretic quantity, whereas the reported
oracle gain is a finite-sample measurement; their difference is now diagnostic
rather than an assertion that every finite sample is within a fixed tolerance.
Legacy accuracy scores and all four registered E5 verdicts are unchanged.

W2 also now accepts a native record without oracle logical observations. Its
covariance and value are unchanged; the new test checks equality of the
statistic with and without the oracle record. The A-star lift is a declared
drift statistic, not a theorem that every syndrome change implies a logical
residual change.

## Statistical and circuit model scope

The 99th-percentile bootstrap is an empirical calibration estimate. It does
not guarantee a population false-positive rate of exactly 1%. E2 and E7 use
null samples distinct from their calibration samples, and E7 reports W2b's
measured 6% null rate as a registered failure. Shared calibration across seeds
is declared. A CUSUM threshold is calibrated for the maximum over its stated
finite run length; per-window thresholds and whole-run false alarms are
different quantities. The original borrowed-threshold W2 is preserved as the
historical failed control; W2a and W2b supply the re-registered own-null repairs.
The qubit naming dictionary is a finite-difference, signed matched-filter
model. Its qubit-level naming failure is preserved, and overlap with a
two-dimensional logical direction does not establish unique physical
localization.

The quadratic statistics are pseudoinverse seminorms; no unconditional power
or chi-square-null theorem is claimed. For the frozen code-capacity family,
positive Pauli probabilities give full syndrome support and distinct Walsh
features, hence a nonsingular population covariance. For the circuit models,
exact GF(2) elimination on the declared detector error patterns gives ranks
40/40 at 5 rounds and 72/72 at 9 rounds. This verifies full detector span for
these positive-noise models, not a claim that a finite empirical covariance
cannot have sampling or conditioning problems. Their moments, pseudoinverses,
and null thresholds remain measured floating quantities.

E4's held-out order-1/order-2 NLL gap estimates a lag-one **macro-history**
information gain in a stationary limit, not the micro-to-macro closure
deficit itself. For N5 the long rollout can wash out the finite-horizon law
used by CD. Its registered correlation is the coefficient of the declared
model/horizon table, with repeated proxy values across tau and a strong N5
contribution; it is not a sample of independent model draws or a theorem
identifying the two information quantities. The reported negative correlation
without N5 remains essential.

E9 adapts to a completed epoch's detector batch before decoding that same
batch. The candidate choice uses detector statistics, not logical truth.
This is legitimate batch decoding, with the declared batch latency; it is
not a controller that chooses all decoding parameters before receiving that
epoch's syndromes. The matched blind schedule is an offline counterfactual
with a uniformly sampled set of times and the witness's realized event count
supplied retrospectively. It matches the declared **event-count** budget,
not every computational or calibration cost. Its independently generated
timeline is not the same trajectory as the witness policy's. The model-known
MWPM decoder is an oracle comparator, not a proof of a globally optimal
decoder or a pointwise ceiling on measured error rates. The frequent-policy
contrast remains unresolved at the reported error scale.

The old pilot rationale asserting invariance under uniform rate rescaling
is false as a mathematical statement. In the actual distance-3 circuits,
rescaling 0.005 to 0.01 produces nonconstant edge-weight ratios from
0.7641786105624969 to 0.8948484550610394 at 5 rounds, and essentially the
same range at 9 rounds. Choosing the heterogeneous E9 drift is justified
by the pilot's larger observed effect, rather than a general impossibility
theorem for uniform drift. This correction leaves the actual experiment intact.

## Claim coverage and later manuscript corrections

This table covers every identifier in the frozen `paper/claims.md`. A
registered verdict means the current computation against the frozen bar;
it does not independently establish the historical time of registration.

| Claims | Evidence and strongest supported scope |
|---|---|
| C-01, C-03 | Implemented residual, closure, quotient, trap, and pricing paths are substantive computations. E2's failed witness is followed by the declared diagnosis, E7 corrected ladder, E8 circuit test, and E9 control loop. Interpretation of that arc is separate from the computed results. Certified deformation bridges remain outside the implementation. |
| C-02, C-22, C-23 | All 25 original and 14 follow-up entries have verdicts, including the measured follow-up rows; 14 of the original 25 are negative. Every verdict agrees with the archived release. The registered bars and model parameters were not tuned during repair. Historical freeze-before-implementation chronology cannot be independently reconstructed from this repository's single release commit. The files declare that provenance. |
| C-04, C-05 | The residual certifies an affine feature class in a stochastic Pauli model. It does not prohibit nonlinear decoders. Circuit evidence uses Stim sampling; no hardware or coherent-quantum theorem is obtained. |
| C-06, C-07 | Singular projection and retention premises are checked above against the imported theorem texts. Rational chain-rule checks now measure rational discrepancies. Lumpability conclusions are support-relative unless the weighting law has full support. |
| C-08, C-09, C-12 | E1 exact traces, all declared single-check ablations, and duplicate saturation agree with the release. E3 saturation also remains exact. |
| C-10, C-11 | REP(3)'s complete degree-2 feature readout attains the conditional-mean MMSE `47291/1715000` exactly. This is squared-error estimation, not MAP success. SURF(3)'s registered greedy comparisons hold over the tested budget/baseline grid only. |
| C-13, C-14 | E4 baseline has `delta = 57159/8000000`, `epsilon = 29/4000`, multiplicity 2; the broken control has exact delta 0 and multiplicity 1. The p-sweep's defect-only label must retain the stated distinction from the full classifier. Hidden-mode prototype reset is mathematical packaging. |
| C-15 | E4's registered correlation and the negative without-N5 correlation persist. The macro-history proxy, repeated rows across tau, and finite-horizon limitations described above preclude a theorem identifying the proxy with CD. |
| C-16, C-17 | Exact witness pairs and gaps remain unchanged. Identity/current tests now make all E5 packages genuinely refine Q; N5's M cardinality becomes 8. Currentizing the mode dissolves the surplus as registered. A uniform prediction error lower bound is half the witness gap. |
| C-18, C-19 | Memory still has positive measured NLL payoff; small-K rounding is still negative, and loud K=16 is positive. Replace the old numeric shares and scores with the held-out values above. At frozen defaults K=2 is now the worst rounding score, so the old assertion that K=4 is worst must change. State the full-signature observation scope. |
| C-20 | Internalization preserves four witnesses; the artifact hypothesis remains a registered negative. This is a successful classification computation, not evidence of a trap catching an artifact. |
| C-21a, C-21b | Exhaustive exact-engine curves and their marginals are rational. Other greedy/logical consequences retain their measured grade. All four pricing predictions remain negative. Discrete pricing has the scope described above. |
| C-24 | E2's original W2 remains a registered negative; W1 and the baseline retain their detection ordering. W2 now requires only the native observations used by its formula. |
| C-25, C-26, C-27 | Diagnosis calculations and independent diagnosis tests support the exact mean shift and numerical energy compression. Float energies and the compression ratio do not acquire a rational grade. The borrowed-threshold mechanism is verified in the implementation. |
| C-28a, C-28b | Walsh inversion gives the finite syndrome law from exact character moments; KL uses numerical logarithms. Logical-channel KLs are measured and seed-dependent. The two seed sets must retain the inventory's explicit distinction. These are scenario diagnostics, not a general impossibility bound for syndrome detectors. |
| C-29, C-30, C-31, C-32 | E7 preserves the failed calibration-scale prediction, off-support detection at N=1000, original-scenario baseline 1000 versus corrected 4000, failed physical naming, and W2b's 6% null FPR. Naming and overlap have the distinct scope explained above. |
| C-33 | Full E8 retains W2 detection 50 versus baseline 100: precisely 2x at the discrete boundary. Preserve the margin caveat; calibration is empirical. |
| C-34, C-35, C-39 | Full E9 retains witness-oracle gap `0.0014266666666666733`, matched-schedule advantage about `0.0184667`, and identical per-seed event counts `[1,1,2,2,1,1,3,2,1,2]`. The frequent-schedule gap about `0.0016267` is below the standard error of seedwise differences about `0.00202374`, so remains unresolved. Candidate-cache use does not supply logical truth to selection. Preserve the single-known-channel, batch-decoding, retrospective event-budget, and model-known MWPM comparator scopes. |
| C-36 | Correct the old float-chain-rule exception: exact discrepancy subtraction is now rational. Blind-spot eigenvectors, display values, generic stationary eigensolvers, numerical logarithms, and sampled circuit quantities remain floating. There is no Lean proof project to certify. |
| C-37 | All nine committed default configurations were rerun twice with byte-identical covered files in the stated environment. The current suite supersedes the historical 170-test count. Hash integrity, reproducibility, and mathematical validity are separate checks. |
| C-38 | Pilot and scored seed ranges and frozen bars match the implemented E8/E9 protocol. The deviations file includes these repairs and a correction to the old uniform-drift rationale. Chronological provenance has the same limit as C-02. |

The later paper phase must update E5 scores/window and descriptive percentages,
the scoped machine minimality, N5's M count, the factor 1/2, the exact arithmetic
description and current verification counts. Its exclusion of fitted macro
models needs to distinguish exact closure certificates from the measured E5
payoff of trained tables. Replace any unconditional covariance, oracle-ceiling,
uniform-drift invariance, or universal finite-catalog obstruction wording with
the scopes above. These changes do not require a material downgrade to the
main contribution or registered results. No paper files are changed here.

## Verification record

The unmodified suite passed: `170 passed in 134.17s`. After the first core
repairs, the targeted pricing, quotient, residual, and closure suite passed:
`68 passed in 4.29s`. The complete suite with the additional core regressions
passed: `195 passed in 110.80s`. E1, E3, E4, and E6 were each regenerated twice
with their committed default configs, with `OPENBLAS_NUM_THREADS=1` and
`OMP_NUM_THREADS=1`. All covered files were byte-identical between the two
runs, and their manifests verified. Every registered verdict in those four
experiments matched the release outputs. E3 adds its rational trace; E6 adds
rational curve twins and removes intermediate rounding. Floating outputs in
other fields can differ at final bits from the release environment: the
thread-count setting is part of this verification's scope. Historical default outputs were copied to
`.codex/mathematics-audit/release-artifacts/` before regenerating them; this
ignored local directory is for the release comparison, not a published
evidence artifact.

E5 was also regenerated twice at its committed default configuration with
the same thread settings. All covered files were byte-identical and its
manifest verified. Compared with the archived release output, all witness
pairs, witness gaps, legacy payoff values, and registered verdicts were
unchanged. The E5 repair suite passed a full run of 200 tests before the
additional surface-distance, transition-refinement, and oracle-free W2 tests;
the latter passed a subsequent full run of 204 tests.

E2, E7, E8, and E9 were then each run twice at their full committed defaults.
All covered files repeated byte-identically, all manifests verified, and all
registered verdicts matched the archived release. E3 and E6 were run twice
again after the final exact greedy-selection repair, with unchanged order and
verdicts. A final suite run includes all new arithmetic, coordinate-domain,
distance, quotient, causal-scoring, minimization, and oracle-free regressions;
passed: **209 passed in 134.69s**, using
`OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/pytest -q`.
A final separate pass verified all nine manifests, equality of the persisted
configs to the archived release, and every original/follow-up verdict. No
files under `paper/` differ from the pre-review checkpoint.

The adversarial self-review separately checked the bridges most likely to
smuggle stronger conclusions: affine versus conditional residual, realized
versus formal signature states, support versus full-state lumpability, current
versus future partition refinement, quantized versus exact HMM state, gap
versus prediction error, fit versus score window, and measured comparator
versus optimal decoder. Counterexamples and genuine transition/precision
ablations now exercise the repaired boundaries. This is an executable finite
audit with theorem-premise review, not an independently reviewed formal proof
of a universal quantum error-correction result.
