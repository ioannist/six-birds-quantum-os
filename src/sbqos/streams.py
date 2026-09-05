"""stim code-capacity samplers; no circuit-level or measurement noise   MS §3.5

Hidden-mode N4/N5 models are sampled by a classical loop because Stim has no
representation of the hidden mode state.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

import numpy as np
import stim

from sbqos.codes import Code, PauliVec, sympl
from sbqos.moments import CovBlocks, Matrix, MomentEngine, ProbeFamily
from sbqos.noise import NoiseModel, sample_error
from sbqos.xi import Witness, blind_spot_witness, xi_residual


@dataclass(frozen=True)
class ShotTable:
    L: ProbeFamily
    D: ProbeFamily
    L_outcomes: np.ndarray
    D_outcomes: np.ndarray
    mode: np.ndarray | None


def build_stim_circuit(code: Code, model: NoiseModel, rounds: int = 1) -> stim.Circuit:
    """Build the code-capacity noise fragment for non-hidden models.

    N4/N5 hidden-mode models are sampled by sample_shots' classical rollout,
    because Stim has no hidden-mode state.

    Ref: design/01_MATH_SPEC.md §3.5.
    """
    if rounds != 1:
        raise ValueError("streams are code-capacity only: rounds must be 1")
    if model.hidden is not None:
        raise ValueError("hidden-mode models are sampled by sample_shots, not represented in Stim")
    _require_uniform_per_qubit(model)

    circuit = stim.Circuit()
    if model.name == "N1":
        p = model.per_qubit[0][1]
        circuit.append("X_ERROR", list(range(code.n)), float(p))
        return circuit

    if model.name in {"N2", "N3"}:
        p_x = model.per_qubit[0][1]
        p_y = model.per_qubit[0][2]
        p_z = model.per_qubit[0][3]
        if not (p_x == p_y == p_z):
            raise ValueError("DEPOLARIZE1 path requires equal X/Y/Z per-Pauli rates")
        circuit.append("DEPOLARIZE1", list(range(code.n)), float(3 * p_x))
        if model.injection is not None:
            circuit.append("CORRELATED_ERROR", _targets_for_vec(model.injection.vec, code.n), float(model.injection.prob))
        return circuit

    raise ValueError(f"unsupported noise model for Stim path: {model.name!r}")


def sample_shots(
    code: Code,
    model: NoiseModel,
    L: ProbeFamily,
    D: ProbeFamily,
    N: int,
    rng: np.random.Generator,
) -> ShotTable:
    """Sample probe flip outcomes.

    Non-hidden models with mutually commuting probes use Stim with before/after
    MPP measurements and DETECTOR differencing. Hidden models use one continuous
    classical rollout, carrying the hidden mode from shot to shot instead of
    restarting independently. Non-hidden models with anticommuting probes also
    use the classical path, because sequential projective MPP measurements
    would corrupt the before/after baseline.

    Ref: design/01_MATH_SPEC.md §3.5.
    """
    probes = L.vecs + D.vecs
    if model.hidden is not None or not _all_commute(probes):
        return _sample_classical(code, model, L, D, N, rng)

    circuit = stim.Circuit()
    _append_probe_measurements(circuit, probes, code.n)
    circuit += build_stim_circuit(code, model, rounds=1)
    _append_probe_measurements(circuit, probes, code.n)
    k = len(probes)
    for i in range(k):
        circuit.append("DETECTOR", [stim.target_rec(-(2 * k - i)), stim.target_rec(-(k - i))])

    seed = int(rng.integers(0, 2**63 - 1))
    dets = circuit.compile_detector_sampler(seed=seed).sample(shots=N)
    outcomes = (1 - 2 * dets.astype(np.int8)).astype(np.int8)
    return ShotTable(
        L=L,
        D=D,
        L_outcomes=outcomes[:, : len(L.vecs)],
        D_outcomes=outcomes[:, len(L.vecs) :],
        mode=None,
    )


def empirical_blocks(shots: ShotTable, L: ProbeFamily, D: ProbeFamily) -> CovBlocks:
    """Return unbiased empirical covariance blocks from sampled ±1 outcomes.

    Ref: design/01_MATH_SPEC.md §3.5.
    """
    if not _same_probe_family(L, shots.L) or not _same_probe_family(D, shots.D):
        raise ValueError("shot table was sampled with a different probe family than requested")
    return CovBlocks(
        L=L,
        D=D,
        K_LL=_cov_hat(shots.L_outcomes, shots.L_outcomes),
        K_DL=_cov_hat(shots.D_outcomes, shots.L_outcomes),
        K_DD=_cov_hat(shots.D_outcomes, shots.D_outcomes),
    )


def omega_stat(
    code: Code,
    model: NoiseModel,
    L: ProbeFamily,
    D: ProbeFamily,
    N: int,
    B: int,
    rng: np.random.Generator,
    quantile: float = 0.99,
) -> Matrix:
    """Parametric bootstrap calibration matrix for blind-spot witnesses.

    Ref: design/01_MATH_SPEC.md §3.5.
    """
    model_blocks = MomentEngine(model, exact=False).cov_blocks(L, D)
    Xi_model, _ = xi_residual(model_blocks)
    values = []
    for _ in range(B):
        shots_b = sample_shots(code, model, L, D, N, rng)
        Xi_emp, _ = xi_residual(empirical_blocks(shots_b, L, D))
        values.append(blind_spot_witness(Xi_emp, Xi_model, D.labels).lam_max)
    threshold = float(np.percentile(np.asarray(values, dtype=float), quantile * 100.0))
    return threshold * np.eye(len(D.vecs), dtype=float)


def w1_witness(shots: ShotTable, model_blocks: CovBlocks, Omega_stat: Matrix) -> Witness:
    """Oracle blind-spot witness; deployability is not claimed.

    Ref: design/01_MATH_SPEC.md §3.5.
    """
    emp_blocks = empirical_blocks(shots, model_blocks.L, model_blocks.D)
    Xi_emp, _ = xi_residual(emp_blocks)
    Xi_model, _ = xi_residual(model_blocks)
    return blind_spot_witness(Xi_emp, _as_float(Xi_model) + _as_float(Omega_stat), model_blocks.D.labels)


def w2_witness(shots: ShotTable, model_blocks: CovBlocks, A_star: Matrix, Omega_stat: Matrix) -> Witness:
    """Deployable-shaped witness using only native-check covariance drift.

    W2a in design/06_W2_PHASE2.md §3.2 is this same raw statistic with
    Omega_stat set from its own null scale: call this function with
    Omega_stat=np.zeros((len(D), len(D))) inside w2_diagnosis.own_null_scale,
    then use threshold*np.eye(len(D)) for scored runs.

    Ref: design/01_MATH_SPEC.md §3.5.
    """
    emp_blocks = empirical_blocks(shots, model_blocks.L, model_blocks.D)
    Delta_LL = _as_float(emp_blocks.K_LL) - _as_float(model_blocks.K_LL)
    A = _as_float(A_star)
    Delta_D = A @ Delta_LL @ A.T
    return blind_spot_witness(Delta_D, Omega_stat, model_blocks.D.labels)


def degree2_model_params(engine: MomentEngine, F: ProbeFamily, N: int) -> tuple[np.ndarray, np.ndarray]:
    """Return exact model means and N-shot estimator covariance for F.

    theta_model is E[sigma_F]. Sigma_theta is Cov(sigma_F)/N, so it is the
    covariance of an N-shot empirical mean, not a per-shot covariance.

    Ref: design/06_W2_PHASE2.md §3.2.
    """
    if not engine.exact:
        raise ValueError("degree2_model_params requires an exact MomentEngine")
    if N <= 0:
        raise ValueError("N must be positive")
    theta_model = np.empty(len(F.vecs), dtype=object)
    for i, vec in enumerate(F.vecs):
        theta_model[i] = engine.mean(vec)
    cov = engine.cov_blocks(F, F).K_LL
    sigma_theta = np.empty(cov.shape, dtype=object)
    scale = Fraction(N)
    for i in range(cov.shape[0]):
        for j in range(cov.shape[1]):
            sigma_theta[i, j] = cov[i, j] / scale
    return theta_model, sigma_theta


def w2b_statistic(
    shots: ShotTable,
    F: ProbeFamily,
    theta_model: np.ndarray,
    sigma_theta: np.ndarray,
) -> float:
    """Return the degree-<=2 quadratic statistic for empirical means."""
    _require_shot_family(shots, F)
    theta_hat = np.asarray(shots.L_outcomes, dtype=float).mean(axis=0)
    diff = theta_hat - np.asarray(theta_model, dtype=float)
    sigma_pinv = np.linalg.pinv(np.asarray(sigma_theta, dtype=float), rcond=1e-12)
    return float(diff @ sigma_pinv @ diff.T)


def qubit_rate_dictionary(
    declared_model: NoiseModel,
    F: ProbeFamily,
    step: Fraction = Fraction(1, 10000),
) -> dict[int, np.ndarray]:
    """Return finite-difference qubit-rate sensitivity directions.

    The perturbation is exact in Fraction arithmetic, but the returned
    derivative direction is a first-order finite-difference approximation.
    """
    declared_engine = MomentEngine(declared_model, exact=True)
    theta_declared = _theta_exact(declared_engine, F)
    directions = {}
    for q in range(len(declared_model.per_qubit)):
        perturbed = _qubit_rate_perturbation(declared_model, q, step)
        theta_perturbed = _theta_exact(MomentEngine(perturbed, exact=True), F)
        directions[q] = np.asarray(
            [float(theta_perturbed[i] - theta_declared[i]) / float(step) for i in range(len(F.vecs))],
            dtype=float,
        )
    return directions


def w2c_naming(
    theta_hat: np.ndarray,
    theta_model: np.ndarray,
    sigma_theta_pinv: np.ndarray,
    dictionary: dict[int, np.ndarray],
) -> tuple[int, float]:
    """Return the qubit named by the signed whitened matched-filter score.

    A name is still returned if every score is negative; in that case it is the
    least-negative positive-rate direction, not a positive match.
    """
    diff = np.asarray(theta_hat, dtype=float) - np.asarray(theta_model, dtype=float)
    W = np.asarray(sigma_theta_pinv, dtype=float)
    best_q = -1
    best_score = -np.inf
    for q, direction in dictionary.items():
        d = np.asarray(direction, dtype=float)
        denom_sq = float(d @ W @ d.T)
        if denom_sq <= 0.0:
            score = 0.0
        else:
            score = float((d @ W @ diff.T) / np.sqrt(denom_sq))
        if score > best_score:
            best_q = q
            best_score = score
    return best_q, best_score


def qubit_logical_sensitivity(
    declared_model: NoiseModel,
    q: int,
    L: ProbeFamily,
    D: ProbeFamily,
    step: Fraction = Fraction(1, 10000),
) -> np.ndarray:
    """Return the top logical direction threatened by qubit q's rate bump."""
    perturbed = _qubit_rate_perturbation(declared_model, q, step)
    Xi_declared, _ = xi_residual(MomentEngine(declared_model, exact=True).cov_blocks(L, D))
    Xi_perturbed, _ = xi_residual(MomentEngine(perturbed, exact=True).cov_blocks(L, D))
    return blind_spot_witness(Xi_perturbed, Xi_declared, D.labels).z


def w2d_shot_scores(
    shots: ShotTable,
    F: ProbeFamily,
    theta_model: np.ndarray,
    sigma_single_pinv: np.ndarray,
) -> np.ndarray:
    """Return per-shot Mahalanobis scores using per-shot covariance pinv.

    sigma_single_pinv must be the pseudo-inverse of Cov(F,F), i.e. the N=1
    covariance from degree2_model_params, not the N-shot empirical-mean
    covariance used by w2b_statistic.
    """
    _require_shot_family(shots, F)
    X = np.asarray(shots.L_outcomes, dtype=float)
    diff = X - np.asarray(theta_model, dtype=float)[None, :]
    W = np.asarray(sigma_single_pinv, dtype=float)
    return np.einsum("ni,ij,nj->n", diff, W, diff, optimize=True)


def cusum_detect(scores: np.ndarray, baseline: float, threshold: float) -> int | None:
    """Return the first crossing index for a one-sided CUSUM, if any."""
    g = 0.0
    for t, score in enumerate(np.asarray(scores, dtype=float)):
        g = max(0.0, g + float(score) - baseline)
        if g > threshold:
            return t
    return None


def cusum_null_threshold(
    code: Code,
    model: NoiseModel,
    L: ProbeFamily,
    D: ProbeFamily,
    F: ProbeFamily,
    theta_model: np.ndarray,
    sigma_single_pinv: np.ndarray,
    run_length: int,
    B: int,
    rng: np.random.Generator,
    target_false_alarm: float = 0.01,
) -> tuple[float, float]:
    """Calibrate CUSUM baseline and threshold under declared-model null."""
    if run_length <= 0 or B <= 0:
        raise ValueError("run_length and B must be positive")
    if not 0.0 <= target_false_alarm <= 1.0:
        raise ValueError("target_false_alarm must be in [0, 1]")
    score_rows = []
    for _ in range(B):
        shots_b = sample_shots(code, model, F, D, run_length, rng)
        score_rows.append(w2d_shot_scores(shots_b, F, theta_model, sigma_single_pinv))
    all_scores = np.concatenate(score_rows)
    baseline = float(np.mean(all_scores))
    max_g = np.asarray([_cusum_max(row, baseline) for row in score_rows], dtype=float)
    allowed = int(np.floor(target_false_alarm * B))
    if allowed >= B:
        threshold = 0.0
    else:
        threshold = float(np.sort(max_g)[B - allowed - 1])
    return baseline, threshold


def _theta_exact(engine: MomentEngine, F: ProbeFamily) -> np.ndarray:
    return np.asarray([engine.mean(vec) for vec in F.vecs], dtype=object)


def _qubit_rate_perturbation(model: NoiseModel, q: int, step: Fraction) -> NoiseModel:
    if model.hidden is not None:
        raise ValueError("qubit-rate perturbations require a non-hidden model")
    if not 0 <= q < len(model.per_qubit):
        raise ValueError("qubit index out of range")
    if step <= 0:
        raise ValueError("step must be positive")
    scale = Fraction(1) + Fraction(step)
    per_qubit = list(model.per_qubit)
    pI, pX, pY, pZ = per_qubit[q]
    total_error = Fraction(1) - pI
    new_dist = (Fraction(1) - scale * total_error, scale * pX, scale * pY, scale * pZ)
    if any(p < 0 for p in new_dist):
        raise ValueError("qubit-rate perturbation produced a negative probability")
    per_qubit[q] = new_dist
    return NoiseModel(f"{model.name}_Q{q}_RATE_PERT", tuple(per_qubit), model.injection, None)


def _require_shot_family(shots: ShotTable, F: ProbeFamily) -> None:
    if not _same_probe_family(F, shots.L):
        raise ValueError("shot table was sampled with a different L probe family than requested")


def _cusum_max(scores: np.ndarray, baseline: float) -> float:
    g = 0.0
    max_g = 0.0
    for score in np.asarray(scores, dtype=float):
        g = max(0.0, g + float(score) - baseline)
        max_g = max(max_g, g)
    return max_g


def _sample_classical(
    code: Code,
    model: NoiseModel,
    L: ProbeFamily,
    D: ProbeFamily,
    N: int,
    rng: np.random.Generator,
) -> ShotTable:
    if model.hidden is None:
        return _sample_classical_iid(code, model, L, D, N, rng)
    L_outcomes = np.empty((N, len(L.vecs)), dtype=np.int8)
    D_outcomes = np.empty((N, len(D.vecs)), dtype=np.int8)
    mode_history = np.empty(N, dtype=np.int64)
    mode_state = 0
    for shot in range(N):
        e, mode_state = sample_error(model, rng, mode_state)
        mode_history[shot] = int(mode_state)
        for i, vec in enumerate(L.vecs):
            L_outcomes[shot, i] = 1 - 2 * sympl(vec, e)
        for i, vec in enumerate(D.vecs):
            D_outcomes[shot, i] = 1 - 2 * sympl(vec, e)
    return ShotTable(L=L, D=D, L_outcomes=L_outcomes, D_outcomes=D_outcomes, mode=mode_history)


def _sample_classical_iid(
    code: Code,
    model: NoiseModel,
    L: ProbeFamily,
    D: ProbeFamily,
    N: int,
    rng: np.random.Generator,
) -> ShotTable:
    paulis = np.empty((N, code.n), dtype=np.uint8)
    for q, dist in enumerate(model.per_qubit):
        paulis[:, q] = rng.choice(4, size=N, p=np.asarray([float(x) for x in dist], dtype=float))
    e_x = ((paulis == 1) | (paulis == 2)).astype(np.uint8)
    e_z = ((paulis == 2) | (paulis == 3)).astype(np.uint8)
    if model.injection is not None:
        injected = rng.random(N) < float(model.injection.prob)
        if np.any(injected):
            inj = model.injection.vec
            inj_x = np.asarray(inj[: code.n], dtype=np.uint8)
            inj_z = np.asarray(inj[code.n :], dtype=np.uint8)
            e_x[injected] ^= inj_x
            e_z[injected] ^= inj_z
    outcomes = _probe_outcomes_from_bits(e_x, e_z, L.vecs + D.vecs)
    return ShotTable(
        L=L,
        D=D,
        L_outcomes=outcomes[:, : len(L.vecs)],
        D_outcomes=outcomes[:, len(L.vecs) :],
        mode=None,
    )


def _probe_outcomes_from_bits(e_x: np.ndarray, e_z: np.ndarray, probes: tuple[PauliVec, ...]) -> np.ndarray:
    N, n = e_x.shape
    out = np.empty((N, len(probes)), dtype=np.int8)
    for i, vec in enumerate(probes):
        probe_x = np.asarray(vec[:n], dtype=np.uint8)
        probe_z = np.asarray(vec[n:], dtype=np.uint8)
        bits = ((e_z @ probe_x) + (e_x @ probe_z)) & 1
        out[:, i] = (1 - 2 * bits).astype(np.int8)
    return out


def _all_commute(vecs: tuple[PauliVec, ...]) -> bool:
    for i in range(len(vecs)):
        for j in range(i + 1, len(vecs)):
            if sympl(vecs[i], vecs[j]) != 0:
                return False
    return True


def _same_probe_family(a: ProbeFamily, b: ProbeFamily) -> bool:
    return (
        a.role == b.role
        and a.labels == b.labels
        and len(a.vecs) == len(b.vecs)
        and all(np.array_equal(x, y) for x, y in zip(a.vecs, b.vecs))
    )


def _cov_hat(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    Af = np.asarray(A, dtype=float)
    Bf = np.asarray(B, dtype=float)
    if Af.shape[0] != Bf.shape[0]:
        raise ValueError("covariance inputs must have the same number of shots")
    if Af.shape[0] < 2:
        raise ValueError("at least two shots are required for unbiased covariance")
    A0 = Af - Af.mean(axis=0)
    B0 = Bf - Bf.mean(axis=0)
    return (A0.T @ B0) / float(Af.shape[0] - 1)


def _as_float(M: Matrix) -> np.ndarray:
    return np.asarray(M, dtype=float)


def _append_probe_measurements(circuit: stim.Circuit, probes: tuple[PauliVec, ...], n: int) -> None:
    for vec in probes:
        targets = _targets_for_vec(vec, n)
        if not targets:
            raise ValueError("cannot MPP-measure an identity probe")
        circuit.append("MPP", stim.target_combined_paulis(targets))


def _targets_for_vec(vec: PauliVec, n: int) -> list[stim.GateTarget]:
    targets = []
    for q in range(n):
        x = int(vec[q])
        z = int(vec[n + q])
        if x and z:
            targets.append(stim.target_y(q))
        elif x:
            targets.append(stim.target_x(q))
        elif z:
            targets.append(stim.target_z(q))
    return targets


def _require_uniform_per_qubit(model: NoiseModel) -> None:
    if not model.per_qubit:
        raise ValueError("noise model has no qubits")
    first = model.per_qubit[0]
    if any(dist != first for dist in model.per_qubit):
        raise ValueError("Stim circuit builder requires uniform per-qubit noise")
    if any(not isinstance(p, Fraction) for dist in model.per_qubit for p in dist):
        raise ValueError("noise probabilities must be Fractions")
