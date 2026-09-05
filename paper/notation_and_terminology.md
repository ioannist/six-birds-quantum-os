# Notation and Terminology for Foundations III

This file fixes the notation and terminology discipline for the Foundations III
paper.

It is intended to be self-contained for drafting agents. An agent should not
need to read the Foundations I or Foundations II papers to know which notation
to use. Source references below explain provenance, but the operative notation
rules are stated in this file.

The default rule is conservative:

> Reuse Foundations I and Foundations II notation whenever the same object or
> concept is being used. Introduce new notation only when Foundations III defines
> a genuinely new object, a typed refinement, or an interaction-level structure
> that did not exist in the earlier papers.

Relabeling and sharper descriptions are allowed when Foundations III makes a
term more precise. A new label must not silently change the meaning of an
inherited symbol.

## Quick Reference

### Core Objects

| Symbol / term | Meaning | Status |
| --- | --- | --- |
| \(\mathcal T\) | Inherited finite theory package | Reuse |
| \(Z\) | Finite carrier, microstate, or micro-description space | Reuse |
| \(f:Z\to X\) | Lens / coarse-description map | Reuse |
| \(\Sigma_f\) | Expressive content / finite definability structure induced by \(f\) | Reuse |
| \(E:\mathcal V\to\mathcal V\) | Completion / packaging endomap | Reuse |
| \(\mathcal A\) | Audit functional | Reuse |
| \(P_1,\ldots,P_6\) | Six primitive roles | Reuse |
| \(\mathsf{FATCD}\) | Finite audited typed closure description domain from Foundations II | Reuse when referring to Foundations II |
| \(D\) | A finite audited typed closure description when working in \(\mathsf{FATCD}\) | Reuse |
| \(\mathbf{BirdInt}^{\mathrm{aud}}_{\mathrm{fin}}\) | Foundations III finite audited interaction calculus | New |
| \(P_i\leftarrow P_j\) | Directed interaction cell: actor/update side \(P_i\), informant/witness side \(P_j\) | New |
| \(W_i\), \(W_j\) | Witness data for a primitive role | Extended |
| \(U_i\) | Update/effect data for an actor primitive | New |
| \(I\) | Instrument | Extended |
| \(L\) | Level/lens/interface record in Foundations III judgments | New typed record |
| \(V\) | Visibility record | Extended |
| \(\Theta\) | Threshold record | Extended |
| \(A\) | Finite audit record, certificate, or trace | New typed record |
| \(\delta\) | Defect record | New typed record |
| \(\lambda\) | Profile | New typed record |
| \(\sigma\) | Status, always family-indexed by context | Extended |
| \(\mathcal N\) | Nonclaim record | Reuse/extended |

### Reserved Symbol Policy

| Symbol | Reserve for | Avoid using for |
| --- | --- | --- |
| \(P\) | Markov/probability kernel when used without primitive index | Primitive set in probability-heavy sections |
| \(\mathbb P\) | Primitive-label set only if probability kernels are not locally prominent | Path laws or probability measures |
| \(\mathsf{Prim}\) | Preferred primitive-label set in probability-heavy sections | Probability kernels |
| \(\mathcal A\) | Audit functional | Finite audit record |
| \(A\) | Finite audit record | Audit functional |
| \(\Sigma_f\) | Expressive content induced by lens \(f\) | Status |
| \(\sigma\) | Status | Expressive content |
| \(E\) | Completion/packaging endomap | Edge set, unless graph notation explicitly overrides it |
| \(V\) | Visibility record in judgments | Description space \(\mathcal V\) |
| \(\mathcal V\) | Description space for completions | Visibility record |

### Canonical Primitive Role Gloss

Use these role descriptions in Foundations III:

| Role | Canonical Foundations III gloss | Guardrail |
| --- | --- | --- |
| \(P_1\) | Descent, closure, rewrite, transport of content | Generic semantic interpretation alone is not \(P_1\) |
| \(P_2\) | Representability, gating, admissibility | Generic filtering without representability/admissibility data is not enough |
| \(P_3\) | Route mismatch, holonomy, path/protocol comparison | Not a directionality certificate by itself |
| \(P_4\) | Refinement, staging, gluing | Generic transition data alone is not enough |
| \(P_5\) | Packaging, completion, objecthood, idempotence | Generic path or derivation data is not \(P_5\) |
| \(P_6\) | Audit, provenance, replay, drive certification | Drive is a face of \(P_6\), not all of \(P_6\) |

### Canonical Status Families

Foundations III uses several status families. Always name the family if the
context is not obvious.

| Family | Applies to | Typical values |
| --- | --- | --- |
| Role-channel status | \(\Chan{i}{D}\) in a six-channel description | `active_projection`, `below_threshold`, `collapsed_boundary_case`, `absent_with_record`, `inapplicable_outside_scope` |
| Directed-cell status | \(P_i\leftarrow P_j\) cells | `outside_scope`, `absent`, `blocked`, `undefined_circular`, `collapsed`, `below_threshold`, `trivial`, `implicit`, `action` |
| Pair-observable status | Pair observability contracts | `real`, `blocked`, `fallback_only`, `dirty`, `missing_source`, `outside_scope` |
| Promotion status | Promotion bridges | `strict`, `non_strict`, `blocked`, `unstable`, `smuggled`, `outside_scope`, `failed_gate` |
| Claim status | Instrument-indexed claims | `accepted`, `visible_only`, `suppressed`, `overread`, `undefined_circular`, `blocked`, `outside_scope` |
| Gate status | Finite checks | `pass`, `fail`, `blocked`, `outside_scope`, `deferred` |
| Square status | High-structure decorated squares | `exact`, `defective`, `no_filler`, `blocked`, `undefined_circular`, `outside_scope` |

Only the first row is inherited directly as the Foundations II channel-status
taxonomy. The other rows are Foundations III status families.

## Source Hierarchy

Use these sources in this order when resolving notation.

1. `paper/detailed_outline.md` for the Foundations III paper structure and new
   canonical interaction-level objects.
2. `thread/08-final-paper-packet/149-assemble-final-domain-definition.md`,
   `150-assemble-final-mathbf-birdint-definition.md`, and
   `151-assemble-final-status-and-defect-definitions.md` for final Foundations
   III definitions.
3. `papers/Tsiokos_2026_Six_Birds_Foundations_II_Admissibility_Meta_Theory_and_the_Exact_Six_Program.tex`
   for inherited admissibility, threshold, visibility, channel, status, and
   exact-six discipline.
4. `papers/Tsiokos_2026_Six_Birds_Foundations_of_Emergence_Calculus.tex` for
   inherited theory-package, lens, completion, audit, closure, and emergence
   calculus notation.

When an inherited concept is reused unchanged, keep the inherited notation. When
Foundations III extends a concept, state the inherited object first and then add
the new typed record, status family, bridge, or judgment form.

## Inherited Notation To Preserve

### Theory Package

Foundations I defines a finite theory package as

[
\mathcal T=(Z,f,\Sigma_f,E,\mathcal A).
]

Use this notation whenever the paper refers to the inherited theory-package
object:

- \(Z\): finite carrier or micro-description space.
- \(f:Z\to X\): lens or coarse description.
- \(\Sigma_f\): expressive content / finite definability structure induced by
  \(f\).
- \(E:\mathcal V\to\mathcal V\): completion or packaging endomap.
- \(\mathcal A\): audit functional.

Foundations III may add typed annotations, visibility records, source records,
defect records, promotion records, and model-realization records around
\(\mathcal T\), but those additions should be presented as extra structure over
the inherited package, not as an unannounced replacement of
\((Z,f,\Sigma_f,E,\mathcal A)\).

### Completion and Objecthood

Keep \(E\) for a completion/packaging endomap when the object is the same
completion rule inherited from Foundations I.

Use \(E\circ E=E\) for exact idempotence where applicable. If an approximate
completion, empirical endomap, or model-specific completion is used, mark the
host and approximation explicitly.

Use "fixed points" or "objects" for internally complete descriptions recognized
by a completion rule.

### Lens and Expressive Content

Use \(f\) for a lens when referring to the inherited coarse-description map.
Use \(\Sigma_f\) for the expressive content induced by \(f\).

If Foundations III needs a broader interface/lens record, it may introduce a
typed record such as \(L\), but \(L\) should not erase \(f\) or \(\Sigma_f\).
State whether \(L\) contains \(f\), refines \(f\), or denotes a different
interface object.

### Audit Functional

Use \(\mathcal A\) for the inherited audit functional when it is a monotone or
certifying functional over the relevant objects.

Foundations III may use \(A\) for a finite audit record inside a directed cell,
promotion bridge, or claim record. If both appear:

- \(\mathcal A\) is the audit functional;
- \(A\) is an audit record, certificate, trace, or finite evidence object.

Do not use \(A\) and \(\mathcal A\) interchangeably.

### Primitive Roles

Use \(P_1,\ldots,P_6\) for the six primitive roles.

Foundations II also defines macros \(\Pone{},\ldots,\Psix{}\) in the manuscript
source. In Markdown planning files, \(P_1,\ldots,P_6\) is acceptable. In LaTeX
drafting, choose one house style and apply it consistently.

The Foundations III role descriptions are canonical for this paper:

- \(P_1\): descent, closure, rewrite, transport of content.
- \(P_2\): representability, gating, admissibility.
- \(P_3\): route mismatch, holonomy, path/protocol comparison.
- \(P_4\): refinement, staging, gluing.
- \(P_5\): packaging, completion, objecthood, idempotence.
- \(P_6\): audit, provenance, replay, drive certification.

These are role labels, not elements of a total algebra.

### Drive Face of \(P_6\)

Use \(P6_{\mathrm{drive}}\) in planning prose and
\(\mathrm{P6}_{\mathrm{drive}}\) or a defined LaTeX macro in manuscript prose,
but do not use both styles in the final draft without a convention note.

Meaning:

\(P6_{\mathrm{drive}}\) is the drive/directionality-certifying face of \(P_6\).
It is not a replacement for \(P_6\). A \(P_3\) route-mismatch or holonomy witness
does not establish directionality without a \(P_6\)-side audit or drive
certificate.

### FATCD and Exact-Six Discipline

Foundations II uses

[
\mathsf{FATCD}
]

for finite audited typed closure descriptions. Keep this notation when referring
to the Foundations II domain.

Do not rename \(\mathsf{FATCD}\) as \(\mathbf{BirdInt}\). They are different
objects:

- \(\mathsf{FATCD}\): inherited description domain for scoped exact-six.
- \(\mathbf{BirdInt}^{\mathrm{aud}}_{\mathrm{fin}}\): Foundations III finite
  audited interaction calculus.

Foundations III may use \(\mathsf{FATCD}\)-style assumptions or records inside
its domain, but it should state the embedding or inheritance relation.

Use these inherited operators when referring to a description \(D\) in the
\(\mathsf{FATCD}\) regime:

| Notation | Meaning |
| --- | --- |
| \(\Raw{D}\) | Raw finite records, features, and annotations carried by \(D\) |
| \(\Audit{D}\) | Honest bookkeeping / audit subrecord of \(D\) |
| \(\Closed{D}\) | Closure condition for references, sources, dependencies, and bookkeeping |
| \(\Dec{D}\) | Decomposition/exhaustion record for \(D\) |
| \(\Residual{D}\) | Residual feature set not already accounted for by active projections or inactive status records |
| \(\Chan{i}{D}\) | \(P_i\)-labeled role channel of \(D\) |
| \(\Status{i}{D}\) | Channel status of \(\Chan{i}{D}\) |
| \(\ScopedExactSix{D}\) | Scoped exact-six assertion for \(D\) |

If these operator macros are not defined in the manuscript preamble, define them
or write the corresponding operator names explicitly. Do not invent alternative
symbols for the same inherited objects.

### Decomposition/Exhaustion Record

When referring to inherited decomposition/exhaustion records, use:

[
\Dec{D}
=
\bigl(\Raw{D},(\Chan{i}{D},\Status{i}{D})_{i=1}^{6},
\Residual{D},\mathrm{Classify},\mathcal L,\mathcal V,
\Audit{D},\mathcal N\bigr).
]

Meanings:

- \(\Raw{D}\): raw finite records and annotations;
- \((\Chan{i}{D},\Status{i}{D})_{i=1}^{6}\): the six role-channel/status
  entries;
- \(\Residual{D}\): unabsorbed residual records;
- \(\mathrm{Classify}\): residual classification map;
- \(\mathcal L\): loss/lift records for level crossings, forgetting, and
  translations;
- \(\mathcal V\): instrument-visibility and suppression annotations in the
  inherited decomposition record;
- \(\Audit{D}\): honest bookkeeping record;
- \(\mathcal N\): explicit nonclaim record.

Do not confuse the inherited \(\mathcal V\) in \(\Dec{D}\) with a Foundations
III cell-level visibility record \(V\), or with the description space
\(\mathcal V\) used for \(E:\mathcal V\to\mathcal V\). If ambiguity arises,
rename the local visibility record to \(V_{\mathrm{vis}}\) in the manuscript.

### Scoped Exact-Six

Use "scoped exact-six" only for the Foundations II theorem shape:

- the domain is \(\mathsf{FATCD}\);
- each admissible description has exactly six role channels;
- each channel has exactly one channel status;
- channels need not all be active;
- residual features are classified rather than silently ignored;
- the theorem is scoped and does not prove unrestricted exact-six.

Do not use "exact-six" in Foundations III to mean that every directed cell,
model realization, or theory package activates all six roles.

### Channel and Activation

Preserve the Foundations II distinction:

- a role channel is a \(P_i\)-labeled slot;
- an active projection is a role witness that passes the required threshold,
  level, witness, and audit conditions.

Having a channel is not the same as having an active witness.

Use \(\pi_i(D)\) for an active derived role projection of \(D\), when working
in inherited Foundations II notation. An active projection must carry:

- a role-aligned feature cluster;
- witness data \(W_i\);
- threshold data \(\Theta_i\);
- level assignment;
- audit/bookkeeping support;
- visibility/support records when relevant.

Do not write \(\pi_i(D)\) if the role is merely present as a channel or if its
status is below-threshold, collapsed, absent-with-record, or outside-scope.

### Foundations II Channel Statuses

When referring specifically to Foundations II channel status, use the inherited
five-status taxonomy:

- `active_projection`: an active derived role projection \(\pi_i(D)\) exists
  with required threshold, witness, level, and audit data;
- `below_threshold`: candidate raw features are present, but the threshold data
  required for activation is absent or not met;
- `collapsed_boundary_case`: a candidate feature cluster collapses under the
  relevant witness schema and cannot support an active projection;
- `absent_with_record`: no relevant raw features for that role are present, and
  the absence is explicitly recorded;
- `inapplicable_outside_scope`: the role-\(P_i\) content lies outside the
  covered scope.

Foundations III may define additional status families for directed cells,
pair-observables, promotions, claims, gates, and high-structure squares. Those
new status families extend the interaction calculus; they do not retroactively
replace the inherited channel-status taxonomy.

### Threshold, Witness, Level, Visibility, Instrument

Preserve the Foundations II vocabulary:

- threshold data;
- witness data;
- level assignment;
- instrument-relative visibility;
- visible content;
- suppressed content;
- empirical-bridge/admissibility records;
- nonclaim records.

Foundations III may make these typed fields in directed-cell, promotion, and
claim judgments. Do not treat them as optional prose labels.

Use the following terms consistently:

- "threshold data" means explicit activation criteria, not informal salience;
- "witness data" means role-specific evidence or structure, not generic support;
- "level assignment" means the behavioral, verification, or structural level at
  which a claim is being made;
- "instrument" means the declared observational or audit context under which
  content is visible;
- "visible content" means content available under the declared instrument;
- "suppressed content" means content not available under the declared
  instrument without a bridge;
- "nonclaim record" means an explicit record of what is not being asserted.

### Behavioral, Verification, and Structural Levels

Each primitive role may appear at three levels:

- behavioral level: status, occurrence, or observed behavior of the role in a
  description;
- verification level: proof, witness, certificate, or checkable record
  supporting a behavioral claim;
- structural level: reusable structure supporting the primitive role.

Do not compare claims across levels without a level map, loss/lift record, or
bridge. Direct cross-level comparison is inadmissible unless explicitly
licensed.

## New Foundations III Notation

### Central Calculus

Foundations III introduces:

[
\mathbf{BirdInt}^{\mathrm{aud}}_{\mathrm{fin}}
]

for the finite audited interaction calculus.

This is new notation and should be reserved for the central Foundations III
object. It should not be used for any earlier paper's domain.

The final domain tuple is:

[
\mathbf{BirdInt}^{\mathrm{aud}}_{\mathrm{fin}}
=
(\mathbb P,\mathsf{Lev},\mathsf{Host},\mathsf{Cont},\mathsf{Instr},\mathsf{Pkg},
\mathsf{Prof},\mathsf{Wit},\mathsf{Upd},\mathsf{Def},\mathsf{Judg},
\mathsf{Status},\mathsf{Gate},\mathsf{Dep},\mathsf{Audit},\mathsf{Vis},
\mathsf{Source},\mathsf{Nonclaim},\mathsf{Real}).
]

Component meanings:

| Component | Meaning |
| --- | --- |
| \(\mathbb P\) or \(\mathsf{Prim}\) | Six primitive role labels |
| \(\mathsf{Lev}\) | Level set and level maps |
| \(\mathsf{Host}\) | Permitted finite host structures |
| \(\mathsf{Cont}\) | Content universe: finite records, maps, diagrams, kernels, graphs, etc. |
| \(\mathsf{Instr}\) | Instruments and instrument records |
| \(\mathsf{Pkg}\) | Theory packages and package records |
| \(\mathsf{Prof}\) | Profiles controlling which judgment form and status rules apply |
| \(\mathsf{Wit}\) | Witness families for primitive roles |
| \(\mathsf{Upd}\) | Update/effect families for primitive roles |
| \(\mathsf{Def}\) | Defect-record families |
| \(\mathsf{Judg}\) | Judgment forms |
| \(\mathsf{Status}\) | Status families |
| \(\mathsf{Gate}\) | Gate/check records |
| \(\mathsf{Dep}\) | Dependency and no-go records |
| \(\mathsf{Audit}\) | Audit records, traces, and certificate objects |
| \(\mathsf{Vis}\) | Visibility and suppression records |
| \(\mathsf{Source}\) | Source-of-truth and provenance records |
| \(\mathsf{Nonclaim}\) | Explicit nonclaim records |
| \(\mathsf{Real}\) | Model-realization records |

Do not abbreviate the central calculus as just "the algebra." Foundations III
explicitly rejects a total six-symbol algebra.

### Permitted Hosts

When a theorem or model-realization statement uses a host, name it.

Permitted host vocabulary:

- finite sets and finite maps;
- finite records and finite relations;
- finite diagrams;
- finite graphs and finite cochain/cycle data;
- finite stochastic kernels;
- finite abstract-interpretation domains;
- finite decorated-square or double-category fragments;
- audited Cantor-shell realization records.

If the host is not one of these, either define it explicitly or mark the claim
as outside the current paper.

### Primitive-Set Notation

The outline currently uses

[
\mathbb P=\{P_1,\ldots,P_6\}.
]

This is acceptable for the finite set of primitive labels, but it can visually
conflict with probability kernels \(P\) from Foundations I. In the manuscript,
choose one of the following and define it once:

- keep \(\mathbb P\) for the primitive-label set and reserve plain \(P\) for
  kernels only when subscripted or context is clear;
- use \(\mathsf{Prim}\) for the primitive-label set if probability kernels are
  prominent in the same section.

Do not change this casually. If probability kernels and primitive labels appear
heavily in the same proof, prefer \(\mathsf{Prim}\) for clarity.

### Directed-Cell Judgments

Foundations III introduces directed-cell judgments:

[
\Gamma;\mathcal T;I
\vdash
(P_i\leftarrow P_j,W_j,U_i,L,V,\Theta,A,\delta)^\lambda:\sigma.
]

Use this only for interaction-level judgments.

Interpretation:

- \(P_i\): actor/update-side primitive.
- \(P_j\): informant/witness-side primitive.
- \(W_j\): witness data of type \(\mathsf{Wit}(P_j)\).
- \(U_i\): update/effect data of type \(\mathsf{Upd}(P_i)\).
- \(L\): level/lens/interface record.
- \(V\): visibility record.
- \(\Theta\): threshold record.
- \(A\): finite audit record.
- \(\delta\): defect record.
- \(\lambda\): profile.
- \(\sigma\): status.

Do not interpret \(P_i\leftarrow P_j\) as a binary product \(P_iP_j\). It is a
typed bridge judgment.

Directed-cell status values should be drawn from the directed-cell status
family, not from the inherited channel-status family. Use:

- `outside_scope`: the candidate cell is not covered by the declared profile,
  host, or instrument;
- `absent`: required actor/informant content is absent;
- `blocked`: a gate, dependency, source, visibility, or defect condition blocks
  action;
- `undefined_circular`: the cell depends on an unstratified circular
  audit/support loop;
- `collapsed`: the candidate degenerates and no longer instantiates the
  intended cell structure;
- `below_threshold`: relevant content exists but threshold data is absent or not
  met;
- `trivial`: the cell is well-formed but carries only identity/null behavior;
- `implicit`: the cell is present only implicitly through another accepted
  structure;
- `action`: the cell is active under the declared witness, update, threshold,
  visibility, and audit records.

If a manuscript section uses a shorter status set, state that it is a
restriction of this family.

### Witness and Update Families

Foundations III introduces:

[
\mathsf{Wit}(P_i),
\qquad
\mathsf{Upd}(P_i).
]

Use these for typed witness and update/effect families.

The central constraint is:

[
W_j\in\mathsf{Wit}(P_j),
\qquad
U_i\in\mathsf{Upd}(P_i).
]

This notation refines Foundations II's witness and threshold discipline. It
does not replace the requirement that witness data be supported by threshold,
level, visibility, and audit records.

### Promotion Judgments

Foundations III introduces promotion judgments:

[
\Gamma;\mathcal T_j;I
\vdash
\mathrm{Promote}
(\mathcal T_j,\mathcal T_{j+1},\pi_j,\pi_{j+1},L,V,\Theta,A,\delta,\mathcal N)
:
\sigma_{\mathrm{promote}}.
]

Use this only for theory-layer/package promotion.

Terminology:

- strict promotion: accepted promotion with nonfactorization across the old
  interface;
- non-strict promotion: accepted promotion that factors through the old
  interface;
- gate: a finite check required for promotion acceptance;
- no-smuggling: the promotion does not hide undeclared structure.

Promotion gate names should be descriptive. Use these names unless the final
formalization chooses shorter labels:

- well-formedness gate;
- source/provenance gate;
- visibility/no-smuggling gate;
- factorization/strictness gate;
- stability gate;
- stacking-viability gate;
- self-reference honesty gate.

Promotion status values:

- `strict`: accepted promotion with nonfactorization;
- `non_strict`: accepted promotion that factors through the old interface;
- `blocked`: some required bridge, source, visibility, or dependency is missing;
- `unstable`: stability gate fails;
- `smuggled`: no-smuggling gate fails;
- `outside_scope`: promotion lies outside the declared domain;
- `failed_gate`: at least one required gate fails.

### Instrument-Indexed Claims

Foundations III uses:

[
\Gamma;\mathcal T;I\vdash\varphi:\chi.
]

Use this for claim semantics under an instrument \(I\).

This extends Foundations II's instrument-relative visibility discipline. It does
not assert instrument-free truth.

Claim status values:

- `accepted`: claim is accepted at its declared strength under the declared
  instrument;
- `visible_only`: claim is limited to visible content;
- `suppressed`: claim targets suppressed content without sufficient bridge for
  stronger acceptance;
- `overread`: claim asserts more than the instrument-visible or bridged content
  supports;
- `undefined_circular`: claim depends on an unstratified circular
  support/audit loop;
- `blocked`: claim is blocked by missing source, failed audit, failed gate, or
  defect;
- `outside_scope`: claim lies outside the domain.

Use "accepted under \(I\)" rather than "true" unless the section has defined a
truth semantics. Foundations III uses instrument-indexed acceptance, not
instrument-free truth.

### Defect Records

Use \(\delta\) for local defect records attached to cells, promotions, claims,
or model-realization checks.

If multiple defects are present, use typed names or subscripts:

- \(\delta_1,\ldots,\delta_6\) for primitive-linked defect families;
- \(\delta_{\mathrm{fact}}\) for factorization defects;
- \(\delta_{\mathrm{vis}}\) for visibility defects;
- \(\delta_{\mathrm{audit}}\) for audit defects.

Do not use a bare \(\delta\) across a long proof if several defect types are in
play.

Primitive-linked defect families:

- \(P_1\): descent, closure, rewrite defects;
- \(P_2\): representability and gating defects;
- \(P_3\): route-mismatch and holonomy defects;
- \(P_4\): refinement, staging, gluing defects;
- \(P_5\): packaging, completion, objecthood defects;
- \(P_6\): audit, provenance, drive defects.

Promotion-specific defect names:

- strictness/factorization defect;
- no-smuggling defect;
- stability defect;
- descent defect inside promotion.

Claim-level defect names:

- hidden-content overread;
- missing visibility bridge;
- claim-strength mismatch;
- missing source/audit.

### Status Families

Foundations III has multiple status families:

- role-channel statuses;
- directed-cell statuses;
- pair-observable statuses;
- promotion statuses;
- claim statuses;
- gate statuses;
- square statuses.

Use the family name whenever ambiguity is possible:

- "directed-cell status";
- "pair-observable status";
- "promotion status";
- "claim status";
- "gate status";
- "square status".

Do not infer one status family from another without a theorem or bridge rule.

The following implications are forbidden unless a theorem or bridge is supplied:

- role-channel status \(\Rightarrow\) directed-cell status;
- directed-cell `action` \(\Rightarrow\) pair-observable `real`;
- promotion `strict` \(\Rightarrow\) macro closure;
- promotion `strict` \(\Rightarrow\) drive;
- claim `accepted` \(\Rightarrow\) suppressed content is visible;
- audit record present \(\Rightarrow\) claim is true.

### Pair-Observable Judgments

Use "pair-observable judgment" for claims that a primitive pair is observable,
real, blocked, dirty, fallback-only, or source-supported as a pair.

Recommended status values:

- `real`: pair has source-of-truth support under the declared instrument;
- `blocked`: pair cannot be accepted because a required source, bridge, or
  visibility condition fails;
- `fallback_only`: only fallback/proxy support exists;
- `dirty`: source/provenance state is contaminated or mixed;
- `missing_source`: no source-of-truth record exists;
- `outside_scope`: pair lies outside the declared profile or host.

Do not infer pair realness from a directed cell. A directed cell can be active
while the pair-observable judgment is blocked.

### Dependency and No-Go Judgments

Use dependency/no-go notation for implication claims between role faces,
statuses, or certificates.

Examples:

[
P_3\not\Rightarrow P6_{\mathrm{drive}},
\qquad
P_5\not\Rightarrow \text{macro closure}.
]

Interpretation:

- \(\not\Rightarrow\) means "does not imply under the declared scope";
- a positive implication requires an explicit bridge theorem;
- a no-go claim should be supported by a theorem or finite countermodel.

Do not treat no-go notation as global metaphysical impossibility. It is scoped
to the declared finite host/profile unless stated otherwise.

### Model-Realization Notation

Use \(\mathcal M\models\mathcal S\) only after defining:

- model family \(\mathcal M\);
- target structure or fragment \(\mathcal S\);
- realization map;
- host;
- scope and nonclaims.

Recommended fragment names:

- \(\mathbf{BirdInt}^{\mathrm{cell/pair/prov}}_{\mathrm{fin\text{-}stoch}}\)
  for the finite stochastic PICA-style cell/pair/provenance fragment;
- \(\mathbf{BirdInt}^{\mathrm{AI}}_{\mathrm{fin}}\) for a finite
  abstract-interpretation fragment, if a compact name is needed;
- \(\mathbf{BirdInt}^{\mathrm{coh}}_{\mathrm{fin}}\) for finite graph/cohomology
  support fragments, if a compact name is needed.

Define any compact fragment notation before using it.

## Terminology Rules

### "Theory Package"

Use "theory package" for the inherited package object
\(\mathcal T=(Z,f,\Sigma_f,E,\mathcal A)\), possibly carrying additional
Foundations III typed records.

Do not use "package" vaguely when the statement depends on whether the object is
a carrier, lens, completion, audit, promotion bridge, or model realization.

### "Interaction"

Use "interaction" for typed Foundations III relationships between role labels,
typically represented by directed-cell, pair-observable, promotion, dependency,
or claim judgments.

Do not treat interaction as multiplication of primitives.

### "Bridge"

Use "bridge" for a typed finite object that relates levels, packages,
visibility contexts, promotions, or model-realization domains.

Specify the bridge type:

- visibility bridge;
- promotion bridge;
- model-realization bridge;
- instrument-transfer bridge;
- drive bridge.

### "Gate"

Use "gate" for a finite check whose pass/fail/blocked/outside-scope result
affects acceptance of a promotion, claim, realization, or interaction.

Do not use "gate" as a synonym for \(P_2\) unless the statement is specifically
about \(P_2\)-style representability/gating.

### "Audit"

Use "audit" broadly for \(P_6\)-side bookkeeping, provenance, replay,
checkability, or drive certification.

Use "drive certificate" only for the drive face \(P6_{\mathrm{drive}}\), not
for all audit.

### "Closure"

Use "closure" carefully:

- Foundations I order-closure operator: use when the host is a poset and the
  closure axioms apply.
- Completion/packaging endomap: use \(E\) when the object is an idempotent
  endomap but not necessarily an order-closure.
- Macro closure: use only for closed induced dynamics or package-supported
  macro dynamics.

Do not collapse these three senses.

### "Strict Extension"

Use "strict extension" for nonfactorization or genuine definability/interface
growth, not for repeated application of a fixed completion.

Strictness does not imply macro closure or drive unless an additional theorem
or bridge supplies that implication.

### "Model Realization"

Use "model realization" for a scoped interpretation of a fragment of
\(\mathbf{BirdInt}^{\mathrm{aud}}_{\mathrm{fin}}\) in a concrete finite host.

Always state:

- the host;
- the realized fragment;
- the realization map;
- the theorem supported;
- the nonclaims.

Do not write that PICA, Cantor, abstract interpretation, or graph/cohomology
realize the whole calculus unless a later theorem proves that exact claim.

## Notation To Avoid Unless Explicitly Justified

Avoid introducing new symbols for inherited objects without a reason:

- Do not replace \(\mathcal T\) for theory packages.
- Do not replace \(E\) for completion endomaps when the inherited object is
  meant.
- Do not replace \(\mathcal A\) for audit functionals when the inherited object
  is meant.
- Do not replace \(P_1,\ldots,P_6\) for primitive roles.
- Do not replace \(\mathsf{FATCD}\) when referring to the Foundations II domain.

Avoid ambiguous overloading:

- Do not use \(P\) both for the primitive set and a probability kernel in the
  same local proof without clarification.
- Do not use \(A\) for both an audit record and an audit functional.
- Do not use \(\sigma\) for both a status and \(\Sigma_f\)-style expressive
  content.
- Do not use "closure" when the exact object is completion, macro closure, or
  order closure.

## Recommended LaTeX Macro Block

When drafting the manuscript, define a notation block close to the preamble.
This keeps inherited notation stable while allowing the new Foundations III
objects.

```tex
% Foundations I / II inherited notation
\newcommand{\FATCD}{\ensuremath{\mathsf{FATCD}}}
\newcommand{\Raw}[1]{\ensuremath{\operatorname{Raw}\!\left(#1\right)}}
\newcommand{\Audit}[1]{\ensuremath{\operatorname{Audit}\!\left(#1\right)}}
\newcommand{\Closed}[1]{\ensuremath{\operatorname{Closed}\!\left(#1\right)}}
\newcommand{\Dec}[1]{\ensuremath{\operatorname{Dec}\!\left(#1\right)}}
\newcommand{\Residual}[1]{\ensuremath{\operatorname{Residual}\!\left(#1\right)}}
\newcommand{\Chan}[2]{\ensuremath{\operatorname{Chan}_{#1}\!\left(#2\right)}}
\newcommand{\Status}[2]{\ensuremath{\operatorname{Status}_{#1}\!\left(#2\right)}}
\newcommand{\ScopedExactSix}[1]{\ensuremath{\operatorname{ScopedExactSix}\!\left(#1\right)}}

\newcommand{\activeproj}{\texttt{active\_projection}}
\newcommand{\belowthr}{\texttt{below\_threshold}}
\newcommand{\collapsedbc}{\texttt{collapsed\_boundary\_case}}
\newcommand{\absentrec}{\texttt{absent\_with\_record}}
\newcommand{\outsidescope}{\texttt{inapplicable\_outside\_scope}}

\newcommand{\Pone}{\ensuremath{\mathrm{P1}}}
\newcommand{\Ptwo}{\ensuremath{\mathrm{P2}}}
\newcommand{\Pthree}{\ensuremath{\mathrm{P3}}}
\newcommand{\Pfour}{\ensuremath{\mathrm{P4}}}
\newcommand{\Pfive}{\ensuremath{\mathrm{P5}}}
\newcommand{\Psix}{\ensuremath{\mathrm{P6}}}
\newcommand{\Pdrive}{\ensuremath{\mathrm{P6}_{\mathrm{drive}}}}

% Foundations III notation
\newcommand{\BirdInt}{\ensuremath{\mathbf{BirdInt}}}
\newcommand{\BirdIntFinAud}{\ensuremath{\mathbf{BirdInt}^{\mathrm{aud}}_{\mathrm{fin}}}}
\newcommand{\Prim}{\ensuremath{\mathsf{Prim}}}
\newcommand{\Wit}{\ensuremath{\mathsf{Wit}}}
\newcommand{\Upd}{\ensuremath{\mathsf{Upd}}}
\newcommand{\Defect}{\ensuremath{\mathsf{Def}}}
\newcommand{\Gate}{\ensuremath{\mathsf{Gate}}}
\newcommand{\Real}{\ensuremath{\mathsf{Real}}}
\newcommand{\Vis}{\ensuremath{\mathsf{Vis}}}
\newcommand{\Supp}{\ensuremath{\mathsf{Supp}}}
```

The macro block is recommended, not mandatory. If the manuscript uses different
macro names, the rendered notation must still match this file's conventions.

## Standalone Drafting Rule

An agent drafting Foundations III should treat this file as sufficient for
notation and terminology. The agent may consult the earlier papers for proof
context, citations, or historical wording, but not to discover basic notation.

If a needed symbol or term is absent from this file:

1. first check whether an existing symbol here already denotes the same object;
2. if yes, reuse it;
3. if no, introduce a new symbol only with an explicit reason;
4. add the new symbol to this file before using it throughout the manuscript.

## Required Notation Checks Before Drafting

Before drafting any section, check:

1. Is every inherited object using inherited notation unless there is a reason
   to change it?
2. If notation is upgraded, is the upgrade explicitly motivated?
3. Does the section distinguish \(\mathcal A\) from \(A\)?
4. Does the section distinguish \(\mathsf{FATCD}\) from
   \(\mathbf{BirdInt}^{\mathrm{aud}}_{\mathrm{fin}}\)?
5. Does the section distinguish a role channel from an active witness?
6. Does the section distinguish the inherited channel-status taxonomy from new
   Foundations III status families?
7. Does the section distinguish \(P_6\) from \(P6_{\mathrm{drive}}\)?
8. Does the section avoid treating \(P_i\leftarrow P_j\) as primitive
   multiplication?
9. Does the section state the host when using model-realization notation?
10. Does the section avoid introducing a new letter when an established one
    already denotes the same object?
