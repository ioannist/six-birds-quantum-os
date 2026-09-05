# 04 — Controls, Claim Discipline, and Acceptance

The SBT corpus's credibility rests on its falsification discipline: every positive result must survive a declared null battery, every claim carries a grade, negatives are first-class. The prototype inherits this wholesale. Sources: the null battery in the companion notes `THEOREMS.md` §6 (six-birds-cognition repository, not included here); the controls of [HOL] §4.4–5, [XOR]/recombination papers' matched control bundles; [F1]'s three-certificate independence; claim-grade vocabulary from the Institutions paper as catalogued in THEOREMS.md §1.3.

---

## 1. The three certificates are independent — never conflate

[F1] proves stability, novelty, and directionality certificates are logically independent. Prototype translation, to be enforced in the report's language:

- **Stability** (small δ, high prototype stability) does NOT imply the logical layer stores anything (the trivialized decoder is perfectly stable). Multiplicity is a separate check.
- **Coverage** (Ξ small) does NOT imply existence (a non-closed layer can have well-covered instantaneous logical observables), and vice versa.
- **Memory witnesses** do NOT imply drift, and drift does not imply memory: E2 and E5 phenomena are distinct and must not be summed.

## 2. The null battery (mandatory; each item maps to a concrete implemented control)

1. **Protocol trap / schedule internalization** ([PT]; [F1] T-AOT-02; THEOREMS.md battery item 7). Any memory or directionality claim must survive internalizing the schedule. Implemented: E5c. Standing rule: if an experimenter-visible schedule exists anywhere (alternating rounds, sweep order), ask whether the claimed effect survives making it state.
2. **Same-family saturation** ([XI]). Any "adding X helps" claim must show a matched redundant addition helping exactly zero. Implemented: E1 P1.4, E3 P3.3.
3. **Null-model calibration.** Any detection claim operates at a declared false-positive rate verified on the null. Implemented: E2 P2.3.
4. **Proxy failure** ([SPEND]). Any pricing claim must beat a scale-matched permuted proxy. Implemented: E6 P6.4.
5. **Slack regime** ([SPEND] slack collapse). Any price-like signal must vanish when budgets are slack. Implemented: E6 (λ = 0 beyond b*), E3 P3.4.
6. **No silent caps** (THEOREMS.md battery item on truncation). Every bounded search/candidate cap logs what was dropped (E3c adjacency cap; currentization candidate list).
7. **Trivialization guard** ([F1] multiplicity guardrail). Implemented: E4 P4.4.
8. **Same-support discipline** ([HOL] fixed support). Quotient comparisons only on the declared history catalog; no post-hoc catalog edits. If a catalog change is needed, it is a new experiment with a new config hash.
9. **Memory-only comparator** (Strict-Tests battery item, via THEOREMS.md). For E5 payoff claims: a decoder given raw history *length* but not the machine structure (e.g., logistic regression on the last 3 syndromes, seeded) must not reproduce the minimal machine's full gap on (b) — include as a secondary baseline; if it does reproduce it, report honestly (it bounds the machine's practical value, not the witness's validity).

## 3. Claim grades (every claim in REPORT.md and results.json carries exactly one)

Adopted from the corpus (THEOREMS.md §1.3): 

- `theorem-anchored` — the claim is an instance of a cited SBT theorem verified computationally (e.g., δ ≤ ε held on every model). The strongest grade the prototype can issue.
- `exact-finite` — exact rational computation on a declared finite model (E1, E4-exact, E5 quotient results).
- `measured` — seeded sampling with reported uncertainty (E2 latencies, E6 consequence test).
- `registered-positive` / `registered-negative` — a frozen prediction that passed / failed. Failures are reported in their own section, never deleted, never re-run with tuned parameters (a tuned re-run is a NEW experiment labeled as such).
- `interpretation` — connective prose (e.g., "this is the leakage signature"). Must be marked; carries no evidential weight.

**Forbidden:** blending grades in one sentence; summing conditional and unconditional results; the word "proves" for anything not `theorem-anchored`.

## 4. REPORT.md template (write it in this order)

1. **Summary table** — one row per registered prediction: id, statement, grade, verdict, artifact path.
2. **Headline results** — E2 latency curves, E5 witness/trap table, E1/E3 coverage results, E4 certificate table, E6 slack.
3. **Negative results** — every `registered-negative`, with the honest reading.
4. **Controls ledger** — the §2 battery: each item, where implemented, outcome.
5. **Scope fences and nonclaims** — copy verbatim: 00_OVERVIEW §2 items 1–5 and MS §3.6.
6. **Mechanism-to-experiment map** — map each mechanism of the original motivation document §5 (removed 2026-09-05) to the artifacts demonstrating it (use the stub table in 03_EXPERIMENTS).
7. **Reproduction** — the exact commands; manifest hash roots.

## 5. Acceptance checklist (the hand-off is DONE when all boxes tick)

- [ ] `pytest` green; theorem-anchor tests present and passing (named per 02_ARCHITECTURE §6).
- [ ] `python -m sbqos.reproduce_all` regenerates all artifacts with matching manifests, twice in a row.
- [ ] Every experiment directory contains config, results, manifest, figures + CSVs.
- [ ] Every registered prediction P*.* has a verdict in REPORT.md.
- [ ] Null battery ledger complete (all 9 items).
- [ ] No dependency outside the frozen list; no imports from the other `six-birds-*` repositories.
- [ ] EXACT paths contain no float arithmetic (grep for `float(` and `np.` inside `quotients.py` and the exact branches of `moments.py`/`closure.py`; document the audit in REPORT.md §7).
- [ ] DEVIATIONS.md either absent or complete.
