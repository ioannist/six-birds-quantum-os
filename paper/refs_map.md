# SBT tag -> file -> bibkey map

Source of truth for the bracket-tag legend: `design/01_MATH_SPEC.md` (top of file). Every `[TAG]` citation
appearing anywhere in `design/*.md` or `REPORT.md` resolves to exactly one row below.
Files are the flattened sources of the Six Birds corpus papers; each is cited in `references.bib` by its Zenodo DOI.

| tag | file | bibkey | used for |
|---|---|---|---|
| [F1] | `Tsiokos_2026_Six_Birds_Foundations_of_Emergence_Calculus.tex` | `sbt-f1` | packaging operator, carriers/lenses, fixed points, T-IC-02 (δ ≤ ε) |
| [F3] | `Tsiokos_2026_Six_Birds_Foundations_III_A_Finite_Audited_Interaction_Calculus_for_SBT.tex` | `sbt-f3` | finite/audited/exact-carrier discipline this whole project inherits |
| [XI] | `Tsiokos_2026_Adequacy_Residuals_and_Blind_Spot_Currency.tex` | `sbt-xi` | Ξ, A*, blind-spot witness, chain rule, saturation — the coverage-audit primitive (E1/E2/E3, and all of §7) |
| [NK] | `Tsiokos_2026_Emergence_IS_the_Needle_Killer.tex` | `sbt-nk` | composable bridge defects, `(√a+√b)²` composition (cited for the deferred M5 transport component) |
| [HOL] | `Tsiokos_2026_Holonomy_with_Memory_in_Six_Birds_Theory_..._Route_Transport.tex` | `sbt-hol` | predictive quotients Q/M, witnesses, MaxFiber, currentization, minimal-machine transport — the memory audit (E5) |
| [PT] | `Tsiokos_2026_Six_Birds_Protocol_Trap_Holonomy_Without_Entropy_Production.tex` | `sbt-pt` | protocol trap / schedule-internalization control (E5c) |
| [NG] | `Tsiokos_2026_Six_Birds_No_Go_Theorems_for_Audited_Emergence.tex` | `sbt-ng` | null-battery discipline, illegitimate-proxy criteria |
| [CAST] | `Tsiokos_2026_To_Cast_a_Stone_with_Six_Birds_..._Packaging_and_Budget.tex` | `sbt-cast` | closure deficit CD_τ, budgeted-randomness curve (chain-rule/degree-ladder framing) |
| [XOR] | `Tsiokos_2026_To_XOR_a_Stone_with_Six_Birds_..._Booleanity.tex` | `sbt-xor` | closure diagnostics for emergent bits/gates (background for existence-certificate status classes) |
| [SPEND] | `Tsiokos_2026_To_Spend_a_Stone_with_Six_Birds_..._Closure_Layers.tex` | `sbt-spend` | currency/constraint duality, shadow prices, slack — the pricing audit (E6) |
| [QM] | `Tsiokos_2026_A_Six_Birds_Eye_View_of_Quantum_Theory_..._Record_Stability.tex` | `sbt-qm` | SBT's own quantum-theory scope limits (grounds REPORT.md §5's nonclaims) |
| [HID] | `Tsiokos_2026_Hiddenness_as_a_Structural_Law_of_Emergence.tex` | `sbt-hid` | hiddenness/exposure dichotomy (background for currentization, E5/P5.4) |

Not separately tagged in the design docs but cited by name in `05_IMPLEMENTATION_PLAN.md` for the
exact-finite discipline precedent:

| paper (by filename) | bibkey | used for |
|---|---|---|
| `Tsiokos_2026_Marking_Erasure_and_Recombination_on_Fixed_Support_...tex` | *(not yet in refs.bib — add only if §4 Methods ends up citing it directly; currently referenced only as a house-style precedent in `05_IMPLEMENTATION_PLAN.md`, not needed for the paper's argument)* | exact-finite evidence discipline precedent |

## External literature bibkeys (Tier 2 of `references.bib`)

| bibkey | paper | relevance |
|---|---|---|
| `gidney2021stim` | Gidney, *Stim: a fast stabilizer circuit simulator*, Quantum 5:497 (2021) | circuit-level sampling infrastructure (§4 Methods, §7) |
| `higgott2022pymatching` | Higgott, *PyMatching* (2022), arXiv:2105.13082 | baseline decoder (all experiments with a decoder) |
| `higgott2025sparseblossom` | Higgott & Gidney, *Sparse Blossom*, Quantum 9:1600 (2025), arXiv:2303.15933 | the actual MWPM algorithm PyMatching 2 uses |
| `fowler2012surfacecodes` | Fowler et al., *Surface codes*, Phys. Rev. A 86:032324 (2012) | canonical surface-code reference, rotated-layout convention |
| `google2023suppressing` | Google Quantum AI, *Suppressing quantum errors...*, Nature 614:676-681 (2023), arXiv:2207.06431 | **the key prior-art citation** — establishes that detector-correlation ($p_{ij}$) noise calibration and its edge-weight formula are already standard practice; §1/§8 must cite this when stating the mechanism-novelty scope fence |
| `mcewen2021removing` | McEwen et al., Nature Communications 12:1761 (2021) | correlated-error/leakage detection prior art |
| `dgr2023reweighting` | Wang et al., *DGR: ... Decoding Graph Re-weighting* (2023), arXiv:2311.16214 | closest prior art to E9's recalibrate-on-drift idea (author list verified 2026-09-04) |
| `page1954continuous` | Page, *Continuous Inspection Schemes*, Biometrika 41(1-2):100-115 (1954) | CUSUM foundational reference (E7's W2d rung) |

## Open item for a later pass

`dgr2023reweighting` needs its author list confirmed (a web search surfaced the title/arXiv id but not a
clean author list) before it can be used in the actual manuscript bibliography. Everything else in Tier 2
was cross-checked against arxiv.org/journal pages on 2026-07-06 and should not need re-verification unless
a referee disputes a detail.

## Correction 2026-09-05: SBT corpus entries are published preprints

All twelve Tier-1 entries are Zenodo-deposited preprints and are cited by DOI (`@misc`, howpublished Zenodo); `sbt-hol` (Holonomy with Memory) was deposited on 2026-09-05 as 10.5281/zenodo.22335923. Each DOI was verified against the Zenodo API record (author, title, date). The July bibliography had typed all twelve as unpublished manuscripts; the citation QA of 2026-09-04 only re-verified the newly added entries, which is how this survived until the author caught it.

## Bibliography expansion (2026-09-04)

60 further external entries were added to `references.bib` after a literature search (157 verified candidates were screened), plus three author-verified additions (`chen2021exponential`, `kemeny1960finite`, `cover2006elements`). Selection rule: cite only where credit for a concept/tool/prior mechanism is owed or a field-level factual claim needs support. Every entry was checked against Crossref/arXiv/Zenodo metadata on 2026-09-04/05.
