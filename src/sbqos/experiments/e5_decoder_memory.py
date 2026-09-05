"""E5 decoder-memory quotient experiment runner."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from types import MappingProxyType

import numpy as np

from sbqos import rng as project_rng
from sbqos.artifacts import Run, parse_fraction
from sbqos.codes import rep_code
from sbqos.experiments.common import main_template, setup_matplotlib
from sbqos.markov import MarkovModel, _delta_distribution, qec_markov_model, rep3_n1_model, rep3_n4_model, rep3_n5_model
from sbqos.noise import NoiseModel, n1, n4
from sbqos.quotients import Package, QuotientPair, currentization_search, internalize_schedule, rep3_n1_package

setup_matplotlib()
import matplotlib.pyplot as plt


def main(config_path: str) -> None:
    main_template(config_path, _run)


@dataclass(frozen=True)
class _Machine:
    nodes: tuple[tuple[int, int], ...]
    edges: tuple[dict, ...]
    likelihoods: dict
    logical_maps: tuple[dict[int, tuple[Fraction, Fraction]], dict[int, tuple[Fraction, Fraction]]]
    degenerate: bool
    exact_orbit: dict


def _run(config: dict, run: Run) -> None:
    seed = int(config["seed"])
    n4_p0 = parse_fraction(config["n4_p0"])
    n4_s = parse_fraction(config["n4_s"])
    n5_p = parse_fraction(config["n5_p"])
    n5_r = parse_fraction(config["n5_r"])
    trap_p0 = parse_fraction(config["trap_p0"])
    trap_p1 = parse_fraction(config["trap_p1"])
    alpha = parse_fraction(config["alpha"])
    payoff_rounds = int(config["payoff_rounds"])
    bfs_depth = int(config["belief_bfs_depth"])
    bfs_cap = int(config["belief_bfs_cap"])

    memoryless_pkg = rep3_n1_package()
    n4_noise = n4(n4_p0, n4_s, 3)
    n4_model = rep3_n4_model(n4_p0, n4_s, exact=True)
    n4_pkg = _hidden_package(n4_model)
    n5_model = rep3_n5_model(n5_p, n5_r, decoder="minimum_weight", exact=True)
    n5_pkg = _hidden_package(n5_model)
    trap = _trap_packages(trap_p0, trap_p1, alpha)

    quotients = {
        "memoryless_n1": _quotient_summary(memoryless_pkg),
        "n4_hidden": _quotient_summary(n4_pkg),
        "n5_latching": _quotient_summary(n5_pkg),
        "trap_naive": _quotient_summary(trap["naive"]),
        "trap_internalized": _quotient_summary(trap["internalized"]),
    }
    currentization = {
        "n4_hidden": _currentization_summary(n4_pkg, n4_model),
        "n5_latching": _currentization_summary(n5_pkg, n5_model),
    }
    _require_frozen_n4_for_belief_machine(n4_p0, n4_s)
    if n4_noise.hidden is None:
        raise ValueError("E5 N4 noise construction must carry hidden mode models")
    machine = _belief_machine(n4_model, n4_s, bfs_depth, bfs_cap, n4_noise.hidden.mode_models)
    payoff = {
        "memoryless_n1": _payoff_memoryless(rep3_n1_model("minimum_weight", exact=True), payoff_rounds, seed),
        "n4_hidden": _payoff_hidden(n4_model, machine, payoff_rounds, seed + 1),
    }
    payoff_v2 = _payoff_v2_study(
        config["payoff_v2_points"],
        int(config["payoff_v2_rounds"]),
        tuple(int(k) for k in config["payoff_v2_run_length_Ks"]),
        tuple(int(k) for k in config["payoff_v2_rounding_Ks"]),
        seed,
    )
    predictions = _predictions(quotients, currentization, machine, payoff)
    results = {
        "experiment": "e5",
        "claim_grade": "exact-finite",
        "quotients": quotients,
        "protocol_trap": {
            "classification": (
                "artifact_trap"
                if quotients["trap_naive"]["witness_count"] > 0 and quotients["trap_internalized"]["witness_count"] == 0
                else "genuine_memory_after_internalization"
            ),
            "naive_witness_count": quotients["trap_naive"]["witness_count"],
            "internalized_witness_count": quotients["trap_internalized"]["witness_count"],
            "internalized_delta_max": quotients["trap_internalized"]["delta_max"],
        },
        "currentization": currentization,
        "minimal_machine": _machine_summary(machine),
        "payoff": payoff,
        "payoff_v2": payoff_v2,
        "predictions": predictions,
    }
    run.write_result(results)
    _save_machine_figure(run, machine)
    _save_trap_figure(run, results["protocol_trap"])
    _save_payoff_figure(run, payoff, quotients["n4_hidden"]["delta_max_float"])
    _save_payoff_v2_figure(run, payoff_v2)


def _hidden_package(model: MarkovModel) -> Package:
    n_states = len(model.states)
    histories = []
    for syndrome in range(2**model.n_syndrome_bits):
        for mode in (0, 1):
            fiber = [i for i, state in enumerate(model.states) if int(model.lens_syndrome[i]) == syndrome and state[-1] == mode]
            mass = Fraction(1, len(fiber))
            histories.append(tuple(mass if i in fiber else Fraction(0) for i in range(n_states)))
    now_events = _syndrome_events(model)
    later_events = now_events + (_event_from_int_lens(model.lens_decoded),)
    one_round = _matrix_tuple(model.P)
    two_rounds = _matmul(one_round, one_round)
    continuations = MappingProxyType({"one_round": one_round, "two_rounds": two_rounds})
    later_pairs = tuple((gamma, event_idx) for gamma in ("one_round", "two_rounds") for event_idx in range(len(later_events)))
    return Package(
        states=model.states,
        histories=tuple(histories),
        continuations=continuations,
        now_events=now_events,
        later_events=later_events,
        later_pairs=later_pairs,
    )


def _trap_packages(p0: Fraction, p1: Fraction, alpha: Fraction) -> dict:
    code = rep_code(3)
    base0 = qec_markov_model(code, n1(p0, code.n), code.logicals[1:], "minimum_weight", exact=True)
    base1 = qec_markov_model(code, n1(p1, code.n), code.logicals[1:], "minimum_weight", exact=True)
    phases = (_matrix_tuple(base0.P), _matrix_tuple(base1.P))
    states = tuple(base0.states[coset] + (phase,) for coset in range(len(base0.states)) for phase in (0, 1))
    n_joint = len(states)
    histories = []
    for syndrome in range(2**base0.n_syndrome_bits):
        for phase in (0, 1):
            fiber = [
                coset * 2 + phase
                for coset in range(len(base0.states))
                if int(base0.lens_syndrome[coset]) == syndrome
            ]
            mass = Fraction(1, len(fiber))
            histories.append(tuple(mass if i in fiber else Fraction(0) for i in range(n_joint)))
    now_events = tuple(
        tuple(Fraction((int(base0.lens_syndrome[i // 2]) >> (base0.n_syndrome_bits - 1 - bit)) & 1) for i in range(n_joint))
        for bit in range(base0.n_syndrome_bits)
    )
    later_events = now_events + (
        tuple(Fraction(int(base0.lens_decoded[i // 2])) for i in range(n_joint)),
    )
    naive = [[Fraction(0) for _ in range(n_joint)] for _ in range(n_joint)]
    for coset in range(len(base0.states)):
        for phase in (0, 1):
            i = coset * 2 + phase
            P_phase = phases[phase]
            next_phase = 1 - phase
            for next_coset, prob in enumerate(P_phase[coset]):
                if prob:
                    naive[i][next_coset * 2 + next_phase] += prob
    naive_matrix = tuple(tuple(row) for row in naive)
    naive_pkg = Package(
        states=states,
        histories=tuple(histories),
        continuations=MappingProxyType({"one_round": naive_matrix}),
        now_events=now_events,
        later_events=later_events,
        later_pairs=(("one_round", 0), ("one_round", 1), ("one_round", 2)),
    )
    return {"naive": naive_pkg, "internalized": internalize_schedule(naive_pkg, phases, alpha)}


def _quotient_summary(pkg: Package) -> dict:
    result = QuotientPair.compute(pkg)
    return {
        "Q_count": len(result.Q),
        "M_count": len(result.M),
        "witness_count": len(result.witnesses),
        "witnesses": [list(pair) for pair in result.witnesses],
        "max_fiber": result.max_fiber,
        "delta_max": str(result.delta_max),
        "delta_max_float": float(result.delta_max),
        "pi_map": {str(k): list(v) for k, v in result.pi_map.items()},
    }


def _currentization_summary(pkg: Package, model: MarkovModel) -> dict:
    mode_bit = tuple(Fraction(state[-1]) for state in model.states)
    check_xor = tuple(Fraction(state[0] ^ state[1]) for state in model.states)
    labels = ("mode_bit", "s0_xor_s1")
    passing = currentization_search(pkg, (mode_bit, check_xor))
    return {
        "candidate_labels": list(labels),
        "passing_sets": [[labels[i] for i in sorted(subset)] for subset in passing],
        "passing_indices": [sorted(subset) for subset in passing],
        "min_cardinality": len(passing[0]) if passing else None,
        "mode_singleton_passes": frozenset({0}) in passing,
        "pure_check_singleton_passes": frozenset({1}) in passing,
    }


def _belief_machine(
    model: MarkovModel,
    switch: Fraction,
    depth: int,
    cap: int,
    mode_models: tuple[NoiseModel, NoiseModel],
) -> _Machine:
    code = rep_code(3)
    basis = code.checks + (code.logicals[1],)
    deltas = [_delta_distribution(code.n, basis, mode_model, True) for mode_model in mode_models]
    likelihoods = [_syndrome_likelihood(delta) for delta in deltas]
    logical_maps = _mode_logical_maps(mode_models)
    nodes = tuple((syndrome, beta) for syndrome in range(4) for beta in (0, 1))
    edges = []
    degenerate = True
    for syndrome, beta in nodes:
        row = {}
        for observed in range(4):
            posterior = _posterior(Fraction(beta), switch, likelihoods, observed)
            next_beta = 1 if posterior > Fraction(1, 2) else 0
            row[str(observed)] = {
                "to": [observed, next_beta],
                "posterior": str(posterior),
                "posterior_float": float(posterior),
            }
            if next_beta != beta:
                degenerate = False
        edges.append(row)
    orbit = _belief_orbit(likelihoods, switch, switch, depth, cap)
    return _Machine(
        nodes=nodes,
        edges=tuple(edges),
        likelihoods={
            "mode0": [str(x) for x in likelihoods[0]],
            "mode1": [str(x) for x in likelihoods[1]],
            "mode0_float": [float(x) for x in likelihoods[0]],
            "mode1_float": [float(x) for x in likelihoods[1]],
        },
        logical_maps=logical_maps,
        degenerate=degenerate,
        exact_orbit=orbit,
    )


def _require_frozen_n4_for_belief_machine(p0: Fraction, switch: Fraction) -> None:
    if p0 != Fraction(1, 50) or switch != Fraction(1, 50):
        raise ValueError(
            "E5 belief-machine likelihoods are frozen for N4 p0=1/50, s=1/50; "
            "the legacy payoff/degeneracy findings are pinned to these defaults, "
            "not derived generically -- re-verify them before changing these config values"
        )


def _syndrome_likelihood(delta: np.ndarray) -> tuple[Fraction, ...]:
    # Frozen E5 packaged-belief observation catalog: the four observation
    # classes are exact subsets of the 3-bit (h0,h1,Zbar) delta signature.
    groups = ((0, 4), (1, 2), (5, 6), (3, 7))
    return tuple(sum((delta[i] for i in group), Fraction(0)) for group in groups)


def _posterior(beta: Fraction, switch: Fraction, likelihoods: list[tuple[Fraction, ...]], observed: int) -> Fraction:
    prior = beta * (Fraction(1) - switch) + (Fraction(1) - beta) * switch
    numerator = prior * likelihoods[1][observed]
    denominator = numerator + (Fraction(1) - prior) * likelihoods[0][observed]
    if denominator == 0:
        return Fraction(0)
    return numerator / denominator


def _belief_orbit(
    likelihoods: list[tuple[Fraction, ...]],
    switch: Fraction,
    start: Fraction,
    depth: int,
    cap: int,
) -> dict:
    current = {start}
    rows = [{"depth": 0, "count": 1, "capped": False}]
    capped = False
    for d in range(1, depth + 1):
        nxt = set()
        for belief in current:
            for observed in range(4):
                nxt.add(_posterior(belief, switch, likelihoods, observed))
                if len(nxt) > cap:
                    capped = True
                    break
            if capped:
                break
        current = set(list(nxt)[:cap])
        rows.append({"depth": d, "count": len(current), "capped": capped})
        if capped:
            break
    return {"start": str(start), "depth_rows": rows, "cap": cap, "capped": capped}


def _payoff_memoryless(model: MarkovModel, rounds: int, seed: int) -> dict:
    syndrome_map = _syndrome_map_from_transition(model)
    trajectory = _rollout(model, rounds, seed)
    syndrome_predictions = [syndrome_map[int(model.lens_syndrome[state])] for state in trajectory]
    truth = [_true_logical(model, state) for state in trajectory]
    acc = _accuracy(syndrome_predictions, truth)
    memory = _memory_comparator_accuracy(model, trajectory, syndrome_map)
    return {
        "syndrome_only_accuracy": acc,
        "machine_accuracy": acc,
        "memory_only_accuracy": memory,
        "machine_minus_syndrome": 0.0,
        "rounds": rounds,
    }


def _payoff_hidden(model: MarkovModel, machine: _Machine, rounds: int, seed: int) -> dict:
    syndrome_map = _syndrome_map_from_modes(machine)
    machine_map = _machine_map_from_modes(machine)
    trajectory = _rollout(model, rounds, seed)
    truth = [_true_logical(model, state) for state in trajectory]
    syndrome_predictions = []
    machine_predictions = []
    # Declared initial belief prototype (mode 0); the observation-driven machine
    # must not read the hidden mode coordinate, even at initialization.
    beta = 0
    prev_syndrome = int(model.lens_syndrome[trajectory[0]])
    for state in trajectory:
        syndrome = int(model.lens_syndrome[state])
        syndrome_predictions.append(syndrome_map[syndrome])
        edge = machine.edges[prev_syndrome * 2 + beta][str(syndrome)]
        beta = int(edge["to"][1])
        machine_predictions.append(machine_map[(syndrome, beta)])
        prev_syndrome = syndrome
    syn_acc = _accuracy(syndrome_predictions, truth)
    machine_acc = _accuracy(machine_predictions, truth)
    memory = _memory_comparator_accuracy(model, trajectory, syndrome_map)
    return {
        "syndrome_only_accuracy": syn_acc,
        "machine_accuracy": machine_acc,
        "memory_only_accuracy": memory,
        "machine_minus_syndrome": machine_acc - syn_acc,
        "rounds": rounds,
    }


def _syndrome_map_from_transition(model: MarkovModel) -> dict[int, int]:
    row0 = np.asarray(model.P[0], dtype=object)
    mapping = {}
    for syndrome in range(4):
        masses = [Fraction(0), Fraction(0)]
        for state, prob in enumerate(row0):
            if int(model.lens_syndrome[state]) == syndrome:
                masses[_true_logical(model, state)] += prob
        mapping[syndrome] = 1 if masses[1] > masses[0] else 0
    return mapping


def _syndrome_map_from_modes(machine: _Machine) -> dict[int, int]:
    likelihoods = machine.likelihoods
    del likelihoods
    # The exact mode-conditioned maps agree at the frozen defaults; use the
    # mode-marginalized table so this decoder is explicitly mode-blind.
    mode_maps = machine.logical_maps
    mapping = {}
    for syndrome in range(4):
        masses0 = mode_maps[0][syndrome]
        masses1 = mode_maps[1][syndrome]
        masses = (masses0[0] + masses1[0], masses0[1] + masses1[1])
        mapping[syndrome] = 1 if masses[1] > masses[0] else 0
    return mapping


def _machine_map_from_modes(machine: _Machine) -> dict[tuple[int, int], int]:
    mode_maps = machine.logical_maps
    return {
        (syndrome, beta): (1 if mode_maps[beta][syndrome][1] > mode_maps[beta][syndrome][0] else 0)
        for syndrome in range(4)
        for beta in (0, 1)
    }


def _mode_logical_maps(
    mode_models: tuple[NoiseModel, NoiseModel],
) -> tuple[dict[int, tuple[Fraction, Fraction]], dict[int, tuple[Fraction, Fraction]]]:
    code = rep_code(3)
    basis = code.checks + (code.logicals[1],)
    rows = []
    for mode_model in mode_models:
        delta = _delta_distribution(code.n, basis, mode_model, True)
        table = {}
        for syndrome in range(4):
            table[syndrome] = (delta[syndrome * 2], delta[syndrome * 2 + 1])
        rows.append(table)
    return rows[0], rows[1]


def _payoff_v2_study(
    points: list[dict],
    rounds: int,
    run_length_Ks: tuple[int, ...],
    rounding_Ks: tuple[int, ...],
    seed: int,
) -> dict:
    return {
        "claim_grade": "measured",
        "post_registration": True,
        "rounds": rounds,
        "points": [
            _payoff_v2_point(
                label=str(point["label"]),
                p0=parse_fraction(point["p0"]),
                switch=parse_fraction(point["s"]),
                rounds=rounds,
                seed=seed,
                run_length_Ks=run_length_Ks,
                rounding_Ks=rounding_Ks,
            )
            for point in points
        ],
    }


def _payoff_v2_point(
    label: str,
    p0: Fraction,
    switch: Fraction,
    rounds: int,
    seed: int,
    run_length_Ks: tuple[int, ...],
    rounding_Ks: tuple[int, ...],
) -> dict:
    d0, d1 = _payoff_v2_deltas(p0)
    mix = 0.5 * d0 + 0.5 * d1  # N4's symmetric mode chain has stationary prior P(mode=1)=1/2.
    outcomes, modes = _payoff_v2_trajectory(d0, d1, switch, rounds, seed)
    static_nll = float(-np.log(mix[outcomes]).mean())
    oracle_nll = float(-np.log(np.where(modes[:, None] == 0, d0, d1)[np.arange(rounds), outcomes]).mean())
    exact_filter = _payoff_v2_exact_filter(outcomes, d0, d1, switch)
    split = rounds // 2
    static_heldout_nll = float(-np.log(mix[outcomes[split:]]).mean())
    run_length = {
        str(K): {"gap": _payoff_v2_run_length_gap(outcomes, mix, K)}
        for K in run_length_Ks
    }
    rounding = {
        str(K): _payoff_v2_rounding_gap(outcomes, d0, d1, mix, switch, exact_filter["beliefs"], K)
        for K in rounding_Ks
    }
    ceiling = _entropy(mix) - 0.5 * _entropy(d0) - 0.5 * _entropy(d1)
    oracle_gap = static_nll - oracle_nll
    if abs(oracle_gap - ceiling) > 5e-3:
        raise AssertionError(f"payoff-v2 oracle gap {oracle_gap!r} disagrees with analytic ceiling {ceiling!r}")
    return {
        "label": label,
        "p0": str(p0),
        "s": str(switch),
        "static_nll": static_nll,
        "static_heldout_nll": static_heldout_nll,
        "oracle_nll": oracle_nll,
        "oracle_gap": oracle_gap,
        "ceiling_analytic": ceiling,
        "exact_filter_nll": exact_filter["nll"],
        "exact_filter_gap": static_nll - exact_filter["nll"],
        "run_length": run_length,
        "rounding": rounding,
    }


def _payoff_v2_deltas(p0: Fraction) -> tuple[np.ndarray, np.ndarray]:
    code = rep_code(3)
    model = n4(p0, Fraction(0), code.n)
    if model.hidden is None:
        raise ValueError("payoff-v2 requires N4 hidden modes")
    basis = code.checks + (code.logicals[1],)
    return tuple(
        np.asarray([float(x) for x in _delta_distribution(code.n, basis, mode_model, True)], dtype=np.float64)
        for mode_model in model.hidden.mode_models
    )


def _payoff_v2_trajectory(
    d0: np.ndarray,
    d1: np.ndarray,
    switch: Fraction,
    rounds: int,
    seed: int,
) -> tuple[np.ndarray, np.ndarray]:
    rng = project_rng(seed)
    mode = 0
    outcomes = np.empty(rounds, dtype=np.int64)
    modes = np.empty(rounds, dtype=np.int64)
    s = float(switch)
    for t in range(rounds):
        if rng.random() < s:
            mode = 1 - mode
        modes[t] = mode
        outcomes[t] = int(rng.choice(8, p=(d0 if mode == 0 else d1)))
    return outcomes, modes


def _payoff_v2_exact_filter(outcomes: np.ndarray, d0: np.ndarray, d1: np.ndarray, switch: Fraction) -> dict:
    b = 0.5
    s = float(switch)
    nll = 0.0
    beliefs = np.empty(outcomes.shape[0], dtype=np.float64)
    for t, x in enumerate(outcomes):
        bp = b * (1.0 - s) + (1.0 - b) * s
        pred = (1.0 - bp) * d0 + bp * d1
        nll -= float(np.log(pred[x]))
        denom = bp * d1[x] + (1.0 - bp) * d0[x]
        b = float(bp * d1[x] / denom)
        beliefs[t] = b
    return {"nll": float(nll / outcomes.shape[0]), "beliefs": beliefs}


def _payoff_v2_run_length_gap(outcomes: np.ndarray, mix: np.ndarray, K: int) -> float:
    nodes = np.empty(outcomes.shape[0], dtype=np.int64)
    node = 0
    for t, outcome in enumerate(outcomes):
        nodes[t] = node
        node = min(node + 1, K - 1) if (int(outcome) & 3) == 0 else 0
    split = outcomes.shape[0] // 2
    table = np.ones((K, 8), dtype=np.float64)
    for t in range(split):
        table[nodes[t], outcomes[t]] += 1.0
    table /= table.sum(axis=1, keepdims=True)
    machine_nll = float(-np.log(table[nodes[split:], outcomes[split:]]).mean())
    # Static keeps the exact declared mixture; the run-length table's estimation
    # noise counts against the packaged memory method.
    static_nll = float(-np.log(mix[outcomes[split:]]).mean())
    return static_nll - machine_nll


def _payoff_v2_rounding_gap(
    outcomes: np.ndarray,
    d0: np.ndarray,
    d1: np.ndarray,
    mix: np.ndarray,
    switch: Fraction,
    beliefs: np.ndarray,
    K: int,
) -> dict:
    eps = np.finfo(float).tiny
    b_min = float(np.clip(np.min(beliefs), eps, 1.0 - eps))
    b_max = float(np.clip(np.max(beliefs), eps, 1.0 - eps))
    grid = np.linspace(_logit(b_min), _logit(b_max), K)
    protos = _sigmoid(grid)
    b = 0.5
    s = float(switch)
    nll = 0.0
    for x in outcomes:
        bp = b * (1.0 - s) + (1.0 - b) * s
        pred = (1.0 - bp) * d0 + bp * d1
        nll -= float(np.log(pred[x]))
        denom = bp * d1[x] + (1.0 - bp) * d0[x]
        post = float(bp * d1[x] / denom)
        b = float(protos[int(np.argmin(np.abs(_logit(protos) - _logit(post))))])
    rounded_nll = float(nll / outcomes.shape[0])
    static_nll = float(-np.log(mix[outcomes]).mean())
    return {"gap": static_nll - rounded_nll, "prototypes": [float(x) for x in protos]}


def _entropy(p: np.ndarray) -> float:
    vals = np.asarray(p, dtype=float)
    nz = vals[vals > 0.0]
    return float(-np.sum(nz * np.log(nz)))


def _logit(x) -> np.ndarray:
    arr = np.asarray(x, dtype=np.float64)
    return np.log(arr / (1.0 - arr))


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def _rollout(model: MarkovModel, rounds: int, seed: int) -> list[int]:
    rng = project_rng(seed)
    P = np.asarray(model.P, dtype=float)
    state = 0
    trajectory = []
    for _ in range(rounds):
        trajectory.append(state)
        state = int(rng.choice(P.shape[0], p=P[state]))
    return trajectory


def _memory_comparator_accuracy(model: MarkovModel, trajectory: list[int], fallback: dict[int, int]) -> float:
    syndromes = [int(model.lens_syndrome[state]) for state in trajectory]
    truth = [_true_logical(model, state) for state in trajectory]
    split = len(trajectory) // 2
    counts: dict[tuple[int, int, int], list[int]] = {}
    for t in range(2, split):
        key = (syndromes[t - 2], syndromes[t - 1], syndromes[t])
        counts.setdefault(key, [0, 0])[truth[t]] += 1
    correct = 0
    total = 0
    for t in range(max(split, 2), len(trajectory)):
        key = (syndromes[t - 2], syndromes[t - 1], syndromes[t])
        if key in counts:
            pred = 1 if counts[key][1] > counts[key][0] else 0
        else:
            pred = fallback[syndromes[t]]
        correct += int(pred == truth[t])
        total += 1
    return correct / total if total else 0.0


def _true_logical(model: MarkovModel, state_index: int) -> int:
    return int(model.states[state_index][model.n_syndrome_bits])


def _accuracy(predictions: list[int], truth: list[int]) -> float:
    arr_p = np.asarray(predictions, dtype=np.int8)
    arr_t = np.asarray(truth, dtype=np.int8)
    return float(np.mean(arr_p == arr_t))


def _predictions(quotients: dict, currentization: dict, machine: _Machine, payoff: dict) -> list[dict]:
    p51_ok = (
        quotients["memoryless_n1"]["witness_count"] == 0
        and quotients["memoryless_n1"]["Q_count"] == quotients["memoryless_n1"]["M_count"] == 4
        and abs(payoff["memoryless_n1"]["machine_minus_syndrome"]) <= 1e-12
    )
    p52_quotient_ok = quotients["n4_hidden"]["witness_count"] >= 1 and quotients["n4_hidden"]["max_fiber"] == 2
    p52_gap = payoff["n4_hidden"]["machine_minus_syndrome"]
    p52_gap_ok = p52_gap > 0.0 and p52_gap <= quotients["n4_hidden"]["delta_max_float"]
    p53_ok = quotients["trap_naive"]["witness_count"] > 0 and quotients["trap_internalized"]["witness_count"] == 0
    p54_ok = currentization["n4_hidden"]["mode_singleton_passes"] and not currentization["n4_hidden"]["pure_check_singleton_passes"]
    return [
        {
            "id": "P5.1",
            "statement": "memoryless package has no witnesses and no payoff gap",
            "verdict": "registered-positive" if p51_ok else "registered-negative",
            "grade": "registered-positive" if p51_ok else "registered-negative",
            "values": {
                "witness_count": quotients["memoryless_n1"]["witness_count"],
                "Q_count": quotients["memoryless_n1"]["Q_count"],
                "M_count": quotients["memoryless_n1"]["M_count"],
                "payoff_gap": payoff["memoryless_n1"]["machine_minus_syndrome"],
            },
        },
        {
            "id": "P5.2",
            "statement": "N4 witness and MaxFiber are nontrivial, with positive bounded payoff",
            "verdict": "registered-positive" if (p52_quotient_ok and machine.degenerate is False and p52_gap_ok) else "registered-negative",
            "grade": "registered-positive" if (p52_quotient_ok and machine.degenerate is False and p52_gap_ok) else "registered-negative",
            "values": {
                "witness_count": quotients["n4_hidden"]["witness_count"],
                "max_fiber": quotients["n4_hidden"]["max_fiber"],
                "delta_max": quotients["n4_hidden"]["delta_max"],
                "machine_nodes": len(machine.nodes),
                "machine_degenerate": machine.degenerate,
                "payoff_gap": p52_gap,
                "payoff_gap_positive_and_bounded": p52_gap_ok,
            },
            "interpretation": (
                "The predictive witness is real, but the coarsened belief coordinate is frozen at these "
                "defaults, so the machine decoder collapses to the syndrome-only MAP and payoff gap is nil."
            ),
        },
        {
            "id": "P5.3",
            "statement": "protocol-trap witnesses vanish after internalization",
            "verdict": "registered-positive" if p53_ok else "registered-negative",
            "grade": "registered-positive" if p53_ok else "registered-negative",
            "values": {
                "naive_witness_count": quotients["trap_naive"]["witness_count"],
                "internalized_witness_count": quotients["trap_internalized"]["witness_count"],
                "internalized_delta_max": quotients["trap_internalized"]["delta_max"],
                "classification": "artifact_trap" if p53_ok else "genuine_memory_after_internalization",
            },
            "interpretation": (
                "Pure internalization leaves witnesses: deterministic p0-vs-3p0 alternation carries real "
                "predictive content because current phase predicts next-round observable statistics. The "
                "frozen schedule was registered as artifact-shaped, but this package behaves as genuine state memory."
            ),
        },
        {
            "id": "P5.4",
            "statement": "mode-bit currentization passes at cardinality 1 while pure checks do not",
            "verdict": "registered-positive" if p54_ok else "registered-negative",
            "grade": "registered-positive" if p54_ok else "registered-negative",
            "values": currentization["n4_hidden"],
        },
    ]


def _machine_summary(machine: _Machine) -> dict:
    return {
        "nodes": [list(node) for node in machine.nodes],
        "edges": list(machine.edges),
        "likelihoods": machine.likelihoods,
        "degenerate": machine.degenerate,
        "exact_orbit": machine.exact_orbit,
        "node_count": len(machine.nodes),
    }


def _syndrome_events(model: MarkovModel) -> tuple[tuple[Fraction, ...], ...]:
    return tuple(
        tuple(Fraction(int(state[bit])) for state in model.states)
        for bit in range(model.n_syndrome_bits)
    )


def _event_from_int_lens(lens: np.ndarray) -> tuple[Fraction, ...]:
    return tuple(Fraction(int(x)) for x in lens)


def _matrix_tuple(matrix) -> tuple[tuple[Fraction, ...], ...]:
    return tuple(tuple(x if isinstance(x, Fraction) else Fraction(x) for x in row) for row in matrix)


def _matmul(A, B) -> tuple[tuple[Fraction, ...], ...]:
    rows = len(A)
    cols = len(B[0]) if B else 0
    inner = len(B)
    return tuple(
        tuple(sum((A[i][k] * B[k][j] for k in range(inner)), Fraction(0)) for j in range(cols))
        for i in range(rows)
    )


def _save_machine_figure(run: Run, machine: _Machine) -> None:
    fig, ax = plt.subplots(figsize=(5, 5))
    angles = np.linspace(0, 2 * np.pi, len(machine.nodes), endpoint=False)
    pos = {node: (np.cos(a), np.sin(a)) for node, a in zip(machine.nodes, angles)}
    for node in machine.nodes:
        x, y = pos[node]
        ax.scatter([x], [y], color="black", s=30)
        ax.text(x, y, f"{node[0]},{node[1]}", ha="center", va="bottom", fontsize=8)
    rows = []
    for idx, node in enumerate(machine.nodes):
        x0, y0 = pos[node]
        for obs, edge in machine.edges[idx].items():
            target = tuple(edge["to"])
            x1, y1 = pos[target]
            ax.plot([x0, x1], [y0, y1], color="gray", linewidth=0.6, alpha=0.5)
            rows.append([f"{node[0]}:{node[1]}", obs, f"{target[0]}:{target[1]}"])
    ax.set_axis_off()
    ax.set_title("E5 packaged belief automaton")
    run.save_figure(fig, "e5_minimal_machine", rows, ["from_node", "observation", "to_node"])
    plt.close(fig)


def _save_trap_figure(run: Run, trap: dict) -> None:
    rows = [["naive", trap["naive_witness_count"]], ["internalized", trap["internalized_witness_count"]]]
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.bar([row[0] for row in rows], [row[1] for row in rows], color="black")
    ax.set_ylabel("witness count")
    ax.set_title("E5 protocol-trap control")
    run.save_figure(fig, "e5_internalization_witnesses", rows, ["package", "witnesses"])
    plt.close(fig)


def _save_payoff_figure(run: Run, payoff: dict, delta_max: float) -> None:
    rows = []
    for package, table in payoff.items():
        for decoder in ("syndrome_only", "machine", "memory_only"):
            rows.append([decoder, package, table[f"{decoder}_accuracy"]])
    fig, ax = plt.subplots(figsize=(7, 4))
    labels = [f"{row[1]}:{row[0]}" for row in rows]
    ax.bar(range(len(rows)), [row[2] for row in rows], color="black")
    ax.axhline(delta_max, color="gray", linestyle="--", linewidth=1)
    ax.set_xticks(range(len(rows)))
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=7)
    ax.set_ylabel("accuracy")
    ax.set_title("E5 payoff validation")
    run.save_figure(fig, "e5_payoff", rows, ["decoder", "package", "accuracy"])
    plt.close(fig)


def _save_payoff_v2_figure(run: Run, payoff_v2: dict) -> None:
    rows = []
    points = payoff_v2["points"]
    fig, axes = plt.subplots(1, len(points), figsize=(6 * len(points), 4), squeeze=False)
    for ax, point in zip(axes[0], points):
        labels = ["static"]
        gaps = [0.0]
        rows.append([point["label"], "static", 0.0])
        for K, row in point["run_length"].items():
            label = f"run_length_K{K}"
            labels.append(label)
            gaps.append(row["gap"])
            rows.append([point["label"], label, row["gap"]])
        for K, row in point["rounding"].items():
            label = f"rounding_K{K}"
            labels.append(label)
            gaps.append(row["gap"])
            rows.append([point["label"], label, row["gap"]])
        for label, value in (
            ("exact_filter", point["exact_filter_gap"]),
            ("oracle", point["oracle_gap"]),
        ):
            labels.append(label)
            gaps.append(value)
            rows.append([point["label"], label, value])
        ax.axhline(0.0, color="gray", linewidth=1)
        ax.bar(range(len(labels)), gaps, color="black")
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=7)
        ax.set_ylabel("NLL gap (nats/round)")
        ax.set_title(f"E5 payoff v2: {point['label']}")
    fig.tight_layout()
    run.save_figure(fig, "e5_payoff_v2_ladder", rows, ["point", "predictor", "gap"])
    plt.close(fig)


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m sbqos.experiments.e5_decoder_memory <config.json>")
    main(sys.argv[1])
