"""CycleOperator, δ, ε, RM, CD_τ, Δ_pred, ExistenceCertificate   MS §4"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

import numpy as np

from sbqos import rng as project_rng
from sbqos.markov import MarkovModel, stationary
from sbqos.moments import Matrix


@dataclass(frozen=True)
class ExistenceCertificate:
    delta: float
    epsilon: float
    bound_ok: bool
    multiplicity: int
    route_mismatch: float
    cd_tau: float
    delta_pred: float
    status: str


def idem_defect(model: MarkovModel, lens: str, tau: int) -> Fraction | float:
    """Return the idempotence defect for a decoded lens.

    Ref: design/01_MATH_SPEC.md §4.2.
    """
    _require_decoded_lens(lens)
    P_tau = _matrix_power(model.P, tau, model.exact)
    lens_values = _lens_values(model, lens)
    _labels, Agg = _aggregation(lens_values, model.exact)
    Expand = _decoded_expand(model, _labels, model.exact)
    E = _matmul(_matmul(P_tau, Agg, model.exact), Expand, model.exact)
    defect = _mat_sub(_matmul(E, E, model.exact), E, model.exact)
    return max((_half_l1(row, model.exact) for row in defect), default=_zero(model.exact))


def retention_error(model: MarkovModel, lens: str, tau: int) -> tuple[Fraction | float, list[Fraction | float]]:
    """Return maximum and per-label retention errors.

    Ref: design/01_MATH_SPEC.md §4.2.
    """
    _require_decoded_lens(lens)
    P_tau = _matrix_power(model.P, tau, model.exact)
    lens_values = _lens_values(model, lens)
    labels, Agg = _aggregation(lens_values, model.exact)
    Expand = _decoded_expand(model, labels, model.exact)
    evolved = _matmul(_matmul(Expand, P_tau, model.exact), Agg, model.exact)
    errors: list[Fraction | float] = []
    for i in range(len(labels)):
        target = _label_onehot(len(labels), i, model.exact)
        errors.append(_half_l1(evolved[i] - target, model.exact))
    return max(errors, default=_zero(model.exact)), errors


def prototype_stability(model: MarkovModel, lens: str, tau: int, eps_stable: float = 0.05) -> int:
    """Return the number of labels whose prototype retention is stable.

    Ref: design/01_MATH_SPEC.md §4.2.
    """
    _max_error, per_label = retention_error(model, lens, tau)
    threshold = Fraction(str(eps_stable)) if model.exact else float(eps_stable)
    return sum(1 for error in per_label if error <= threshold)


def route_mismatch(model: MarkovModel, lens: str, tau: int) -> Fraction | float:
    """Return route mismatch for decoded or syndrome lens.

    Ref: design/01_MATH_SPEC.md §4.3.
    """
    _require_nonabsorbing_stationary(model, "route_mismatch", "route_mismatch_finite_horizon")
    return _route_mismatch_for_lens(model, lens, tau)


def route_mismatch_finite_horizon(
    model: MarkovModel,
    lens: str,
    tau: int,
    horizon: int,
    initial_state: int = 0,
) -> float:
    """Finite-horizon route mismatch for decoded or syndrome lens.

    Ref: design/01_MATH_SPEC.md §4.3.
    """
    return float(
        _route_mismatch_for_lens(
            model,
            lens,
            tau,
            weights=_finite_horizon_weights(model, horizon, initial_state),
        )
    )


def closure_deficit(model: MarkovModel, lens: str, tau: int) -> float:
    """CD_tau against the requested lens.

    Ref: design/01_MATH_SPEC.md §4.4.
    """
    _require_nonabsorbing_stationary(model, "closure_deficit")
    return _closure_deficit_for_lens(model, lens, tau)


def closure_deficit_finite_horizon(
    model: MarkovModel,
    tau: int,
    horizon: int,
    initial_state: int = 0,
) -> float:
    """Finite-horizon CD_tau against the decoded lens for absorbing models.

    Ref: design/01_MATH_SPEC.md §4.4.
    """
    weights = _finite_horizon_weights(model, horizon, initial_state)
    return _closure_deficit_for_lens(model, "decoded", tau, weights=weights)


def closure_deficit_variational_check(
    model: MarkovModel,
    tau: int,
    n_perturbations: int,
    seed: int,
) -> bool:
    """Check that the fiber-average macro kernel minimizes KL prediction loss.

    Ref: design/01_MATH_SPEC.md §4.4.
    """
    context = _prediction_context(model, "decoded", tau)
    baseline = _prediction_loss(context.lens_values, context.R, context.weights, context.p_bar)
    cd_tau = closure_deficit(model, "decoded", tau)
    if abs(baseline - cd_tau) > 1e-12:
        raise AssertionError("baseline variational loss does not match closure_deficit")

    gen = project_rng(seed)
    p_bar = _as_float_matrix(context.p_bar)
    for _ in range(n_perturbations):
        perturbed = np.empty_like(p_bar)
        for i, row in enumerate(p_bar):
            draw = gen.random(row.shape[0])
            draw = draw / np.sum(draw)
            perturbed[i] = 0.75 * row + 0.25 * draw
            perturbed[i] = perturbed[i] / np.sum(perturbed[i])
        loss = _prediction_loss(context.lens_values, context.R, context.weights, perturbed)
        if loss + 1e-12 < baseline:
            raise AssertionError("perturbed macro kernel beat fiber-average kernel")
    return True


def predictive_gap(model: MarkovModel, tau_stream_length: int, seed: int) -> float:
    """Stream proxy Delta_pred = NLL_1 - NLL_2 for decoded labels.

    Ref: design/01_MATH_SPEC.md §4.4.
    """
    _require_nonabsorbing_stationary(model, "predictive_gap", "predictive_gap_finite_horizon")
    return _predictive_gap_from_initial(model, tau_stream_length, seed, stationary(model.P))


def predictive_gap_finite_horizon(
    model: MarkovModel,
    tau_stream_length: int,
    seed: int,
    horizon: int,
    initial_state: int = 0,
) -> float:
    """Finite-horizon stream proxy Delta_pred for absorbing models.

    Ref: design/01_MATH_SPEC.md §4.4.
    """
    return _predictive_gap_from_initial(
        model,
        tau_stream_length,
        seed,
        _finite_horizon_weights(model, horizon, initial_state),
    )


def _predictive_gap_from_initial(
    model: MarkovModel,
    tau_stream_length: int,
    seed: int,
    initial_probs: np.ndarray,
) -> float:
    if tau_stream_length < 4:
        raise ValueError("tau_stream_length must be at least 4")
    n_labels = int(np.max(model.lens_decoded)) + 1
    if n_labels <= 1:
        return 0.0

    gen = project_rng(seed)
    P = np.asarray(model.P, dtype=float)
    state = int(gen.choice(P.shape[0], p=_prob_row(initial_probs)))
    stream = np.empty(tau_stream_length, dtype=np.int64)
    for t in range(tau_stream_length):
        stream[t] = int(model.lens_decoded[state])
        state = int(gen.choice(P.shape[0], p=_prob_row(P[state])))

    split = tau_stream_length // 2
    train = stream[:split]
    heldout = stream[split:]
    if heldout.shape[0] < 3:
        raise ValueError("tau_stream_length leaves fewer than 3 held-out labels")

    counts1, counts2 = _predictive_fit_counts(train, n_labels)
    probs1 = counts1 / counts1.sum(axis=1, keepdims=True)
    probs2 = counts2 / counts2.sum(axis=2, keepdims=True)

    nll1 = 0.0
    count1 = 0
    for t in range(2, heldout.shape[0]):
        nll1 -= float(np.log(probs1[heldout[t - 1], heldout[t]]))
        count1 += 1

    nll2 = 0.0
    count2 = 0
    for t in range(2, heldout.shape[0]):
        nll2 -= float(np.log(probs2[heldout[t - 2], heldout[t - 1], heldout[t]]))
        count2 += 1

    return (nll1 / count1) - (nll2 / count2)


def full_existence_certificate(
    model: MarkovModel,
    tau: int,
    *,
    delta_max: float,
    cd_max: float,
    eps_stable: float = 0.05,
    stream_length: int = 20000,
    seed: int = 0,
) -> ExistenceCertificate:
    """Compute and assemble the full existence certificate.

    Ref: design/01_MATH_SPEC.md §4.5.
    """
    _require_nonabsorbing_stationary(model, "full_existence_certificate")
    delta = idem_defect(model, "decoded", tau)
    epsilon, _per_label = retention_error(model, "decoded", tau)
    multiplicity = prototype_stability(model, "decoded", tau, eps_stable=eps_stable)
    rm = route_mismatch(model, "decoded", tau)
    cd_tau = closure_deficit(model, "decoded", tau)
    delta_pred = predictive_gap(model, stream_length, seed)
    return assemble_certificate(
        delta,
        epsilon,
        rm,
        cd_tau,
        delta_pred,
        delta_max=delta_max,
        cd_max=cd_max,
        multiplicity=multiplicity,
        ε_stable=eps_stable,
    )


def _require_decoded_lens(lens: str) -> None:
    if lens != "decoded":
        raise ValueError(
            "idem_defect/retention_error are only defined for the decoded lens "
            "(no natural prototype exists for the syndrome lens)"
        )


def _require_nonabsorbing_stationary(
    model: MarkovModel,
    operation: str,
    alternative: str = "closure_deficit_finite_horizon",
) -> None:
    if model.is_absorbing:
        raise ValueError(
            f"{operation} is not defined with stationary weights for absorbing hidden-mode models; "
            f"use {alternative} instead"
        )


class _PredictionContext:
    def __init__(self, lens_values, R, weights, p_bar):
        self.lens_values = lens_values
        self.R = R
        self.weights = weights
        self.p_bar = p_bar


def _route_mismatch_for_lens(
    model: MarkovModel,
    lens: str,
    tau: int,
    weights: list[Fraction] | np.ndarray | None = None,
) -> Fraction | float:
    exact = model.exact if weights is None else False
    P_tau = _matrix_power(model.P, tau, exact)
    lens_values = _lens_values(model, lens)
    labels, Agg = _aggregation(lens_values, exact)
    R = _matmul(P_tau, Agg, exact)
    weights = _stationary_weights(model) if weights is None else np.asarray(weights, dtype=float)
    total = _zero(exact)

    for label_index, label in enumerate(labels):
        fiber = [i for i, value in enumerate(lens_values) if value == label]
        fiber_mass = sum((weights[i] for i in fiber), _zero(exact))
        if fiber_mass == 0:
            continue
        average = _weighted_average_rows(R, weights, fiber, fiber_mass, exact)
        for z in fiber:
            total += weights[z] * _l1(R[z] - average, exact)
    return total


def _closure_deficit_for_lens(
    model: MarkovModel,
    lens: str,
    tau: int,
    weights: list[Fraction] | np.ndarray | None = None,
) -> float:
    context = _prediction_context(model, lens, tau, weights=weights)
    return _prediction_loss(context.lens_values, context.R, context.weights, context.p_bar)


def _prediction_context(
    model: MarkovModel,
    lens: str,
    tau: int,
    weights: list[Fraction] | np.ndarray | None = None,
) -> _PredictionContext:
    exact = model.exact if weights is None else False
    P_tau = _matrix_power(model.P, tau, exact)
    lens_values = _lens_values(model, lens)
    labels, Agg = _aggregation(lens_values, exact)
    R = _matmul(P_tau, Agg, exact)
    weights = _stationary_weights(model) if weights is None else np.asarray(weights, dtype=float)
    p_bar = _zero_matrix(len(labels), len(labels), exact)

    for label_index, label in enumerate(labels):
        fiber = [i for i, value in enumerate(lens_values) if value == label]
        fiber_mass = sum((weights[i] for i in fiber), _zero(exact))
        if fiber_mass == 0:
            continue
        p_bar[label_index] = _weighted_average_rows(R, weights, fiber, fiber_mass, exact)
    return _PredictionContext(lens_values, R, weights, p_bar)


def _prediction_loss(lens_values: np.ndarray, R: Matrix, weights, p_bar: Matrix) -> float:
    total = 0.0
    p_bar_float = _as_float_matrix(p_bar)
    R_float = _as_float_matrix(R)
    for state, label in enumerate(lens_values):
        total += float(weights[state]) * _kl(R_float[state], p_bar_float[int(label)])
    return total


def _finite_horizon_weights(model: MarkovModel, horizon: int, initial_state: int) -> np.ndarray:
    if not 0 <= initial_state < model.P.shape[0]:
        raise ValueError("initial_state out of range")
    P_horizon = _matrix_power(model.P, horizon, exact=False)
    mu = np.zeros(model.P.shape[0], dtype=float)
    mu[initial_state] = 1.0
    return mu @ P_horizon


def _kl(p: np.ndarray, q: np.ndarray) -> float:
    total = 0.0
    for p_i, q_i in zip(p, q):
        if p_i == 0:
            continue
        if q_i <= 0:
            raise ValueError("KL encountered q_i == 0 with p_i > 0")
        total += float(p_i) * float(np.log(float(p_i) / float(q_i)))
    return total


def assemble_certificate(
    delta,
    epsilon,
    rm,
    cd_tau,
    delta_pred,
    *,
    delta_max,
    cd_max,
    multiplicity,
    ε_stable=0.05,
) -> ExistenceCertificate:
    """Assemble the first-match existence certificate status.

    Ref: design/01_MATH_SPEC.md §4.5.
    """
    del ε_stable
    if multiplicity < 2:
        status = "trivialized"
    elif cd_tau > cd_max:
        status = "non_closed"
    elif delta <= delta_max:
        status = "certified"
    else:
        status = "degrading"
    return ExistenceCertificate(
        delta=float(delta),
        epsilon=float(epsilon),
        bound_ok=delta <= epsilon,
        multiplicity=int(multiplicity),
        route_mismatch=float(rm),
        cd_tau=float(cd_tau),
        delta_pred=float(delta_pred),
        status=status,
    )


def _lens_values(model: MarkovModel, lens: str) -> np.ndarray:
    if lens == "decoded":
        return model.lens_decoded
    if lens == "syndrome":
        return model.lens_syndrome
    raise ValueError("lens must be 'decoded' or 'syndrome'")


def _aggregation(lens_values: np.ndarray, exact: bool) -> tuple[tuple[int, ...], Matrix]:
    labels = tuple(int(x) for x in sorted(set(int(v) for v in lens_values)))
    label_to_index = {label: i for i, label in enumerate(labels)}
    Agg = _zero_matrix(len(lens_values), len(labels), exact)
    one = _one(exact)
    for state_index, label in enumerate(lens_values):
        Agg[state_index, label_to_index[int(label)]] = one
    return labels, Agg


def _decoded_expand(model: MarkovModel, labels: tuple[int, ...], exact: bool) -> Matrix:
    Expand = _zero_matrix(len(labels), model.P.shape[0], exact)
    one = _one(exact)
    for row, label in enumerate(labels):
        Expand[row, label] = one
    return Expand


def _matrix_power(P: Matrix, tau: int, exact: bool) -> Matrix:
    if tau < 0:
        raise ValueError("tau must be nonnegative")
    base = _matrix(P, exact)
    result = _identity(base.shape[0], exact)
    power = tau
    while power:
        if power & 1:
            result = _matmul(result, base, exact)
        base = _matmul(base, base, exact)
        power >>= 1
    return result


def _matmul(A: Matrix, B: Matrix, exact: bool) -> Matrix:
    if not exact:
        return np.asarray(A, dtype=float) @ np.asarray(B, dtype=float)
    A = _matrix(A, exact=True)
    B = _matrix(B, exact=True)
    out = _zero_matrix(A.shape[0], B.shape[1], exact=True)
    for i in range(A.shape[0]):
        for j in range(B.shape[1]):
            out[i, j] = sum((A[i, k] * B[k, j] for k in range(A.shape[1])), Fraction(0))
    return out


def _mat_sub(A: Matrix, B: Matrix, exact: bool) -> Matrix:
    if not exact:
        return np.asarray(A, dtype=float) - np.asarray(B, dtype=float)
    A = _matrix(A, exact=True)
    B = _matrix(B, exact=True)
    out = _zero_matrix(A.shape[0], A.shape[1], exact=True)
    for idx in np.ndindex(A.shape):
        out[idx] = A[idx] - B[idx]
    return out


def _matrix(M: Matrix, exact: bool) -> Matrix:
    if not exact:
        return np.asarray(M, dtype=float)
    A = np.asarray(M)
    out = np.empty(A.shape, dtype=object)
    for idx in np.ndindex(A.shape):
        out[idx] = A[idx] if isinstance(A[idx], Fraction) else Fraction(A[idx])
    return out


def _as_float_matrix(M: Matrix) -> np.ndarray:
    A = np.asarray(M)
    out = np.empty(A.shape, dtype=float)
    for idx in np.ndindex(A.shape):
        out[idx] = float(A[idx])
    return out


def _identity(n: int, exact: bool) -> Matrix:
    eye = _zero_matrix(n, n, exact)
    for i in range(n):
        eye[i, i] = _one(exact)
    return eye


def _zero_matrix(rows: int, cols: int, exact: bool) -> Matrix:
    if exact:
        out = np.empty((rows, cols), dtype=object)
        out[:, :] = Fraction(0)
        return out
    return np.zeros((rows, cols), dtype=float)


def _label_onehot(n_labels: int, label_index: int, exact: bool) -> np.ndarray:
    row = np.empty(n_labels, dtype=object if exact else float)
    row[:] = _zero(exact)
    row[label_index] = _one(exact)
    return row


def _stationary_weights(model: MarkovModel) -> list[Fraction] | np.ndarray:
    weights = stationary(model.P)
    if not model.exact:
        return weights
    n_states = model.P.shape[0]
    uniform = 1.0 / n_states
    if not np.allclose(weights, np.full(n_states, uniform), atol=1e-12):
        raise ValueError("exact model stationary distribution is not uniform")
    return [Fraction(1, n_states) for _ in range(n_states)]


def _weighted_average_rows(
    R: Matrix,
    weights: list[Fraction] | np.ndarray,
    fiber: list[int],
    fiber_mass,
    exact: bool,
) -> np.ndarray:
    out = np.empty(R.shape[1], dtype=object if exact else float)
    out[:] = _zero(exact)
    for z in fiber:
        out += (weights[z] / fiber_mass) * R[z]
    return out


def _half_l1(row: np.ndarray, exact: bool) -> Fraction | float:
    return _l1(row, exact) / 2


def _l1(row: np.ndarray, exact: bool) -> Fraction | float:
    if exact:
        return sum((abs(x) for x in row), Fraction(0))
    return float(np.sum(np.abs(np.asarray(row, dtype=float))))


def _zero(exact: bool) -> Fraction | float:
    return Fraction(0) if exact else 0.0


def _one(exact: bool) -> Fraction | float:
    return Fraction(1) if exact else 1.0


def _prob_row(row: np.ndarray) -> np.ndarray:
    probs = np.asarray(row, dtype=float).copy()
    probs[probs < 0] = 0.0
    total = float(np.sum(probs))
    if total <= 0:
        raise ValueError("probability row has nonpositive mass")
    return probs / total


def _predictive_fit_counts(train: np.ndarray, n_labels: int) -> tuple[np.ndarray, np.ndarray]:
    counts1 = np.ones((n_labels, n_labels), dtype=float)
    # Laplace +1 smoothing keeps held-out NLL finite even for unseen transitions.
    for t in range(1, train.shape[0]):
        counts1[train[t - 1], train[t]] += 1.0

    counts2 = np.ones((n_labels, n_labels, n_labels), dtype=float)
    # Same Laplace smoothing for order-2 contexts.
    for t in range(2, train.shape[0]):
        counts2[train[t - 2], train[t - 1], train[t]] += 1.0
    return counts1, counts2
