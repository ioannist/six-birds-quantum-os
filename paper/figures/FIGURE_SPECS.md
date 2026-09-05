# Figure Specifications

Specification of every figure in the paper: what each shows, which CSV it is generated from, the exact
series/axis/annotation requirements, and the caption requirements. F3–F9 are produced by
`paper/figures/make_figures.py` from the experiment CSVs under `artifacts/` (regenerate with
`python paper/figures/make_figures.py`; byte-deterministic; tested by `tests/test_paper_figures.py`).
F1 and F2 are TikZ sources (`fig_F1_map.tex`, `fig_F2_cycle.tex`). Data values embedded below were copied
from the artifacts at the commit noted per section for cross-checking; the CSVs are the source of truth.

Figures are included at native size (`\includegraphics{figures/generated/<file>}`), so single-column
figures are 4.8in wide and full-width figures 6.5in.

---

## Shared style

```
STYLE (arXiv / LaTeX article, 11pt, 1in margins; text width is 6.5in):

- Output a vector PDF (and optionally a 300-dpi PNG preview). Transparent or white background.
- Figure size: this is a single-column article and figures are included at NATIVE size (no
  \includegraphics width scaling), so single figures are 4.8in wide and full-width figures 6.5in wide;
  height chosen for a 0.6-0.7 aspect ratio per panel. Never scale fonts down to fit; resize the figure.
- Minimum text size anywhere in a figure: 7pt (ticks, annotations, notes included).
- Typography: serif, matching Latin Modern / Computer Modern. In matplotlib use
  rcParams: font.family="serif", font.serif=["Latin Modern Roman","CMU Serif","Times"],
  mathtext.fontset="cm", font.size=9, axes.labelsize=9, legend.fontsize=8,
  xtick.labelsize=8, ytick.labelsize=8. Use LaTeX-style math in labels (e.g. $\mathrm{tr}\,\Xi$).
- No figure title inside the image. The LaTeX caption carries all interpretation.
- Axes: remove top and right spines; black 0.6pt axis lines; ticks outward; no gridlines,
  or at most a very light dotted y-grid (alpha 0.3). Line width 1.2pt; marker size 4pt.
- Colors: Okabe-Ito colorblind-safe palette only:
  black #000000, orange #E69F00, sky blue #56B4E9, green #009E73, yellow #F0E442,
  blue #0072B2, vermilion #D55E00, purple #CC79A7. Baselines/controls are always black;
  the paper's method series get the colored lines. Distinguish series by line style AND
  color (solid/dashed/dotted) so the figure survives grayscale printing.
- Legend: no frame, placed inside the axes where it does not overlap data; use the
  human-readable series names given in the prompt, not CSV column names. Documented exception: F7's
  legend has an opaque, borderless white background because the two reference lines cross its area.
- Panels in multi-panel figures share the y-axis, are labeled (a), (b), (c) in bold at the
  top-left corner, and have identical size.
- Do not round, smooth, interpolate, clip, or omit any value given in the prompt. If a value
  looks anomalous it is still real data and must be plotted as-is.
- Print the plotted arrays to stdout after saving so the numbers can be checked against the
  source table.
```

---

## F1 — The SBT-to-QEC instantiation map (conceptual)

> Shipped as TikZ, `paper/figures/fig_F1_map.tex`. The relations on the arrows below are the ones the
> results support; an earlier draft of this figure carried three wrong ones and was replaced at sign-off.

- **Placement:** §3, after the scope-fence list, `\label{fig:map}`.

```
Two-column mapping diagram, 6.5in wide, serif Latin Modern, thin 0.6pt borders, rounded corners, no
icons/shadows/gradients. Column headers (bold small caps): "Six Birds Theory primitive" | "QEC audit object".

A TOP BAND spanning both columns, light grey fill (#F2F2F2), no arrow, 8pt: "Packaging operator
E = U_f ∘ Q_f ∘ P^τ  =  the QEC cycle (noise → syndrome → recovery): the shared substrate of every audit;
not itself scored".

Six aligned rows below it, left box → arrow with 7-8pt label → right box:
1. "Existence / closure certificate (δ, ε, CD_τ, RM, multiplicity)" → "Logical-qubit objecthood status:
   certified / degrading / non-closed / trivialized". Label: "δ ≤ ε holds (theorem); status set by
   thresholds on δ, CD_τ and multiplicity". Solid.
2. "Adequacy residual Ξ(D|L), witness, chain rule" → "Syndrome-coverage audit (native + degree-2
   checks)". Label: "Ξ = K_DD − K_DL K_LL⁺ K_LD". Solid.
3. "Predictive quotient / memory witness (Q, M, Δ^max)" → "Decoder-memory certificate; minimal decoder
   machine". Label: "witness = same current class, different predictive class". Solid.
4. "Protocol trap / schedule internalization" → "Schedule-artifact vs. genuine-memory control". Label:
   "internalize the schedule, recompute witnesses (here all 4 survived)". Solid.
5. "Shadow price / slack point (V, λ, b*)" → "Check-budget economics". Label: "λ(b) = V(b+1) − V(b);
   evidence: negative". DASHED grey arrow; both boxes light grey fill.
6. "Transport / functoriality" → "(not instantiated)". Whole row grey (#BBBBBB), no arrow, right-aligned
   7pt italic "deferred, not implemented".

Legend, 7pt: "solid arrow = positively evidenced audit object (4); dashed = machinery exact, every
registered prediction failed (1); grey = deferred (1); top band = shared substrate, not scored".
Do NOT write "δ ≤ ε ⇒ certified", "M = |Q| > 1 ⇒ memory pays", or "witness vanishes after
internalization": each states a relation the results contradict.
```

- **Caption requirements:** the packaging band is substrate, not a scored primitive; four solid; the
  pricing sentence must be split so that "implemented exactly" and "every registered prediction failed"
  are separate sentences (one grade each); transport deferred.

## F2 — The diagnosis-and-repair cycle (conceptual)

> **Status (2026-09-05, redesigned):** shipped as TikZ, `paper/figures/fig_F2_cycle.tex`, as a rectangular two-row loop (top row S1→S2→S3 left to right, right side S3→S4, bottom row S4→S5 right to left, closing arrow S5→S1 up the left side; all arrows straight; the thesis sentence typeset horizontally inside the loop; E8/E9 as sub-boxes inside the "Generalization" stage). The circular/pentagon layouts were rejected at sign-off (short bent stubs, sloped label). Stage texts carry the corrected wording ("neither baseline meets the criterion within the grid", "predicted failure to beat the baseline held", E8 "met at the grid's thinnest margin", E9 "on a known drifting channel").

- **Placement:** §7 top, `sec_07_arc.tex`, first figure, before the numbers.
- **Filename:** `fig_F2_repair_cycle.pdf` (single column, 3.4in, or full width if the text does not fit).


- **Caption requirements:** the closing-arrow sentence appears in the caption verbatim. Give the predicted-negative-that-held more weight than the win (paper §7 text does this deliberately).

---

## F3 — Chain-rule check selection beats baselines at every budget (SURF(3), E3)

- **Placement:** §5, `sec_05_results_certificates.tex`, `\label{fig:coverage}`.
- **Filename:** `fig_F3_e3_coverage_vs_budget.pdf` (single column, 3.4in).
- **Source:** `artifacts/e3_default/bfb9ffc6/e3_coverage_vs_budget.csv`.

```
Specification (implemented in make_figures.py): a single-panel line chart from the data below.

x-axis: "check budget b" (integers 0-8, linear, ticks at every integer).
y-axis: "residual trace  $\mathrm{tr}\,\Xi$" (linear, from 0.15 to 0.45).

Series (legend names in quotes):
  "greedy (chain rule)"  — solid line, circle markers, blue #0072B2
  "lexicographic"        — dashed line, square markers, vermilion #D55E00
  "random (mean of 10 seeds)" — dotted line, no markers, black
  shaded band between random_min and random_max, light grey (#000000 at alpha 0.12),
  legend entry "random (min-max over 10 seeds)".

budget, greedy,               lex,                  random_mean,          random_min,           random_max
0,      0.434484420608,       0.434484420608,       0.434484420608,       0.434484420608,       0.434484420608
1,      0.3560513753705304,   0.3560513753705304,   0.3996255993394496,   0.3560513753705304,   0.434484420608
2,      0.2991940298827946,   0.3520520184472085,   0.3730979638347801,   0.32390055517709615,  0.4025484241924263
3,      0.2620865864748007,   0.3224651374551609,   0.34673655487145594,  0.3224651374551609,   0.39810714147649473
4,      0.230150590059227,    0.2773676144566584,   0.32041838224922564,  0.2644698450618803,   0.3661711450609211
5,      0.21223877333186683,  0.23418847925853864,  0.28399115608733305,  0.24107363050717323,  0.3172762734716599
6,      0.19765715326925165,  0.23027110824106595,  0.2495034676831882,   0.19987714189828676,  0.308267374781208
7,      0.18405024538986486,  0.18405024538986486,  0.2128184071528091,   0.18405024538986486,  0.23675153644199032
8,      0.17538887995719527,  0.17538887995719527,  0.17538887995719524,  0.17538887995719527,  0.17538887995719527

Note that all series coincide at b=0 and b=8 and greedy equals lex at b=1 and b=7; draw the
greedy series on top (highest zorder) so it stays visible where curves overlap.
```

- **Caption requirements:** greedy is at or below every baseline at every budget; a registered comparison against *tested* baselines, not a general optimality proof for b>1 (only b=1 is optimal by construction). Cite fact ids from `facts.md` as in the placeholder.

---

## F4 — Degree-ladder contraction attains the exact optimal MMSE (REP(3), E3)

- **Placement:** §5, `sec_05_results_certificates.tex`, `\label{fig:ladder}`.
- **Filename:** `fig_F4_e3_degree_ladder.pdf` (single column, 3.4in, short: ~2.2in tall).
- **Source:** `artifacts/e3_default/bfb9ffc6/e3_degree_ladder.csv`.

```
Specification (implemented in make_figures.py): a single-panel chart with two categorical x positions.

x-axis categories (in this order): "degree-1", "degree-2-complete". Axis label: "ladder rung".
y-axis: "residual trace  $\mathrm{tr}\,\Xi$", linear from 0 to 0.10.

Plot trace_xi as two bars (width 0.5, fill sky blue #56B4E9, black 0.6pt edge), and draw a
horizontal dashed black reference line across the whole axis at the mmse_floor value, labeled
in the legend "exact optimal-decoder MMSE = 47291/1715000".
Annotate each bar with its value in 7pt above the bar: "0.083680" and "0.027575".

rung, trace_xi,             mmse_floor
1,    0.08367977099236641,  0.027574927113702623
2,    0.027574927113702623, 0.027574927113702623

The second bar must sit exactly on the reference line (the difference is exactly 0.0 in exact
rational arithmetic); do not offset it for visibility.
```

- **Caption requirements:** state the exact fraction 47291/1715000, that rung 2 minus the floor is exactly 0, and why (the degree-2-complete family generates every function of the REP(3) syndrome, so its floor *is* the optimal-decoder MMSE). This is the one place the word "optimal" is allowed (claims.md C-10).

---

## F5 — Decoder-memory payoff-v2 NLL ladder (REP(3)+N4, E5)

- **Placement:** §5, `sec_05_results_certificates.tex`, `\label{fig:payoff}`.
- **Filename:** `fig_F5_e5_payoff_ladder.pdf` (full width, 6.5in, two panels side by side).
- **Source:** `artifacts/e5_default/941e4f34/e5_payoff_v2_ladder.csv`.

```
Specification (implemented in make_figures.py): a two-panel bar chart (panels (a) and (b), shared y-axis).

Panel (a) title-in-corner: "frozen defaults". Panel (b): "loud mode".
x-axis: ten predictors in this fixed order, tick labels rotated 45 degrees:
  oracle, exact filter, run-length K=2, K=4, K=8, K=16, rounding K=2, K=4, K=8, K=16.
Insert a thin vertical dotted divider between "exact filter" and "run-length K=2" and another
between "run-length K=16" and "rounding K=2". Color groups: oracle black; exact filter blue
#0072B2; run-length bars green #009E73; rounding bars vermilion #D55E00.
y-axis: "NLL gap vs. static predictor (nats / round)". The axis MUST include negative values;
do not clip at zero. Draw a solid black zero line. Use the same y-range on both panels, from
-0.08 to +0.065.
The "static" row (gap 0.0) is the reference and is represented by the zero line, not a bar.

point,           predictor,      gap
frozen_defaults, oracle,          0.010610683791784647
frozen_defaults, exact_filter,    0.0019555946458122975
frozen_defaults, run_length_K2,   0.00014990331257269673
frozen_defaults, run_length_K4,   0.00039084583742104995
frozen_defaults, run_length_K8,   0.0008050817401397126
frozen_defaults, run_length_K16,  0.0009133989134531562
frozen_defaults, rounding_K2,    -0.004734536660328081
frozen_defaults, rounding_K4,    -0.0061612657180165065
frozen_defaults, rounding_K8,    -0.005285668243491082
frozen_defaults, rounding_K16,   -0.003747357328565404
loud_mode,       oracle,          0.058335528953413984
loud_mode,       exact_filter,    0.03615016176755015
loud_mode,       run_length_K2,   0.004289397286800778
loud_mode,       run_length_K4,   0.008848778123807133
loud_mode,       run_length_K8,   0.010518443617859363
loud_mode,       run_length_K16,  0.010356102169596149
loud_mode,       rounding_K2,    -0.0703496611486325
loud_mode,       rounding_K4,    -0.04440285412943701
loud_mode,       rounding_K8,    -0.03750137706612855
loud_mode,       rounding_K16,    0.030134888818091232

The loud-mode rounding K=16 bar is positive (+0.0301) while its siblings are negative. This is
a real measured value; plot it as-is and add a small 7pt annotation "+0.0301" above it.
In panel (a) the bars are too small to read on the shared scale: print each bar's value (signed,
2 significant figures, 7pt, rotated 90°) just beyond the bar's end.
```

- **Caption requirements:** oracle is a ceiling, not deployable; exact filter is the realistic upper bound; run-length machines are positive and generally improve with K (note the slight loud-mode decline from K=8, 0.010518, to K=16, 0.010356: do not write "grows with K" unqualified); rounding machines are mostly negative except the loud-mode K=16 point, which is a real reported result, not an error bar.

---

## F6 — E7 corrected witness ladder: detection fraction vs. shots, three scenarios

- **Placement:** §7, `sec_07_arc.tex`, `\label{fig:e7-ladder}` (the paper's centerpiece figure).
- **Filename:** `fig_F6_e7_detection_ladder.pdf` (full width, 6.5in, three panels).
- **Source:** `artifacts/e7_default/ab6885e6/e7_detection_latency.csv`.

```
Specification (implemented in make_figures.py): three side-by-side panels with a shared y-axis.

Panel (a) "(0,3): original E2 scenario", panel (b) "(2,5): near parity", panel (c) "(4,8):
off both logical supports". Put these as 8pt text in the top-left of each panel.
x-axis: "shots N" on a log scale with ticks exactly at 250, 500, 1000, 2000, 4000, 8000, 16000
(plain integer labels, no scientific notation).
y-axis: "detection fraction (10 seeds)", from -0.02 to 1.02, ticks at 0, 0.5, 1.

Five series per panel, identical styling across panels, one shared legend below the panels
in one row:
  "W2a: legacy statistic, recalibrated null"                 solid,  sky blue #56B4E9, circle markers
  "W2b: quadratic statistic (W2c naming shares this curve)"  solid,  blue #0072B2, square markers, line width 1.6pt (headline)
  "W2d: sequential (CUSUM)"                                  dashed, green #009E73, triangle markers
  (Ladder semantics per design/06_W2_PHASE2.md §3.2: W2a = the OLD lifted statistic with only its null
  recalibrated, W2b = the corrected degree-≤2 quadratic statistic, W2c = matched-filter naming whose
  detection curve is W2b's, W2d = CUSUM wrapper on W2b. Legend in two rows of three below the panels.)
  "baseline"                 solid,  black, x markers
  "baseline CUSUM"           dashed, black, plus markers

scenario, N,     w2a, w2b, w2d, baseline, baseline_cusum
0_3,      250,   0.0, 0.0, 0.0, 0.2, 0.0
0_3,      500,   0.1, 0.0, 0.0, 0.5, 0.0
0_3,      1000,  0.1, 0.1, 0.0, 1.0, 0.2
0_3,      2000,  0.1, 0.8, 0.0, 1.0, 1.0
0_3,      4000,  0.2, 1.0, 0.1, 1.0, 1.0
0_3,      8000,  0.3, 1.0, 0.8, 1.0, 1.0
0_3,      16000, 0.3, 1.0, 0.9, 1.0, 1.0
2_5,      250,   0.0, 0.1, 0.0, 0.4, 0.0
2_5,      500,   0.0, 0.2, 0.0, 0.7, 0.0
2_5,      1000,  0.1, 0.2, 0.0, 1.0, 0.3
2_5,      2000,  0.0, 1.0, 0.1, 1.0, 1.0
2_5,      4000,  0.0, 1.0, 0.4, 1.0, 1.0
2_5,      8000,  0.1, 1.0, 1.0, 1.0, 1.0
2_5,      16000, 0.1, 1.0, 1.0, 1.0, 1.0
4_8,      250,   0.1, 0.5, 0.0, 0.0, 0.0
4_8,      500,   0.0, 0.8, 0.0, 0.0, 0.0
4_8,      1000,  0.0, 1.0, 0.1, 0.1, 0.0
4_8,      2000,  0.0, 1.0, 1.0, 0.1, 0.0
4_8,      4000,  0.1, 1.0, 1.0, 0.0, 0.0
4_8,      8000,  0.0, 1.0, 1.0, 0.1, 0.3
4_8,      16000, 0.1, 1.0, 1.0, 0.1, 0.8

Where several series sit exactly on top of each other (e.g. all at 1.0), apply a tiny vertical
jitter of at most 0.015 so markers remain distinguishable, and say so in a 6pt note under
panel (c): "markers at coincident values are offset by ≤0.015 for legibility".
```

- **Caption requirements:** identify each panel's scenario; for panel (a) say the baseline detecting first was the *registered, expected* outcome (P7.3, claims.md C-31), not a surprise; for panel (c) say both baselines never detect within the grid while the corrected rungs do (C-30, bar was 10x).

---

## F7 — E7 naming: modal qubit and direction overlap

- **Placement:** §7, `sec_07_arc.tex`, `\label{fig:naming}`, right after F6. May be folded into a table instead (three rows only).
- **Filename:** `fig_F7_e7_naming_overlap.pdf` (single column, 3.4in, ~2.2in tall).
- **Source:** `artifacts/e7_default/ab6885e6/e7_naming_overlap.csv`.

```
Specification (implemented in make_figures.py): a grouped bar chart with three categorical x positions.

x-axis categories (in this order): "(0,3)", "(2,5)", "(4,8)"; axis label "injection pair".
Two bars per category:
  "mean logical-direction overlap"  fill blue #0072B2
  "seeds naming a true-pair qubit / 10"  fill orange #E69F00
y-axis from 0 to 1, label "fraction".
Horizontal dashed black line at 0.6 labeled "registered overlap bar (0.6)"; horizontal dotted
black line at 0.8 labeled "registered naming bar (8/10)".
Annotate the (4,8) bars with "0.869" and "3/10" in 7pt.

scenario, modal_qubit, named_in_pair_count, mean_overlap
0_3,      7,           0,                   0.07882840831208546
2_5,      8,           0,                   0.2529763995597246
4_8,      5,           3,                   0.868781895694894

The registered naming prediction (P7.5) concerns the off-support pair (4,8); the other two
pairs are shown for context only. Do not omit them.
```

- **Caption requirements:** the P7.5 split stated plainly: direction overlap 0.869 clears the 0.6 bar, qubit naming 3/10 fails the 8/10 bar (registered-negative, C-32); reading marked as interpretation: SURF(3) has only two logical operators, so overlap is a coarse, near-binary check.

---

## F8 — E8 circuit-level detection fractions (global drift)

- **Placement:** §7, `sec_07_arc.tex`, `\label{fig:e8}`.
- **Filename:** `fig_F8_e8_circuit_level.pdf` (single column, 3.4in).
- **Source:** `artifacts/e8_default/cf7094d8/e8_detection_latency.csv`.

```
Specification (implemented in make_figures.py): a single-panel line chart.

x-axis: "detector-stream shots $N$" (reserve $N_{\mathrm{det}}$ for the two threshold values), log scale, ticks exactly at 10, 20, 50,
100, 250, 500, 1000, 2000 with plain integer labels.
y-axis: "detection fraction (10 seeds)", from -0.02 to 1.02.

Series:
  "corrected witness (W2b)"  solid, blue #0072B2, square markers
  "pymatching baseline"      solid, black, x markers

N,    witness_frac, baseline_frac
10,   0.4,          0.1
20,   0.8,          0.1
50,   1.0,          0.4
100,  1.0,          1.0
250,  1.0,          1.0
500,  1.0,          1.0
1000, 1.0,          1.0
2000, 1.0,          1.0

Draw two vertical dotted lines: at N=50 (blue, labeled "witness reaches 1.0 at N=50") and at
N=100 (black, labeled "baseline reaches 1.0 at N=100"), labels in 7pt placed near the top of
the axes. Add a 7pt annotation between them: "ratio 2x = registered bar, exactly".
```

- **Caption requirements (mandatory, same sentence as the result):** the witness clears the registered 2x bar exactly, at the thinnest margin this discrete grid can resolve, not a comfortable win (claims.md C-33). Do not let the caption imply a wide margin.

---

## F9 — E9 closed-loop policy comparison: post-drift error and recalibration budget

- **Placement:** §7, `sec_07_arc.tex`, `\label{fig:e9}`, the arc's final figure.
- **Filename:** `fig_F9_e9_closed_loop.pdf` (single column, 3.4in).
- **Source:** `artifacts/e9_default/f24323a0/e9_post_drift_error.csv`.

```
Specification (implemented in make_figures.py): a single-panel bar chart with five categorical positions.

x-axis policies in this fixed left-to-right order (tick labels on two lines where needed):
  "static", "scheduled\n(budget-matched)", "scheduled\n(frequent)", "witness-triggered", "oracle".
Bar fills: static and oracle grey #BBBBBB (floor and ceiling references); the two scheduled
policies black; witness-triggered blue #0072B2. Black 0.6pt bar edges.
y-axis: "mean post-drift logical error (10 seeds)", from 0.08 to 0.125 (a broken or clipped
axis is acceptable here because the zero is not informative, but say "axis starts at 0.08" in
7pt inside the plot).
Above each bar, annotate in 7pt: "recalibrations: <value>" using the mean_recalibration_events
column. For witness-triggered and scheduled (budget-matched) use a bold annotation, since
both spend exactly 1.6 events per seed.

policy,             mean_post_drift_error, mean_recalibration_events
static,             0.11854666666666666,   0.0
scheduled_matched,  0.11146666666666667,   1.6
scheduled_frequent, 0.09462666666666666,   8.0
witness,            0.093,                 1.6
oracle,             0.09157333333333333,   0.0

Draw a thin horizontal dashed grey line at the oracle value across the axis labeled "oracle
ceiling" in 7pt.
```

- **Caption requirements:** state the matched-budget fact in words (witness and the budget-matched schedule spend identical realized event counts per seed, 1.6 each, C-34); state the P9.3 caveat: the frequent schedule spends about 5x the budget and its 0.0016 deficit to the witness is smaller than the paired standard error of about 0.002 at 10 seeds, so that contrast is statistically unresolved (C-35). Do not caption it as "witness still wins".

---

## LaTeX inclusion

Each figure is included at native size, keeping its `\label{}`:

```latex
\includegraphics[width=\linewidth]{figures/generated/fig_F3_e3_coverage_vs_budget.pdf}
```

For full-width figures inside a single-column article this is identical; if the paper ever moves to a two-column class, use `figure*` for F1, F5, and F6.

## Checklist before committing a regenerated figure

- [ ] Plotted values checked against the CSV (the script prints its arrays).
- [ ] Fonts are serif and no text is smaller than 7pt at final size.
- [ ] No title inside the image; caption meets the per-figure requirements and carries its fact ids.
- [ ] Anomalous values (F5 loud-mode rounding K=16, F8 exact-2x margin, F9 frequent-vs-witness gap) are visible, not trimmed.
- [ ] File saved as vector PDF under `paper/figures/generated/` and `latexmk` builds clean.
