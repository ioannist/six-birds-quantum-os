"""explicit-state Markov models of QEC rounds   MS §4.1"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

import numpy as np

from sbqos.codes import Code, PauliVec, canonical_rep, logical_flips, rep_code, surface_code, sympl
from sbqos.moments import Matrix, MomentEngine
from sbqos.noise import HiddenSpec, NoiseModel, n1, n2, n4, n5


@dataclass(frozen=True)
class MarkovModel:
    name: str
    n_syndrome_bits: int
    n_logical_bits: int
    states: tuple[tuple[int, ...], ...]
    P: Matrix
    exact: bool
    lens_syndrome: np.ndarray
    lens_decoded: np.ndarray
    lens_mode_hidden: bool
    is_absorbing: bool
    decoder_name: str


def qec_markov_model(
    code: Code,
    model: NoiseModel,
    tracked_logicals: tuple[PauliVec, ...],
    decoder: str,
    exact: bool,
) -> MarkovModel:
    """Build the QEC Markov model from syndrome/logical-class signatures.

    Ref: design/01_MATH_SPEC.md §4.1.
    """
    if decoder not in {"minimum_weight", "broken"}:
        raise ValueError("decoder must be 'minimum_weight' or 'broken'")

    n_syndrome_bits = len(code.checks)
    n_logical_bits = len(tracked_logicals)
    n_signature_bits = n_syndrome_bits + n_logical_bits
    if model.hidden is not None:
        return _hidden_qec_markov_model(
            code,
            model,
            tracked_logicals,
            decoder,
            exact,
            n_syndrome_bits,
            n_logical_bits,
            n_signature_bits,
        )

    n_states = 2**n_signature_bits
    if n_states > 20000:
        raise ValueError("Markov state space exceeds size guard")

    basis = code.checks + tracked_logicals
    delta = _delta_distribution(code.n, basis, model, exact)
    idx = np.arange(n_states, dtype=np.int64)
    P = delta[idx[:, None] ^ idx[None, :]]
    lens_syndrome = idx // (2**n_logical_bits)
    lens_decoded = _decoded_lens(code, tracked_logicals, decoder, lens_syndrome, idx, n_logical_bits)
    states = tuple(tuple(int(bit) for bit in _int_to_bits(int(i), n_signature_bits)) for i in idx)

    return MarkovModel(
        name=f"{code.name}_{model.name}_{decoder}",
        n_syndrome_bits=n_syndrome_bits,
        n_logical_bits=n_logical_bits,
        states=states,
        P=P,
        exact=exact,
        lens_syndrome=lens_syndrome.astype(np.int64),
        lens_decoded=lens_decoded.astype(np.int64),
        lens_mode_hidden=False,
        is_absorbing=False,
        decoder_name=decoder,
    )


def stationary(P: Matrix) -> np.ndarray:
    """Return a stationary distribution, verified in float arithmetic.

    Ref: design/02_ARCHITECTURE.md §4.7.
    """
    Pf = np.asarray(P, dtype=float)
    eigenvalues, eigenvectors = np.linalg.eig(Pf.T)
    idx = int(np.argmin(np.abs(eigenvalues - 1.0)))
    pi = np.real(eigenvectors[:, idx])
    if np.sum(pi) < 0:
        pi = -pi
    pi = np.where(pi < 0, 0.0, pi)
    total = np.sum(pi)
    if total <= 0:
        raise ValueError("stationary eigenvector has nonpositive mass")
    pi = pi / total
    residual = np.linalg.norm(pi @ Pf - pi, ord=1)
    if residual > 1e-12:
        raise ValueError(f"stationary distribution did not converge: residual={residual!r}")
    return pi


def rep3_n1_model(decoder: str, exact: bool = True) -> MarkovModel:
    code = rep_code(3)
    return qec_markov_model(code, n1(Fraction(1, 20), code.n), code.logicals[1:], decoder, exact)


def rep5_n1_model(decoder: str, exact: bool = True) -> MarkovModel:
    code = rep_code(5)
    return qec_markov_model(code, n1(Fraction(1, 20), code.n), code.logicals[1:], decoder, exact)


def surf3_n2_model(decoder: str, exact: bool = False) -> MarkovModel:
    code = surface_code(3)
    return qec_markov_model(code, n2(Fraction(3, 100), code.n), code.logicals, decoder, exact)


def rep3_n4_model(
    p0: Fraction = Fraction(1, 50),
    s: Fraction = Fraction(1, 50),
    decoder: str = "minimum_weight",
    exact: bool = False,
) -> MarkovModel:
    code = rep_code(3)
    return qec_markov_model(code, n4(p0, s, code.n), code.logicals[1:], decoder, exact)


def rep3_n5_model(
    p: Fraction = Fraction(1, 20),
    r: Fraction = Fraction(1, 100),
    leak_qubit: int = 1,
    decoder: str = "minimum_weight",
    exact: bool = False,
) -> MarkovModel:
    code = rep_code(3)
    return qec_markov_model(code, n5(p, r, code.n, leak_qubit), code.logicals[1:], decoder, exact)


def _hidden_qec_markov_model(
    code: Code,
    model: NoiseModel,
    tracked_logicals: tuple[PauliVec, ...],
    decoder: str,
    exact: bool,
    n_syndrome_bits: int,
    n_logical_bits: int,
    n_signature_bits: int,
) -> MarkovModel:
    hidden = model.hidden
    if hidden is None:
        raise ValueError("hidden model branch requires hidden dynamics")

    n_sc = 2**n_signature_bits
    n_states = 2 * n_sc
    if n_states > 20000:
        raise ValueError("Markov state space exceeds size guard")

    basis = code.checks + tracked_logicals
    deltas = tuple(_delta_distribution(code.n, basis, mode_model, exact) for mode_model in hidden.mode_models)
    T_mode = _mode_transition_matrix(hidden, exact)
    dtype = object if exact else np.float64
    P = np.empty((n_states, n_states), dtype=dtype)
    idx_sc = np.arange(n_sc, dtype=np.int64)
    xor_idx = idx_sc[:, None] ^ idx_sc[None, :]
    for mode in range(2):
        row_slice = slice(mode * n_sc, (mode + 1) * n_sc)
        for next_mode in range(2):
            col_slice = slice(next_mode * n_sc, (next_mode + 1) * n_sc)
            P[row_slice, col_slice] = T_mode[mode, next_mode] * deltas[next_mode][xor_idx]

    lens_syndrome_sc = idx_sc // (2**n_logical_bits)
    lens_decoded_sc = _decoded_lens(code, tracked_logicals, decoder, lens_syndrome_sc, idx_sc, n_logical_bits)
    states = tuple(
        tuple(int(bit) for bit in _int_to_bits(sc, n_signature_bits)) + (mode,)
        for mode in range(2)
        for sc in range(n_sc)
    )

    return MarkovModel(
        name=f"{code.name}_{model.name}_{decoder}",
        n_syndrome_bits=n_syndrome_bits,
        n_logical_bits=n_logical_bits,
        states=states,
        P=P,
        exact=exact,
        lens_syndrome=np.tile(lens_syndrome_sc, 2).astype(np.int64),
        lens_decoded=np.tile(lens_decoded_sc, 2).astype(np.int64),
        lens_mode_hidden=True,
        is_absorbing=hidden.kind == "latching",
        decoder_name=decoder,
    )


def _mode_transition_matrix(hidden: HiddenSpec, exact: bool) -> np.ndarray:
    p = hidden.transition_prob if exact else float(hidden.transition_prob)
    one = Fraction(1) if exact else 1.0
    zero = Fraction(0) if exact else 0.0
    dtype = object if exact else np.float64
    if hidden.kind == "alternating":
        return np.array(((one - p, p), (p, one - p)), dtype=dtype)
    if hidden.kind == "latching":
        return np.array(((one - p, p), (zero, one)), dtype=dtype)
    raise ValueError(f"unknown hidden kind: {hidden.kind!r}")


def _delta_distribution(
    n: int,
    basis: tuple[PauliVec, ...],
    model: NoiseModel,
    exact: bool,
) -> np.ndarray:
    r = len(basis)
    n_states = 2**r
    engine = MomentEngine(model, exact=exact)
    dtype = object if exact else np.float64
    moments = np.empty(n_states, dtype=dtype)
    for subset in range(n_states):
        v = np.zeros(2 * n, dtype=np.uint8)
        for i, basis_vec in enumerate(basis):
            if (subset >> (r - 1 - i)) & 1:
                v ^= basis_vec
        moments[subset] = engine.mean(v)

    delta = _hadamard_transform(moments)
    if exact:
        scale = Fraction(1, n_states)
        delta = np.array([scale * x for x in delta], dtype=object)
        if sum(delta.tolist(), Fraction(0)) != Fraction(1):
            raise AssertionError("exact delta distribution does not sum to 1")
        if any(x < 0 for x in delta):
            raise AssertionError("exact delta distribution has negative entries")
    else:
        delta = delta / float(n_states)
        if abs(float(np.sum(delta)) - 1.0) > 1e-9:
            raise AssertionError("float delta distribution does not sum to 1")
        if float(np.min(delta)) < -1e-9:
            raise AssertionError("float delta distribution has negative entries")
    return delta


def _hadamard_transform(values: np.ndarray) -> np.ndarray:
    out = values.copy()
    h = 1
    n = out.shape[0]
    while h < n:
        for start in range(0, n, 2 * h):
            left = out[start : start + h].copy()
            right = out[start + h : start + 2 * h].copy()
            out[start : start + h] = left + right
            out[start + h : start + 2 * h] = left - right
        h *= 2
    return out


def _decoded_lens(
    code: Code,
    tracked_logicals: tuple[PauliVec, ...],
    decoder: str,
    lens_syndrome: np.ndarray,
    idx: np.ndarray,
    n_logical_bits: int,
) -> np.ndarray:
    if decoder == "broken":
        return np.zeros_like(idx, dtype=np.int64)

    decoded = np.empty_like(idx, dtype=np.int64)
    logical_mask = 2**n_logical_bits - 1
    for state_index, syndrome_int in enumerate(lens_syndrome):
        logical_int = int(idx[state_index] & logical_mask)
        syndrome_bits = _int_to_bits(int(syndrome_int), len(code.checks))
        recovery = canonical_rep(code, syndrome_bits)
        recovery_logical = _logical_int_for(recovery, tracked_logicals)
        decoded[state_index] = logical_int ^ recovery_logical
    return decoded


def _logical_int_for(e: PauliVec, tracked_logicals: tuple[PauliVec, ...]) -> int:
    value = 0
    for logical in tracked_logicals:
        value = (value << 1) | sympl(logical, e)
    return value


def _int_to_bits(value: int, width: int) -> np.ndarray:
    return np.array([(value >> (width - 1 - i)) & 1 for i in range(width)], dtype=np.uint8)
