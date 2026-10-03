# Mathematics and mechanization audit

This audit reviews the mathematics and executable certificates behind SBQOS.
The manuscript and its supporting files under `paper/` are deliberately unchanged.
The review is in progress: repairs to the core arithmetic and closure machinery
do not yet establish completion of the experiment and claim audit.

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
in mode 0. The noise kernel itself accumulates errors; recovery/prototype
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

## Repairs and regression evidence

| Issue | Repair | Evidence |
|---|---|---|
| Pricing enumeration rounded every residual and cost before optimizing. Marginals could disappear, and an infeasible cost `1 + 10^-30` could round to 1. | Exact engines retain Fraction values through traces, costs, maxima, and shadow-price differences. E6 exports rational twins and numeric copies. | Exact rational value curve, budget-boundary, small-marginal, and E6 rational-serialization tests. |
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
| Identity probes were legal mathematically but the commuting Stim path could not measure them. | Use classical character sampling when a constant probe is present. | Identity outcomes and empirical covariance are exactly constant and zero respectively. |
| A zero-variance test used a nonzero cross covariance, violating joint covariance positivity. | Give the test a realizable zero cross covariance. | Correct zero-variance residual regression. |

## Outstanding experiment and theorem coverage checks

The following findings require continued work before the audit can be closed.
They are not a completed approval of the current experiments.

1. **E5 observation likelihood mismatch.** `_syndrome_likelihood` groups the
   3-bit signature with indices `(0,4), (1,2), (5,6), (3,7)`, whereas the
   syndrome integer supplied by `_payoff_hidden` corresponds to consecutive
   pairs `(0,1), (2,3), (4,5), (6,7)`. The former catalog includes logical-bit
   information and is not the sensor actually supplied to the update. At the
   frozen defaults, the correct mode-0 syndrome law is
   `(1801/1875, 74/5625, 74/5625, 74/5625)` and the mode-1 law is
   `(553/625, 24/625, 24/625, 24/625)`. Both the old and corrected one-step
   updates remain on their initial side of 1/2 at these parameters; the
   negative payoff result may therefore survive the repair. This must be
   checked by rerunning, not assumed.
2. **E5 minimality and exact-filter scope.** A deterministic rounded-belief
   automaton is exact for its declared packaging rule; it is not thereby the
   predictive quotient of the original HMM. Check the exported machine's
   readout, reachable nodes, and minimality relative to that readout. The old
   deviations text's universal assertion that no finite catalog can be closed
   is false: a singleton stationary distribution is already closed. A
   nontrivial obstruction needs the appropriate premises. The current
   implementation does not establish those premises or a general obstruction.
3. **E5 rounding control and scoring protocol.** Prototype-grid endpoints
   currently use the exact filter's beliefs from the entire scored trajectory.
   Check and repair this information leak. Preserve frozen historical findings
   and distinguish corrected scores and protocols. Check the filter's initial
   prior against the generator's declared initial mode. Comparisons scored on
   different windows need explicit scope.
4. **Predictive gap readout.** `Delta^max` is a separation of two possible
   probability vectors. The implied unavoidable uniform prediction error is
   at least `Delta^max / 2`, not `Delta^max`: one common prediction can lie at
   their midpoint. The paper will need this small mathematical correction in
   its later editing phase. Check exported readouts and finite-catalog scope.
5. **Statistical witnesses.** An empirical bootstrap percentile is a
   calibration estimate, not a distribution-free guarantee of 1% false
   positives. Check independent null trials, reused calibration, singular
   covariance support, sequential versus per-window rates, and the actual
   information supplied to each baseline and naming procedure.
6. **Circuit control experiment.** Check causal use of epoch batches,
   retrospective per-seed budget matching, candidate-cache behavior, oracle
   scope, and error-bar calculations. Verify frozen E8 and E9 configurations,
   not only their reduced smoke tests.
7. **Artifact and claim coverage.** Regenerate affected default experiments
   twice, compare old and new numeric results and registered verdicts, verify
   manifests, and reconcile all C-01 through C-39 statements with executable
   evidence. A fresh manifest written by a runner only proves internal file
   integrity; it does not independently prove agreement with the release
   evidence or mathematical correctness.

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
thread-count setting is part of this verification's scope. Broader default
experiment and claim verification remains unfinished. Historical default outputs were copied to
`.codex/mathematics-audit/release-artifacts/` before regenerating them; this
ignored local directory is for the ongoing comparison, not a published
evidence artifact.
