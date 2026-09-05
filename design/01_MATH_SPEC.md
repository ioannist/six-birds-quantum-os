# 01 — Mathematical Specification

Every object the prototype computes, with exact formulas and paper references. The implementing agent must treat this document as normative: if code and this document disagree, this document wins.

Paper references use file paths under `six-birds-papers/` (symlinked at repo root). Abbreviations:

- **[F1]** `Tsiokos_2026_Six_Birds_Foundations_of_Emergence_Calculus.tex`
- **[F3]** `Tsiokos_2026_Six_Birds_Foundations_III_A_Finite_Audited_Interaction_Calculus_for_SBT.tex`
- **[XI]** `Tsiokos_2026_Adequacy_Residuals_and_Blind_Spot_Currency.tex`
- **[NK]** `Tsiokos_2026_Emergence_IS_the_Needle_Killer.tex`
- **[HOL]** `Tsiokos_2026_Holonomy_with_Memory_in_Six_Birds_Theory_Predictive_Quotients_Witnesses_and_Fixed_Support_Route_Transport.tex`
- **[PT]** `Tsiokos_2026_Six_Birds_Protocol_Trap_Holonomy_Without_Entropy_Production.tex`
- **[NG]** `Tsiokos_2026_Six_Birds_No_Go_Theorems_for_Audited_Emergence.tex`
- **[CAST]** `Tsiokos_2026_To_Cast_a_Stone_with_Six_Birds_A_Closure_Deficit_Account_of_Randomness_under_Packaging_and_Budget.tex`
- **[XOR]** `Tsiokos_2026_To_XOR_a_Stone_with_Six_Birds_Closure_Diagnostics_for_Emergent_Bits_Gates_and_Booleanity.tex`
- **[SPEND]** `Tsiokos_2026_To_Spend_a_Stone_with_Six_Birds_Currency_Constraint_Duality_and_Shadow_Prices_Across_Closure_Layers.tex`
- **[QM]** `Tsiokos_2026_A_Six_Birds_Eye_View_of_Quantum_Theory_Operational_Closure_Semantics_for_Measurement_Contextuality_and_Record_Stability.tex`
- **[HID]** `Tsiokos_2026_Hiddenness_as_a_Structural_Law_of_Emergence.tex`

---

## 1. Codes and error spaces

### 1.1 Stabilizer codes used

Exactly three codes; do not add others.

1. **REP(d)** — classical repetition code protecting against X (bit-flip) noise, d ∈ {3, 5}. Data qubits: d. Checks: h_i = Z_i Z_{i+1}, i = 1..d−1. Logical: X̄ = X_1...X_d detected by Z̄ = Z_1 (any single Z acts as the logical readout functional; use Z on qubit 1). Number of logical bits k = 1. `code.logicals = (X̄, Z̄)` for structural uniformity with every other code (matching the general "2k logical reps" statement in §2 below) — but note that under N1 (which never produces Z or Y content), X̄ is a dead, zero-variance observable: `mean(X̄)=1` and `cov(X̄,·)=0` identically, since N1 has no Z-content for X̄ to detect. **Any experiment building a dissolving/logical probe family `D` for REP+N1 must select `code.logicals[1:]` (Z̄ only)** — including X̄ would add a degenerate dimension carrying no information, not an error, but pointless clutter in every downstream Ξ/covariance computation. (Flagged during T1/T2 review, 2026-07-04 — this is a documentation clarification of already-ambiguous prose, not a change to the frozen formulas.)
2. **SURF(3)** — rotated surface code, distance 3: n = 9 data qubits, 4 X-checks, 4 Z-checks, k = 1. Use the standard rotated-lattice layout; hard-code the check supports in `codes.py` as explicit qubit-index lists (write them out; do not generate programmatically). Logical X̄ = X on the 3 qubits of one row; logical Z̄ = Z on the 3 qubits of one column.
3. **SURF(5)** — same, distance 5 (n = 25). Only used in E3 and E6 scaling checks; everything must run with SURF(3) alone if compute is tight.

### 1.2 Symplectic representation

A Pauli error on n qubits (modulo phase) is e = (e^x | e^z) ∈ F_2^{2n}. A check or logical observable is likewise a = (a^x | a^z) ∈ F_2^{2n}. The **detection bit** of observable a on error e is the symplectic pairing

```
⟨a, e⟩ := a^x · e^z + a^z · e^x   (mod 2)
```

(a Z-type check a = (0|a^z) detects the X-part of e, etc.). Syndrome of e = vector of ⟨h_i, e⟩ over all checks; logical flip vector = ⟨λ_j, e⟩ over the 2k logical representatives — this is always structural and always length 2k for every code, **including REP** (`code.logicals`/`logical_flips` return both X̄ and Z̄ for REP too, not just Z̄). The "just Z̄" guidance in §1.1 applies only to which slice of `code.logicals` an *experiment* should feed into a `D` (dissolving/logical) probe family for REP+N1 — it is not a statement about `logical_flips`'s own return shape, which stays uniform across codes. (Clarified 2026-07-04 per the independent reviewer checkpoint-1 re-review finding.)

### 1.3 Noise models

All are **stochastic Pauli, code-capacity** (one error draw per shot; no measurement error except where a model says so). Each model is a named frozen object:

- **N1 (iid bit-flip p):** each qubit independently gets X with prob p, else I. Used with REP.
- **N2 (iid depolarizing p):** each qubit gets X, Y, Z each with prob p/3, else I. Used with SURF.
- **N3 (N2 + correlated pair injection):** N2 plus, with prob q, apply Z⊗Z on one fixed adjacent data-qubit pair (q₁, q₂) — an *unmodeled* channel for drift experiments; the declared model believes N2.
- **N4 (hidden-mode drift):** a hidden mode variable m_t ∈ {0, 1} evolving as a 2-state Markov chain (switch prob s per round, default s = 0.02); in mode 0 noise is N2(p₀), in mode 1 noise is N2(p₁) with p₁ = 3·p₀. The mode is *not* observable. Used for closure-deficit and decoder-memory experiments.
- **N5 (latching leakage proxy):** one designated qubit ℓ has a hidden latch: initially normal; each round it latches with prob r (default 0.01); once latched, that qubit's noise becomes fully depolarizing (p = 3/4 · uniform X/Y/Z) forever. Classical proxy of leakage.

Default parameters (frozen in configs): p = 0.05 (REP), p = 0.03 (SURF code-capacity), q = 0.02, p₀ = 0.02.

---

## 2. The ±1 observable calculus and moment engine (EXACT-capable)

This is the computational heart of the Ξ audit. **Ref: [XI] :: probe-family currency; the covariance instantiation is our declared bridge** (see §4.6 scope note).

### 2.1 Observables

For any a ∈ F_2^{2n} define the ±1 random variable over the noise distribution P(e):

```
σ_a(e) := (−1)^{⟨a, e⟩} ∈ {+1, −1}
```

Key identity (used everywhere): **σ_a · σ_b = σ_{a⊕b}** (pointwise, since pairings add mod 2).

### 2.2 First moments, independent noise

For independent per-qubit noise with per-qubit distribution p_i over {I, X, Y, Z}:

```
E[σ_a] = ∏_{i=1}^{n} m_i(a),   m_i(a) = Σ_{P ∈ {I,X,Y,Z}} p_i(P) · (−1)^{⟨a_i, P⟩}
```

where a_i is the restriction of a to qubit i and ⟨a_i, P⟩ is the single-qubit symplectic pairing. Worked values the unit tests must reproduce (derive once by hand and hard-code as expected values):

- a acts as Z on qubit i (detects X and Y): m_i = 1 − 2(p_X + p_Y). Under N2(p): m_i = 1 − 4p/3.
- a acts as X on qubit i (detects Z and Y): m_i = 1 − 2(p_Z + p_Y) = 1 − 4p/3 under N2.
- a acts as Y on qubit i (detects X and Z): m_i = 1 − 2(p_X + p_Z) = 1 − 4p/3 under N2.
- a acts as I on qubit i: m_i = 1.
- Under N1(p), a = Z on qubit i: m_i = 1 − 2p.

For **N3**, the correlated term is handled by conditioning: E[σ_a] = (1−q)·E_{N2}[σ_a] + q·(−1)^{⟨a, z_{q₁}⊕z_{q₂}⟩}·E_{N2}[σ_a] where z_{q₁}⊕z_{q₂} is the injected ZZ error's symplectic vector (the injection composes with independent N2 draws; pairings add, so the factor pulls out).

All of these are rational numbers when the p's are rational ⟹ the EXACT path uses `Fraction`.

### 2.3 Second moments and covariance blocks

For probe families given as lists of vectors: native family L = [h_1..h_m] (checks currently scheduled), logical family D = [λ_1..λ_{2k}], candidate extensions M = [μ_1..μ_r]:

```
K_LL[i,j] = Cov(σ_{h_i}, σ_{h_j}) = E[σ_{h_i ⊕ h_j}] − E[σ_{h_i}]·E[σ_{h_j}]
K_DL[i,j] = E[σ_{λ_i ⊕ h_j}] − E[σ_{λ_i}]·E[σ_{h_j}]
K_DD[i,j] = E[σ_{λ_i ⊕ λ_j}] − E[σ_{λ_i}]·E[σ_{λ_j}]
```

(and analogously K_MM, K_DM, K_ML). Every entry is a closed-form product via §2.2 — **no sampling is needed for model-side moments.**

### 2.4 Degree-2 feature extension (the "nonlinear ladder")

A degree-2 feature is σ_{h_i ⊕ h_j} for i < j, i.e. the parity product of two checks — a *derived probe*, treated as a new probe vector h_i ⊕ h_j. The family `L2(L)` = L ∪ {h_i⊕h_j : i<j}. This realizes the strict-native-extension mechanism of the chain rule ([XI] :: chain rule / strict native extension) inside a fixed measurement set: products are genuinely new features (σ_{a⊕b} is NOT a linear function of σ_a, σ_b), while a *repeated* check is linear and must show exactly zero discharge ([XI] :: same-family saturation). E3b uses this ladder.

---

## 3. Adequacy residual Ξ, witness, chain rule

**Ref: [XI] :: adequacy residual; blind-spot witness; chain rule; same-family saturation. Also [NK] :: T3 adequacy interface, T14 strict-extension repair contraction.**

### 3.1 Residual

```
Ξ(D|L) := K_DD − K_DL · K_LL⁺ · K_LD
```

where K_LL⁺ is the Moore–Penrose pseudoinverse. FLOAT path: `numpy.linalg.pinv(K_LL, rcond=1e-12)`. EXACT path: compute over `Fraction` by (i) finding a maximal linearly independent subset of rows of K_LL via exact Gaussian elimination, (ii) solving the normal equations on that subset. Ξ must be symmetric PSD; assert `min eigenvalue ≥ −1e-9` (float) / assert PSD via exact LDL^T signs (exact, optional — a float eigencheck on the Fraction-to-float cast is acceptable).

Optimal explanation map (the "linear decoder" / GLS map, [XI] :: optimal native explanation): `A_star = K_DL @ K_LL⁺`.

### 3.2 Blind-spot witness

Given a declared residual budget Ω (PSD matrix, default Ω = ω·I with scalar ω in config):

```
Δ_Ξ := Ξ(D|L) − Ω
witness exists  ⟺  λ_max(Δ_Ξ) > 0
witness vector z := unit eigenvector of Δ_Ξ for λ_max     ([XI] :: blind-spot witness theorem)
witness magnitude := λ_max(Δ_Ξ)
```

Report both z (in the logical-observable basis, labeled by logical operator names) and λ_max.

### 3.3 Chain rule and discharge (marginal value of a candidate check)

For candidate family M (one or more probe vectors), conditional blocks:

```
K_MM|L := K_MM − K_ML K_LL⁺ K_LM
K_DM|L := K_DM − K_DL K_LL⁺ K_LM
discharge(M | L, D) := K_DM|L · (K_MM|L)⁺ · (K_DM|L)ᵀ          — a PSD matrix on D-space
value(M) := tr(discharge(M|L,D))
```

**Chain-rule identity (must be unit-tested):** `Ξ(D | L∪M) = Ξ(D|L) − discharge(M|L,D)` up to numerical tolerance 1e-10 (float) or exactly (EXACT path). Ref: [XI] :: chain rule (Crabtree–Haynsworth iterated Schur).

**Saturation test (must be unit-tested):** if M = {h} with h already in L (duplicated check), then `discharge = 0` exactly (EXACT path) / ≤ 1e-10 (float). Ref: [XI] :: same-family saturation. **This is the *only* saturating case for single-Pauli ±1 observables — do not generalize it to "M is an F2/GF(2)-linear combination of L's raw Pauli vectors" (e.g. `M = h_i ⊕ h_j`).** §2.4 above already states the reason explicitly: `σ_{a⊕b}` is a *product* of `σ_a, σ_b` in the ±1 domain, which is generically **not** a real-linear combination of them, so an XOR-combined probe is generically a genuinely new (degree-2) feature with *positive* discharge, not a saturated one — conflating GF(2)-linear-combination-of-binary-vectors with real-linear-combination-of-±1-observables produced exactly this error in an implementation packet on 2026-07-05 (caught at independent-review checkpoint 2); if you are about to write a test asserting an XOR-combined probe saturates, re-read this paragraph first.

### 3.4 Greedy check selection

`select_checks(L₀, D, candidates, budget)`: repeatedly add `argmax value(M)/cost(M)` among remaining candidates until budget exhausted or `max value < tol_stop` (config, default 1e-8). Log the full ranked list each round. This implements the acquisition rule of the curiosity law (see the companion notes `THEOREMS.md` §E9 of the six-birds-cognition repository, not included here, which designates the Xi chain-rule contraction as the acquisition numerator).

### 3.5 Empirical covariances and the drift witness (two tiers)

- **W1 (oracle witness, simulation-only):** estimate all blocks (K̂_LL, K̂_DL, K̂_DD) from N shots where the true error e is known to the simulator (Stim or the internal sampler), so σ_λ values are available. Compute `Ξ_emp` and `Δ = Ξ_emp − Ξ_model − Ω_stat` where Ω_stat is a statistical allowance (see below). Witness = top eigenpair of Δ. **Label all W1 outputs `oracle`** — deployability is not claimed.
- **W2 (syndrome-only witness, deployable-shaped):** only K̂_LL is estimable in the field. Define the syndrome-covariance defect `Δ_LL := K̂_LL − K_LL^model` and its lifted logical impact estimate `Δ_D := A_star · Δ_LL · A_starᵀ`. Witness = top eigenpair of Δ_D (after subtracting Ω_stat). E2 validates W2 against W1.
- **Statistical allowance Ω_stat:** from B = 200 bootstrap resamples of the shot set, compute the null distribution of λ_max under the declared model (simulate the model itself with matched N); set Ω_stat = (empirical 99th percentile of null λ_max) · I. This calibrates the false-positive rate at 1% by construction. Document N and B in every artifact.

### 3.6 Scope fence (verbatim into report)

> The prototype's Ξ is the conditional covariance of logical ±1 observables given scheduled-check ±1 observables (optionally augmented with degree-2 products). Ξ = 0 certifies exact coverage by the linear estimator class over the declared feature family; Ξ ≻ 0 certifies a coverage gap for that class and prices it. It does **not** assert that no nonlinear decoder covers the gap. The degree ladder (E3b) shows the residual contracting as feature degree grows, which is the framework's own account of what nonlinear decoding buys ([XI] chain rule; [CAST] budgeted-randomness curve).

Additional note the agent must not "fix": for any stabilizer code at code capacity, there exist zero-syndrome errors with nontrivial logical action (the logical operators themselves), so a naïve F_2 kernel-inclusion test Ker L ⊆ Ker D always fails. The meaningful statement is the noise-weighted one above — logical operators are high weight, hence exponentially suppressed in the covariances. Do not implement a global kernel test; a *bounded-weight* kernel test (errors of weight ≤ t) is used only as a unit-test sanity (05_IMPLEMENTATION_PLAN, task T3 tests).

---

## 4. Existence audit: cycle operator, δ, ε, RM, CD_τ

### 4.1 The Markov cycle model

For each (code, noise, decoder) triple build a finite Markov chain:

- **State space Z:** error cosets. For REP(d): e ∈ F_2^d (X-error indicator per qubit), |Z| = 2^d. For SURF(3) code-capacity with N2: e ∈ F_2^{2n} reduced modulo the stabilizer group — represent a state as (syndrome s, logical class c) ∈ F_2^{m} × F_2^{2k} where c is the logical coset label relative to a fixed canonical representative per syndrome (compute canonical representatives once via minimum-weight lookup; for d=3 the full table has 2^8 syndromes — enumerate). For hidden-mode models (N4, N5), the state is (coset, hidden mode).
- **Kernel P:** one QEC round = apply one noise draw (composition of the current error with a fresh error; cosets compose by ⊕ of symplectic vectors, syndromes and logical classes update accordingly), then (for the "cycle" operator only) apply recovery.
- **Lens f:** the decoder lens — f(state) = decoded logical frame (apply the frozen decoder to the syndrome; the macro label is the resulting logical class estimate), or the plain syndrome lens where an experiment says so. For hidden-mode models the mode is NOT in the lens image (it is hidden).
- **Prototypes u_x:** for macro label x, the canonical distribution the recovery step produces: point mass on (corrected canonical coset for x). Ref: [F1] :: canonical lift U_f with prototype distributions; the choice of prototypes is declared, part of the package ([QM] §Markov analogue: "prototypes are a chosen completion/section and are part of the package").

The composed operator, **Ref: [F1] :: D-IC-01 empirical endomap; [QM] §"A classical analogue" uses the identical construction**:

```
E_{τ,f}(μ) := U_f( Q_f( μ Pᵗ ) )        (t = τ steps of P; Q_f = pushforward through f; U_f = prototype lift)
```

### 4.2 Idempotence defect and retention error (EXACT)

```
δ_{τ,f} := max over point masses δ_z of  ½ · || (E² − E)(δ_z) ||₁      — extreme-point form
ε_{τ,f} := max over macro labels x of  || Q_f(u_x Pᵗ) − δ_x ||_TV      — retention error
```

Extreme-point sufficiency and the bound are theorems: **assert δ_{τ,f} ≤ ε_{τ,f} on every model** (Ref: [F1] :: T-IC-02, "approximate idempotence from retention"; the defect is attained at Dirac extremes by convexity, [F1] :: D-IC-02). Also compute the **multiplicity check**: number of macro labels x with prototype stability `||E(u_x) − u_x||_TV ≤ ε_stable` (config, default 0.05); require ≥ 2 for a nontrivial logical layer (Ref: [F1] :: nontriviality guardrail — "small defect certifies saturation, NOT multiplicity"; this is the trivial-decoder guard).

### 4.3 Route mismatch RM (float ok)

Per **[XOR] :: route-mismatch diagnostic RM_τ(f)** (fiberwise transition-profile form):

```
R_τ(z, x') := Σ_{z' : f(z')=x'} Pᵗ(z, z')                       — micro state z's coarse profile
K_τ(x, x') := Σ_{z ∈ B_x} w_z · R_τ(z, x')                       — fiber-averaged macro row (w = stationary weights, renormalized per fiber)
RM_τ(f)   := Σ_x Σ_{z ∈ B_x} w_z · || R_τ(z,·) − K_τ(x,·) ||₁
```

RM = 0 ⟺ the lens is dynamically lumpable at horizon τ. The signature failure the report must exhibit: a decoder lens that is **channel-accurate but RM ≈ max** under N5 (latched qubit changes future transition profiles inside one current fiber) — the "channel-perfect but RM = 1" leakage signature ([XOR] :: CNOT erased-view result; original motivation document §4.1 (removed 2026-09-05)).

### 4.4 Closure deficit CD_τ (EXACT on small models)

Per **[F3] :: Theorem 8 (FiniteMarkovClosureDeficit), [NG] :: NG_MACRO_CLOSURE_DEFICIT (B5), [CAST] :: exact decomposition & KL form**:

```
CD_τ(Π) := I( X_t ; Y_{t+τ} | Y_t )        under the stationary law, Y = Π(X)
        = Σ_x π(x) · D_KL( p_x^{(τ)}  ||  p̄_{Π(x)}^{(τ)} )
p_x^{(τ)}(y') := Pr[ Y_{t+τ}=y' | X_t=x ]           (row of Pᵗ pushed through Π)
p̄_y^{(τ)}     := Σ_{x∈Π⁻¹(y)} π(x|y) · p_x^{(τ)}     (fiber average)
```

Compute the stationary π by exact eigenvector (float `scipy` acceptable here; verify `||πP − π||₁ ≤ 1e-12`). Guaranteed facts to assert: CD_τ ≥ 0; CD_τ = 0 for lumpable (mode-free) models up to 1e-12 ([NG] :: B5 "CD = 0 iff τ-closed"); the variational property CD_τ = min over macro kernels K of the KL prediction loss, minimized by the fiber-average kernel K* — spot-check by evaluating the loss at K* and at two perturbed kernels (both must be ≥ loss at K*).

**Stream proxy (float):** the predictive gap `Δ_pred := NLL₁ − NLL₂` of order-1 vs order-2 empirical Markov predictors of the macro stream (held-out split 50/50), which estimates I(Y_{t−1}; Y_{t+1} | Y_t). Ref: [CAST] :: predictive-gap proxy; registered correlation vs exact CD across models: Pearson r ≥ 0.9 (CAST's own benchmark reports r = 0.959).

### 4.5 Certificate assembly

`ExistenceCertificate` = record with fields (δ, ε, bound_ok := δ≤ε, multiplicity, RM, CD_τ, Δ_pred, status) where status ∈ {`certified`, `degrading`, `non_closed`, `trivialized`} assigned by frozen thresholds in config: `certified` iff δ ≤ δ_max ∧ CD_τ ≤ cd_max ∧ multiplicity ≥ 2; `trivialized` iff multiplicity < 2; `non_closed` iff CD_τ > cd_max; else `degrading`. Statuses are exactly-one; the classifier is a first-match priority list (`trivialized ≻ non_closed ≻ degrading ≻ certified`), mirroring the status discipline of [F3] §5.6.

---

## 5. Memory audit: predictive quotients (EXACT, `Fraction` end to end)

**Ref: [HOL] :: route-transport package, current/predictive equivalence, quotients Q/M, comparison map π, predictive witness, MaxFiber, Δ^max, exact finite instantiation (§4), paired controls (§4.4–5). This module is a faithful re-implementation of [HOL]'s exact finite machinery, instantiated on QEC round dynamics.**

### 5.1 Package data (all rational)

- Interfaces i ∈ {`now`, `later`}; internal state sets X_i = the Markov states of §4.1 (coset [+ hidden mode]).
- Histories at `now`: a declared finite catalog H of rational probability row-vectors over X_now. Construction: start from the stationary distribution conditioned on each observable syndrome value after w warm-up rounds (w = 3), i.e. one history per reachable syndrome value per initial mode-mixture — this gives histories that agree or disagree on current data in controlled ways. Freeze the exact catalog in config (list the vectors).
- Continuations: `one_round` (kernel P as a rational matrix — noise probabilities are rational by construction), `k_rounds` for k ∈ {1, 2}; loop ℓ = `one_round∘one_round` where an experiment declares it.
- Events at an interface: for `now` — each syndrome bit as weight function w_b(state) = value of bit b in the state's syndrome (0/1 rational); for `later` — the same PLUS the logical-frame indicator (0/1 per logical class). The logical indicator is deliberately absent at `now` (it is future-only), reflecting that logical readout is not a current observable.

### 5.2 Signatures and quotients

Per [HOL] §4: current signature s⁰(h) = tuple of obs(h, e) for all `now` events, where `obs(h, e) = Σ_state h(state)·w_e(state)` (exact rational). Future signature s⁺(h) = tuple of obs(push_γ h, e) over the **declared catalog** of (continuation γ, later event e) pairs — no derived continuations beyond the declared list ([HOL]'s "declared catalog only" discipline). Partition H by exact equality of signature tuples → Q (current classes) and M (predictive classes).

Diagnostics (all exact): witness count = number of unordered pairs equal in s⁰, unequal in s⁺; `MaxFiber` = max number of M-classes over one Q-class; `Δ^max` = max over such pairs of max entrywise |future-obs difference| (a rational number — the calibrated size of what any memoryless decoder forfeits, [HOL] §4.3).

### 5.3 Minimal decoder machine

The predictive quotient M with transport maps T^M_γ (action of each declared continuation on M-classes; well-definedness is [HOL] :: Theorem "predictive transport"; assert it computationally: all members of an M-class must map into a single M-class, else raise). Output the machine as a labeled digraph (nodes = M-classes, edges = continuations). Minimality/universality is [HOL] :: reachable-image factorization theorem — cite, do not re-prove.

**Not every declared history catalog is transport-closed, and that is expected.** [HOL]'s own benchmark suite builds transport/loop-action examples (e.g. the memory-wheel benchmark) as small, purpose-designed catalogs whose declared histories are chosen so that pushing forward via each declared continuation lands back on another declared history's own predictive signature. A catalog built for a different purpose — e.g. §5.1's "one history per reachable syndrome value" memoryless-package audit (used for the witness-count/|Q|=|M| diagnostic of `05_IMPLEMENTATION_PLAN.md` T5) — has no reason to be transport-closed, since pushing a syndrome-conditioned history forward one round under a mixing noise model generally yields a distribution whose own predictive signature matches no declared history at all, regardless of how finely the catalog is drawn (this holds even at the finest possible catalog, one point mass per raw state — verified directly). `transport_check` correctly `raise`s in this case; that is the assertion working as designed, not a defect to route around. Minimal-machine extraction is only meaningful on a catalog built for that purpose — do not call `transport_check` on an audit-purpose catalog like `rep3_n1_package` and expect it to succeed.

### 5.4 Currentization search

Candidate added current events: the hidden-mode indicator (for N4/N5) and each candidate extra check bit from a declared list. For each candidate set c, recompute Q with events ∪ c; **currentization passes** when witness count = 0 and MaxFiber = 1 ([HOL] §controls: currentization status). Return the minimal-cardinality passing set (exhaustive search over the declared candidate list, which must stay ≤ 12 candidates).

### 5.5 Protocol-trap control (mandatory null)

For any experiment claiming decoder memory: build the **internalized counterpart** — if the apparent memory came from an alternating schedule (E5c uses a 2-phase alternating noise schedule as the trap), add the phase as an explicit state coordinate with an autonomous clock (random-scan lift per [PT] §autonomous lifted protocol: with prob α clock ticks, else state updates under current phase kernel; α = 1/2) and recompute witnesses. If witnesses vanish, classify `artifact_trap`; genuine memory (N4 hidden mode) must survive internalization. Ref: [PT] :: protocol-trap theorem; [HOL] :: protocol_trap_naive/honest benchmark pair; [F1] :: T-AOT-02.

---

## 6. Price audit: budgets, duals, slack (float)

**Ref: [SPEND] :: currency roles C1–C4, shadow price λ = ∂Φ*/∂b, slack collapse λ = 0, proxy-currency failure; THEOREMS.md §E6 (attention as budgeted exposure, KKT normal form) and §E9 (acquisition per discharge-per-cost).**

Setup: candidate check family 𝒞 (all degree-1 checks + declared degree-2 products), each with cost 1 (degree-1) or 2 (degree-2); budget b ∈ {0, 1, ..., b_max}. Define the optimal-coverage value function

```
V(b) := max_{S ⊆ 𝒞, cost(S) ≤ b}  [ tr Ξ(D|L₀) − tr Ξ(D | L₀ ∪ S) ]
```

computed by the greedy selector of §3.4 (declare in the report that greedy is a lower bound on V; for REP(3) with |𝒞| ≤ 12 also compute exact V by enumeration and report the gap).

**Shadow price:** λ(b) := V(b+1) − V(b) (discrete marginal value; the discrete analogue of ∂Φ*/∂b). **Slack certificate:** the smallest b* with λ(b) ≤ λ_tol (default 1e-9) for all b ≥ b*; the certificate asserts budgets beyond b* are slack. **Registered consequence (E6):** removing resources down to b* changes the achievable logical MMSE (= tr Ξ) by ≤ λ_tol·(b−b*), and the *sampled* logical error rate of the A_star linear decoder built on the selected checks changes within statistical error. Slack collapse λ = 0 exactly occurs when Ξ hits 0 before budget exhausts — exhibit it (REP(3) reaches Ξ = 0 with its full check set under N1).

**Proxy null ([SPEND] :: proxy-currency failure):** re-run selection with a *scale-matched permuted cost vector* (costs shuffled among candidates, seeded); registered prediction: coverage-per-budget curve strictly worse (report the two curves).

---

## 7. Notation table (single source of truth for code identifiers)

| Math | Code | Type |
|---|---|---|
| e, a ∈ F_2^{2n} | `PauliVec` | `np.ndarray[uint8]` shape (2n,) |
| ⟨a,e⟩ | `sympl(a, e)` | int {0,1} |
| E[σ_a] | `MomentEngine.mean(a)` | `Fraction` or `float` |
| K_LL, K_DL, ... | `MomentEngine.cov_block(A, B)` | matrix |
| Ξ(D\|L) | `xi_residual(K)` | matrix |
| λ_max(Ξ−Ω), z | `blind_spot_witness(xi, omega)` | `(float, vec)` |
| discharge(M\|L,D) | `discharge(K, M_idx)` | matrix |
| E_{τ,f} | `CycleOperator.apply(mu)` | vector |
| δ_{τ,f}, ε_{τ,f} | `idem_defect()`, `retention_error()` | `Fraction` |
| RM_τ(f) | `route_mismatch()` | float |
| CD_τ(Π) | `closure_deficit(P, pi, lens, tau)` | float |
| Δ_pred | `predictive_gap(stream)` | float |
| Q, M, π, witnesses | `QuotientPair.compute()` | exact objects |
| λ(b), b* | `shadow_prices(...)`, `slack_point(...)` | floats |
