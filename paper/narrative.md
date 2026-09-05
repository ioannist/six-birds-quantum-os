# Frozen Narrative Decisions

Written before any LaTeX prose, per the paper plan's Phase A4. These decisions govern all of Phase B;
deviating from them mid-write requires updating this file first (same discipline as `design/DEVIATIONS.md`
for the prototype build — a deviation is logged, not silently absorbed into the prose).

## Title

**Recommended:** *"Auditing Emergence in Quantum Error Correction: A Falsifiable Instantiation of Six
Birds Theory"*

Alternatives considered:
1. *"Closure Certificates for Logical Qubits: Testing Six Birds Theory Against Quantum Error Correction"*
   — more concrete about the QEC object (closure certificates), but leads with QEC-sounding vocabulary
   that risks being read as a QEC contribution paper, which is not the point (see below).
2. *"What Happens When an Emergence Framework Meets Real Numbers: Six Birds Theory on Quantum Error
   Correction"* — the most honest/plain-spoken option, good for a workshop-style framing, but too
   informal for a main title; could work as a subtitle or in the introduction's framing sentence instead.

**Why the recommended title:** "Auditing Emergence" foregrounds the actual contribution (an audit
methodology, not a QEC technique); "Falsifiable Instantiation" states the paper's real thesis in the title
itself — this is a test of whether SBT generates falsifiable structure, not a QEC results paper. It also
reads honestly to a QEC audience skimming titles: it does not promise a decoder improvement.

## Abstract (first draft — to be rewritten in Phase B13 from the finished sections, this is the frozen
## *shape*, not the frozen wording)

> Six Birds Theory (SBT) claims that its abstract primitives — packaging operators, adequacy residuals,
> existence certificates, predictive quotients, protocol traps, and priced budgets — generate checkable,
> falsifiable structure in any domain with a notion of packaging. We test this claim by instantiating four
> of these six primitives on quantum error correction (QEC), building an open, reproducible simulation
> prototype, and pre-registering predictions before running each experiment. Of 25 original predictions,
> 14 failed as frozen and are reported unaltered, each with a diagnostic reading; a fifth primitive
> (pricing) was implemented but its predictions also failed at every frozen tolerance; a sixth
> (transport/functoriality) was explicitly out of scope. The paper's centerpiece is a self-correction
> arc: one registered failure (a deployable drift-detection witness) is diagnosed using the framework's
> own exact machinery, corrected, and re-registered — including a prediction that the correction would
> still fail on the original test scenario, which held. The correction then generalizes to circuit-level
> noise and a closed decoder-recalibration loop, where it beats a genuinely budget-matched blind schedule.
> None of the individual QEC mechanisms is novel relative to existing detector-correlation calibration and
> adaptive decoder reweighting; the contribution is that SBT's audit/certificate framing, pre-registration
> discipline, and self-correction loop survived contact with a real technical domain, including its own
> honestly-reported failures. All code, configs, and results are open and reproduce byte-identically.

(~230 words; will need trimming to ~180-200 in B13, but every clause above maps to a specific,
already-verified claim in `paper/claims.md` — C-01/C-02/C-03 for the opening thesis, C-22/C-23 for the 14
negatives, C-21a/C-21b for the pricing caveat, C-01 again for the M5 deferral, C-24..C-35 for the
self-correction arc, the non-claims checklist for the "no mechanism novelty" sentence, C-37 for
reproducibility.)

## Story arc (binding on section order and emphasis)

1. **Set up the test, not the technology.** SBT claims value only when it changes the audit/packaging
   layer, not when it renames existing mechanics (this is the primer's own standard — see
   `six-birds-papers/SIX_BIRDS_ANTI_REDUCTIONISM_PRIMER.md`). The paper exists to check whether that's
   true here, adversarially.
2. **Instantiate all six primitives honestly** — four positively demonstrated (coverage/Ξ, existence
   certificate, predictive-quotient memory witness, protocol-trap control), one implemented but
   evidentially negative (pricing/shadow-prices), one explicitly deferred (transport/functoriality). State
   this split in the introduction itself, not just in limitations — burying it would repeat the exact
   overclaim an external review already caught once (see `paper/claims.md`'s provenance note).
3. **Show the falsification discipline is real**, via the certificate/exact results (chain rule, exact
   MMSE) and via the 14 honest negatives, each with a specific, non-hand-wavy reading — three worked
   examples in the main text, full table in the appendix.
4. **The centerpiece: diagnosis → correction → re-registration → generalization.** E2's registered failure
   is diagnosed with the framework's own exact machinery (not new mechanics — this point matters: the
   *diagnostic move itself* is an instance of the adequacy-residual primitive, applied reflexively). The
   correction is re-registered, including a predicted continued failure that held (this is the strongest
   single piece of evidence against "post-hoc storytelling" and must be given prominent, explicit
   narrative weight — flag it, don't let it pass as one bullet among many). The correction generalizes to
   circuit-level noise (thin margin, stated as such) and a closed control loop (a clean, budget-matched win).
5. **Close by being explicit about what this does and does not establish.** Does: SBT's primitives, when
   forced into a real domain, produced checkable structure, a real falsification loop, and a genuine
   self-correction under adversarial internal and external review. Does not: validate SBT's broader
   metaphysical ambitions elsewhere in the corpus; establish QEC-mechanism novelty; provide hardware-scale
   or hardware-validated evidence.

## Headline vs. appendix split

**Main text (headline):**
- The mapping table (§3) — four positive, one negative, one deferred, stated plainly in the table itself.
- Exact coverage/degree-ladder result attaining the enumerated optimal MMSE (the cleanest single
  "the theory computes the right object" result — gets real space, including the exact fraction).
- The existence-certificate status table (certified/degrading/non-closed/trivialized), because it is the
  clearest single illustration of the certificate idea doing real classification work.
- Three worked negative-result examples (one per failure-type: wrong-scale bound, over-strict threshold,
  mischaracterized-but-informative structure) — not all 14, but the three that best teach the taxonomy.
- The full E2→diagnosis→E7→E8→E9 arc, with the predicted-and-held failure (P7.3) given explicit narrative
  weight, and both thin-margin/statistically-unresolved caveats (E8's P8.1, E9's P9.3) stated in the same
  sentence as the result, never separated from it.
- The pricing negative result (C-21a/C-21b) stated plainly as a full negative, not softened.

**Appendix:**
- Full 25+14+7+2+4 prediction table with grades/verdicts/artifact paths (Appendix B).
- Null-battery ledger (Appendix C).
- All 8 deviations, 2-3 sentences each (Appendix D) — including the newly-logged bounded-weight fix and
  the E9 budget-matching correction, both of which are *evidence for* the rigor claim and should not be
  hidden, but at appendix length/detail, not main-text length.
- Full math-spec formula summary (Appendix E).
- Notation table (Appendix A).

## Explicit non-negotiables carried from `paper/claims.md`'s non-claims checklist into every draft

- Never say "all six primitives were implemented."
- Never let the protocol-trap result read as "the trap caught something" — it is a negative result for
  the artifact hypothesis.
- Never generalize "exact" beyond the specific modules named in claims.md C-36.
- E8's P8.1 and E9's P9.3 always carry their margin/statistical-uncertainty caveat in the same sentence.
- No mechanism-novelty claim for detector-correlation calibration or decoder reweighting — cite
  `google2023suppressing` and `dgr2023reweighting` in §1/§8 to make this explicit, not merely implied.
