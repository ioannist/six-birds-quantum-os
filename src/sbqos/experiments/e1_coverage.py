"""E1 coverage audit runner."""

from __future__ import annotations

from itertools import combinations

import numpy as np

from sbqos.artifacts import Run, parse_fraction
from sbqos.codes import Code, PauliVec, canonical_rep, logical_flips, rep_code, surface_code, syndrome
from sbqos.experiments.common import main_template, setup_matplotlib
from sbqos.moments import MomentEngine, ProbeFamily
from sbqos.noise import n1, n2
from sbqos.xi import blind_spot_witness, discharge, xi_residual

setup_matplotlib()
import matplotlib.pyplot as plt


def main(config_path: str) -> None:
    main_template(config_path, _run)


def _run(config: dict, run: Run) -> None:
    seed = int(config["seed"])
    del seed
    rep3_p = parse_fraction(config["rep3_p"])
    rep5_p = parse_fraction(config["rep5_p"])
    surf3_p = parse_fraction(config["surf3_p"])

    specs = (
        _Spec("rep3", rep_code(3), "N1", rep3_p),
        _Spec("rep5", rep_code(5), "N1", rep5_p),
        _Spec("surf3", surface_code(3), "N2", surf3_p),
    )

    full = {}
    ablations = {}
    exhaustive = {}
    bounded = {}
    duplicate = {}

    for spec in specs:
        engine = _engine(spec)
        L_full = _checks_family(spec.code)
        D = _logical_family(spec)
        blocks = engine.cov_blocks(L_full, D)
        Xi_full, A_star = xi_residual(blocks)
        full[spec.name] = {"trace_xi": _trace(Xi_full)}
        ablations[spec.name] = _single_drop_ablations(spec, engine, D, full[spec.name]["trace_xi"])
        duplicate[spec.name] = _duplicate_discharge(engine, L_full, D, spec.code.checks[0])
        if spec.name.startswith("rep"):
            exhaustive[spec.name] = _rep_exhaustive(spec, engine, D)
            bounded[spec.name] = _bounded_weight_check(spec.code, engine, L_full, D, A_star)

    exact_float_control = _exact_float_control((specs[0], specs[1]))
    surf_ablations = ablations["surf3"]
    surf_overlap_failures = [row for row in surf_ablations if row["overlap"] < 0.9]
    surf_direction_ok = all(row["direction_correct"] for row in surf_ablations)
    p12 = _p12_values(ablations)

    predictions = [
        {
            "id": "P1.1",
            "statement": "REP full-check residual bound and distance suppression",
            "verdict": "registered-negative",
            "grade": "registered-negative",
            "values": {
                "rep3_trace": full["rep3"]["trace_xi"],
                "rep3_threshold": 1e-2,
                "rep5_trace": full["rep5"]["trace_xi"],
                "rep3_over_rep5_ratio": full["rep3"]["trace_xi"] / full["rep5"]["trace_xi"],
                "registered_min_ratio": 10.0,
            },
            "interpretation": (
                "The registered bound was written at logical-error-probability scale; "
                "tr Xi is the linear-estimator MMSE of a +/-1 observable and is not that quantity."
            ),
        },
        {
            "id": "P1.2",
            "statement": "single-check ablations strictly increase residual, with REP(5) end/middle distinction recorded",
            "verdict": "registered-positive" if p12["all_positive"] and p12["rep5_end_middle_differ"] else "registered-negative",
            "grade": "registered-positive" if p12["all_positive"] and p12["rep5_end_middle_differ"] else "registered-negative",
            "values": p12,
        },
        {
            "id": "P1.3",
            "statement": "witness overlap threshold and directional naming",
            "verdict": "registered-negative" if surf_overlap_failures else "registered-positive",
            "grade": "registered-negative" if surf_overlap_failures else "registered-positive",
            "values": {
                "surf3_overlaps": [row["overlap"] for row in surf_ablations],
                "threshold": 0.9,
                "direction_correct_all": surf_direction_ok,
                "failures": [row["check_label"] for row in surf_overlap_failures],
            },
            "interpretation": (
                "Some SURF(3) overlaps miss the frozen 0.9 threshold, while every Z-type drop names "
                "Zbar and every X-type drop names Xbar."
            ),
        },
        {
            "id": "P1.4",
            "statement": "duplicated-check saturation gives zero discharge",
            "verdict": "registered-positive" if all(row["value"] == 0.0 for row in duplicate.values()) else "registered-negative",
            "grade": "registered-positive" if all(row["value"] == 0.0 for row in duplicate.values()) else "registered-negative",
            "values": duplicate,
        },
    ]

    results = {
        "experiment": "e1",
        "claim_grade": "exact-finite",
        "full": full,
        "single_check_ablations": ablations,
        "rep_exhaustive_subsets": exhaustive,
        "bounded_weight_cross_check": bounded,
        "duplicate_saturation": duplicate,
        "exact_vs_float_control": exact_float_control,
        "predictions": predictions,
    }
    run.write_result(results)
    _save_rep5_figure(run, exhaustive["rep5"])
    _save_surf_witness_figure(run, surf_ablations)


class _Spec:
    def __init__(self, name: str, code: Code, noise: str, p):
        self.name = name
        self.code = code
        self.noise = noise
        self.p = p


def _engine(spec: _Spec, exact: bool = True) -> MomentEngine:
    if spec.noise == "N1":
        model = n1(spec.p, spec.code.n)
    elif spec.noise == "N2":
        model = n2(spec.p, spec.code.n)
    else:
        raise ValueError(f"unsupported E1 noise model: {spec.noise!r}")
    return MomentEngine(model, exact=exact)


def _checks_family(code: Code, indices: tuple[int, ...] | None = None) -> ProbeFamily:
    if indices is None:
        vecs = code.checks
        labels = tuple(f"h{i}" for i in range(len(code.checks)))
    else:
        vecs = tuple(code.checks[i] for i in indices)
        labels = tuple(f"h{i}" for i in indices)
    return ProbeFamily("native", vecs, labels)


def _logical_family(spec: _Spec) -> ProbeFamily:
    if spec.name.startswith("rep"):
        return ProbeFamily("logical", (spec.code.logicals[1],), ("Zbar",))
    return ProbeFamily("logical", spec.code.logicals, ("Xbar", "Zbar"))


def _single_drop_ablations(spec: _Spec, engine: MomentEngine, D: ProbeFamily, full_trace: float) -> list[dict]:
    rows = []
    omega = np.zeros((len(D.vecs), len(D.vecs)), dtype=float)
    for drop in range(len(spec.code.checks)):
        kept = tuple(i for i in range(len(spec.code.checks)) if i != drop)
        L = _checks_family(spec.code, kept)
        Xi, _ = xi_residual(engine.cov_blocks(L, D))
        witness = blind_spot_witness(Xi, omega, D.labels)
        z = np.asarray(witness.z, dtype=float)
        named_idx = int(np.argmax(np.abs(z)))
        denom = float(np.sum(z * z))
        overlap = float((z[named_idx] ** 2) / denom) if denom else 0.0
        check_type = _check_type(spec.code.checks[drop])
        expected = _expected_logical_for_drop(spec, check_type)
        named = D.labels[named_idx]
        trace = _trace(Xi)
        rows.append(
            {
                "check_index": drop,
                "check_label": f"h{drop}",
                "check_type": check_type,
                "trace_xi": trace,
                "delta_trace": trace - full_trace,
                "lambda_max": float(witness.lam_max),
                "witness_z": [float(x) for x in z],
                "named_logical": named,
                "expected_logical": expected,
                "direction_correct": named == expected,
                "overlap": overlap,
            }
        )
    return rows


def _p12_values(ablations: dict[str, list[dict]]) -> dict:
    per_code = {
        code_name: [row["delta_trace"] for row in rows]
        for code_name, rows in ablations.items()
    }
    all_deltas = [delta for deltas in per_code.values() for delta in deltas]
    rep5 = per_code["rep5"]
    end_values = [rep5[0], rep5[3]]
    middle_values = [rep5[1], rep5[2]]
    end_mean = float(np.mean(np.asarray(end_values, dtype=float)))
    middle_mean = float(np.mean(np.asarray(middle_values, dtype=float)))
    if end_mean > middle_mean:
        ordering = "end_larger"
    elif middle_mean > end_mean:
        ordering = "middle_larger"
    else:
        ordering = "equal"
    return {
        "single_drop_deltas": per_code,
        "all_positive": all(delta > 0.0 for delta in all_deltas),
        "rep5_end_values": end_values,
        "rep5_middle_values": middle_values,
        "rep5_end_mean": end_mean,
        "rep5_middle_mean": middle_mean,
        "rep5_end_middle_differ": end_mean != middle_mean,
        "rep5_end_middle_ordering": ordering,
    }


def _check_type(vec: PauliVec) -> str:
    n = len(vec) // 2
    has_x = bool(np.any(vec[:n]))
    has_z = bool(np.any(vec[n:]))
    if has_x and has_z:
        return "mixed"
    return "X" if has_x else "Z"


def _expected_logical_for_drop(spec: _Spec, check_type: str) -> str:
    if spec.name.startswith("rep"):
        return "Zbar"
    if check_type == "Z":
        return "Zbar"
    if check_type == "X":
        return "Xbar"
    return "unknown"


def _rep_exhaustive(spec: _Spec, engine: MomentEngine, D: ProbeFamily) -> list[dict]:
    rows = []
    m = len(spec.code.checks)
    for mask in range(1 << m):
        indices = tuple(i for i in range(m) if (mask >> i) & 1)
        Xi, _ = xi_residual(engine.cov_blocks(_checks_family(spec.code, indices), D))
        rows.append({"subset_mask": mask, "size": len(indices), "trace_xi": _trace(Xi)})
    return rows


def _bounded_weight_check(code: Code, engine: MomentEngine, L: ProbeFamily, D: ProbeFamily, A_star) -> dict:
    t = (code.n - 1) // 2
    total = 0
    passed = 0
    failures = []
    A = np.asarray(A_star, dtype=float)
    # The A_star decoder is affine on the +/-1 outcomes: mean_D + A(sigma_L - mean_L).
    # A_star maps centered variables, so the mean terms are part of the estimator.
    mean_D = float(engine.mean(D.vecs[0]))
    mean_L = np.asarray([float(engine.mean(vec)) for vec in L.vecs], dtype=float)
    for weight in range(t + 1):
        for support in combinations(range(code.n), weight):
            e = np.zeros(2 * code.n, dtype=np.uint8)
            for q in support:
                e[q] = 1
            s_bits = syndrome(code, e)
            check_outcomes = 1.0 - 2.0 * np.asarray(s_bits, dtype=float)
            estimate = mean_D + float((A @ (check_outcomes - mean_L))[0])
            predicted = 1 if estimate >= 0.0 else -1
            true = 1 - 2 * int(logical_flips(code, e)[1])
            total += 1
            if predicted == true:
                passed += 1
            else:
                failures.append({"support": list(support), "estimate": estimate, "true": true})
            r = canonical_rep(code, s_bits)
            decoded = e ^ r
            if int(logical_flips(code, decoded)[1]) != int(logical_flips(code, e)[1] ^ logical_flips(code, r)[1]):
                raise AssertionError("logical-flip XOR sanity check failed")
    return {"max_weight": t, "passed": passed, "total": total, "ok": passed == total, "failures": failures}


def _duplicate_discharge(engine: MomentEngine, L_full: ProbeFamily, D: ProbeFamily, duplicate: PauliVec) -> dict:
    blocks = engine.cov_blocks(L_full, D)
    M = ProbeFamily("candidate", (duplicate,), ("h0_dup",))
    ext = engine.extend_blocks(blocks, M)
    matrix, value = discharge(ext, (0,))
    exact_zero = value == 0.0 and np.all(np.asarray(matrix, dtype=float) == 0.0)
    if not exact_zero:
        raise AssertionError("duplicate-check discharge was not zero")
    return {"value": float(value), "exact_zero": bool(exact_zero)}


def _exact_float_control(specs: tuple[_Spec, ...]) -> dict:
    diffs = {}
    for spec in specs:
        D = _logical_family(spec)
        L_full = _checks_family(spec.code)
        exact_trace = _trace(xi_residual(_engine(spec, exact=True).cov_blocks(L_full, D))[0])
        float_trace = _trace(xi_residual(_engine(spec, exact=False).cov_blocks(L_full, D))[0])
        diffs[spec.name] = abs(exact_trace - float_trace)
    return {"max_abs_diff": max(diffs.values()), "per_code": diffs, "ok": max(diffs.values()) <= 1e-12}


def _save_rep5_figure(run: Run, rows: list[dict]) -> None:
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.scatter([row["size"] for row in rows], [row["trace_xi"] for row in rows], color="black", s=24)
    ax.set_xlabel("subset size")
    ax.set_ylabel("tr Xi")
    ax.set_title("REP(5) residual by check subset")
    run.save_figure(
        fig,
        "rep5_trace_by_subset_size",
        [[row["subset_mask"], row["size"], row["trace_xi"]] for row in rows],
        ["subset_mask", "size", "trace_xi"],
    )
    plt.close(fig)


def _save_surf_witness_figure(run: Run, rows: list[dict]) -> None:
    fig, ax = plt.subplots(figsize=(7, 4))
    labels = [row["check_label"] for row in rows]
    overlaps = [row["overlap"] for row in rows]
    ax.bar(labels, overlaps, color="black")
    ax.axhline(0.9, color="gray", linestyle="--", linewidth=1)
    ax.set_xlabel("dropped check")
    ax.set_ylabel("witness overlap")
    ax.set_title("SURF(3) single-drop witness overlap")
    run.save_figure(
        fig,
        "surf3_witness_overlap",
        [[row["check_label"], row["check_type"], row["overlap"], row["named_logical"]] for row in rows],
        ["check_label", "check_type", "overlap", "named_logical"],
    )
    plt.close(fig)


def _trace(M) -> float:
    return float(np.trace(np.asarray(M, dtype=float)))


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m sbqos.experiments.e1_coverage <config.json>")
    main(sys.argv[1])
