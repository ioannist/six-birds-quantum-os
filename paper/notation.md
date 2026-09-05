# Notation Table

Maps every code-level name that will appear in results/claims to a paper symbol. Rule for Phase B: prose
uses only the paper symbol; the code name goes in a footnote or parenthetical on first use only, never
repeated. Grouped by the SBT primitive each symbol belongs to (matches `paper/narrative.md`'s mapping
figure, F1).

## Coverage audit (adequacy residual / Ξ) — primitive [XI]

| code name | paper symbol | meaning | first used |
|---|---|---|---|
| `K_LL`, `K_DL`, `K_DD` | $K_{LL}, K_{DL}, K_{DD}$ | covariance blocks of scheduled-check / logical ±1 observables | §2 |
| `xi_residual` / Ξ | $\Xi(D\mid L)$ | adequacy residual: logical information invisible to the linear span of L | §2 |
| `A_star` | $A^\*$ | coverage-optimal linear map, $A^\* = K_{DL}K_{LL}^{+}$ | §2 |
| `discharge` | $\Delta_M$ | marginal residual discharge of adding candidate family $M$ | §2 |
| chain rule identity | $\Xi(D\mid L\cup M) = \Xi(D\mid L) - \Delta_M$ | exact marginal-value decomposition | §5 |
| `blind_spot_witness` (`lam_max`, `z`) | $\lambda_{\max}(\Xi-\Omega),\; z$ | blind-spot witness eigenvalue/eigenvector | §2, §5 |
| `omega_stat` / `Omega` | $\Omega$ | null-calibrated threshold matrix | §5, §7 |
| `degree2_family` | $L^{(2)}$ | native checks + all pairwise XOR products (degree-$\le$2 feature family) | §7 |
| `W1` (oracle witness) | $\mathcal{W}_{\text{oracle}}$ | blind-spot witness computed with the true model (not deployable) | §6, §7 |
| `W2` (original deployable witness, E2) | $\mathcal{W}_{\text{dep}}$ | the original syndrome-only witness that registered negative in E2 | §6, §7 |
| `W2a`/`W2b`/`W2c`/`W2d` (corrected ladder, E7) | $\mathcal{W}'_{\text{a-d}}$ | corrected witness rungs: own-null recalibration / degree-$\le$2 quadratic GLR / matched-filter naming / CUSUM sequential | §7 |
| `theta_model`, `sigma_theta` | $\theta_{\mathrm{model}},\; \Sigma_\theta$ | exact mean vector of $L^{(2)}$ under the declared model and its estimator covariance $\Sigma_\theta = \operatorname{Cov}(F)/N$; the hatted $\hat\theta$ is the *empirical* mean (Eq. W2b) | §7 |
| `w2_prime_statistic` (circuit-level) | $T'$ | degree-$\le$2 quadratic statistic generalized to Stim detector streams | §7 |
| `N_det` | $N_{\det}$ | smallest sample size with detection in $\ge 9/10$ (or $4/5$ pilot) seeds | §6, §7 |

## Existence / closure audit — primitive [F1], [CAST]

| code name | paper symbol | meaning | first used |
|---|---|---|---|
| `delta` | $\delta$ | idempotence defect of the packaging operator $E$ | §2 |
| `epsilon` | $\varepsilon$ | retention error (probability of leaving the correctable coset) | §2 |
| δ ≤ ε (T-IC-02) | $\delta \le \varepsilon$ | theorem-anchored decoder-agnostic stability bound | §5 |
| `CD_tau` | $CD_\tau$ | closure deficit, $I(X_t; Y_{t+\tau}\mid Y_t)$ | §2, §5 |
| `route_mismatch` (`RM`) | $RM_\tau$ | evolve-then-decode vs. decode-then-evolve mismatch | §2, §5 |
| `Delta_pred` | $\Delta_{\text{pred}}$ | out-of-sample predictive gap (seeded rollout) | §5 |
| `multiplicity` | mult. | number of stable logical prototypes at tolerance | §2, §5 |  <!-- 2026-09-05: symbol changed from μ, which the paper reserves for carrier distributions (Eq. packaging) -->
| existence status | `certified` / `degrading` / `non_closed` / `trivialized` | typed existence-certificate status | §5 |

## Memory audit (predictive quotients) — primitive [HOL]

| code name | paper symbol | meaning | first used |
|---|---|---|---|
| `Q`, `M` | $Q, M$ | predictive quotient and minimal-machine state counts | §5 |
| `witness_count` | $\lvert\text{Wit}\rvert$ | number of predictive-quotient witnesses | §5 |
| `max_fiber` | $\text{MaxFiber}$ | largest fiber cardinality over the quotient map | §5 |
| `delta_max` (`Δ^max`) | $\Delta^{\max}$ | exact worst-case predictive-quotient gap | §5 |
| `currentization_search` | — | search for a minimal exposing-observable set (currentization) | §5 |
| `internalize_schedule` | — | random-scan lift folding an external schedule into state | §5 |
| protocol-trap classification | `genuine_memory_after_internalization` / `artifact_trap` | [PT]-style classification outcome | §5, §6 |

## Pricing audit — primitive [SPEND]

| code name | paper symbol | meaning | first used |
|---|---|---|---|
| `V(b)` / `V_exact` | $V(b)$ | value curve over budget $b$ (greedy / exact enumeration) | §5 |
| `lambda(b)` | $\lambda(b)$ | shadow price, $V(b{+}1)-V(b)$ | §5 |
| `b_star` | $b^\*$ | slack point | §5 |
| proxy costs | — | permuted-cost negative control | §5 |

## Circuit-level / closed-loop control (§7 only — no exact closed form; all measured)

| code name | paper symbol | meaning | first used |
|---|---|---|---|
| `p0` | $p_0$ | declared per-channel error probability | §7 |
| `p1` (E7/E8) | $p_1$ | truth/drifted error probability (or elevated channel rate) | §7 |
| `distance`, `rounds` | $d, R$ | surface-code distance, circuit rounds (Stim) | §7 |
| `cusum_detect` (`g_t`, `baseline`, `threshold`) | $g_t,\; b,\; h$ | one-sided CUSUM statistic, baseline, alarm threshold | §7 |
| `E_total`, `drift_epoch` | $E, e^\*$ | total epochs, epoch at which the drift begins | §7 |
| decoder policies | `static` / `oracle` / `scheduled_matched` / `scheduled_frequent` / `witness` | paper names: floor / ceiling / budget-matched blind schedule / high-budget blind schedule / targeted witness-triggered policy | §7 |
| `calibration_curve`, `nearest_candidate` | — | empirical candidate-rate lookup used for decoder recalibration | §7 |
| `recalibration_events` | $B$ (budget) | number of recalibration events spent by a policy | §7 |

## Grade vocabulary (not a symbol table, but must stay consistent — see `paper/claims.md` header)

`theorem-anchored`, `exact-finite`, `measured`, `registered-positive`, `registered-negative`,
`interpretation`. Rendered in the paper as small-caps or a fixed inline style (e.g. `\textsc{measured}`),
consistently, every single time a grade is stated — never as plain prose ("this was measured").
