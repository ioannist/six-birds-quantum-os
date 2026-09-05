from fractions import Fraction

import numpy as np
import pytest

from sbqos.closure import (
    _prediction_context,
    _predictive_fit_counts,
    assemble_certificate,
    closure_deficit,
    closure_deficit_finite_horizon,
    closure_deficit_variational_check,
    full_existence_certificate,
    idem_defect,
    predictive_gap,
    predictive_gap_finite_horizon,
    prototype_stability,
    retention_error,
    route_mismatch,
    route_mismatch_finite_horizon,
)
from sbqos.markov import rep3_n1_model, rep3_n5_model, stationary


def test_rep3_minimum_weight_idempotence_retention_tau1_exact():
    model = rep3_n1_model("minimum_weight", exact=True)

    delta = idem_defect(model, "decoded", tau=1)
    epsilon, per_label = retention_error(model, "decoded", tau=1)

    assert delta == Fraction(57159, 8000000)
    assert epsilon == Fraction(29, 4000)
    assert per_label == [Fraction(29, 4000), Fraction(29, 4000)]
    assert delta <= epsilon


def test_rep3_minimum_weight_idempotence_retention_tau2_exact():
    model = rep3_n1_model("minimum_weight", exact=True)

    delta = idem_defect(model, "decoded", tau=2)
    epsilon, _per_label = retention_error(model, "decoded", tau=2)

    assert delta == Fraction(192591723519, 8000000000000)
    assert epsilon == Fraction(101441, 4000000)
    assert delta <= epsilon


def test_rep3_minimum_weight_multiplicity_and_route_mismatch_exact():
    model = rep3_n1_model("minimum_weight", exact=True)

    assert prototype_stability(model, "decoded", tau=1, eps_stable=0.05) == 2
    assert route_mismatch(model, "decoded", tau=1) == Fraction(513, 8000)
    assert route_mismatch(model, "syndrome", tau=1) == Fraction(0)


def test_idem_and_retention_reject_syndrome_lens():
    model = rep3_n1_model("minimum_weight", exact=True)

    with pytest.raises(ValueError, match="only defined for the decoded lens"):
        idem_defect(model, "syndrome", tau=1)
    with pytest.raises(ValueError, match="only defined for the decoded lens"):
        retention_error(model, "syndrome", tau=1)


def test_stationary_uniform_for_xor_translation_models(surf3_n2_minimum_weight_model):
    rep = rep3_n1_model("minimum_weight", exact=True)
    surf = surf3_n2_minimum_weight_model

    for model in (rep, surf):
        pi = stationary(model.P)
        expected = np.full(model.P.shape[0], 1.0 / model.P.shape[0])
        np.testing.assert_allclose(pi, expected, atol=1e-12)


def test_broken_decoder_trivialization_control():
    model = rep3_n1_model("broken", exact=True)

    delta = idem_defect(model, "decoded", tau=1)
    epsilon, _per_label = retention_error(model, "decoded", tau=1)
    multiplicity = prototype_stability(model, "decoded", tau=1)
    cert = assemble_certificate(
        delta,
        epsilon,
        route_mismatch(model, "decoded", tau=1),
        cd_tau=999.0,
        delta_pred=0.0,
        delta_max=0.1,
        cd_max=0.1,
        multiplicity=multiplicity,
    )

    assert delta == Fraction(0)
    assert multiplicity == 1
    assert cert.status == "trivialized"


def test_certificate_classifier_priority_cases():
    assert (
        assemble_certificate(0.0, 0.0, 0.0, 0.0, 0.0, delta_max=0.1, cd_max=0.1, multiplicity=1).status
        == "trivialized"
    )
    assert (
        assemble_certificate(0.0, 0.0, 0.0, 1.0, 0.0, delta_max=0.1, cd_max=0.1, multiplicity=2).status
        == "non_closed"
    )
    assert (
        assemble_certificate(0.5, 0.5, 0.0, 0.0, 0.0, delta_max=0.1, cd_max=0.1, multiplicity=2).status
        == "degrading"
    )
    assert (
        assemble_certificate(0.01, 0.01, 0.0, 0.0, 0.0, delta_max=0.1, cd_max=0.1, multiplicity=2).status
        == "certified"
    )


def test_surf3_float_idempotence_bound_route_mismatch_and_multiplicity(surf3_n2_minimum_weight_model):
    model = surf3_n2_minimum_weight_model

    delta = idem_defect(model, "decoded", tau=1)
    epsilon, _per_label = retention_error(model, "decoded", tau=1)

    assert delta <= epsilon + 1e-9
    assert route_mismatch(model, "syndrome", tau=1) < 1e-9
    assert prototype_stability(model, "decoded", tau=1, eps_stable=0.05) >= 2


def test_rep3_closure_deficit_ground_truth_values():
    model = rep3_n1_model("minimum_weight", exact=True)

    cd1 = closure_deficit(model, "decoded", tau=1)
    cd2 = closure_deficit(model, "decoded", tau=2)

    assert abs(cd1 - 0.014804630357312679) <= 1e-9
    assert abs(cd2 - 0.02102502284988188) <= 1e-9
    assert cd1 >= 0
    assert cd2 >= 0


def test_thm_B5_lumpable_zero_deficit_for_syndrome_lens():
    model = rep3_n1_model("minimum_weight", exact=True)
    context = _prediction_context(model, "syndrome", tau=1)

    for label in sorted(set(int(v) for v in context.lens_values)):
        rows = [context.R[i] for i, value in enumerate(context.lens_values) if int(value) == label]
        first = rows[0]
        for row in rows[1:]:
            np.testing.assert_array_equal(row, first)

    assert closure_deficit(model, "syndrome", tau=1) < 1e-9


def test_closure_deficit_variational_property_rep3():
    model = rep3_n1_model("minimum_weight", exact=True)

    assert closure_deficit_variational_check(model, tau=1, n_perturbations=10, seed=0)


def test_absorbing_n5_rejects_stationary_closure_paths_and_finite_horizon_runs():
    model = rep3_n5_model()

    with pytest.raises(ValueError, match="closure_deficit_finite_horizon"):
        closure_deficit(model, "decoded", tau=1)
    with pytest.raises(ValueError, match="closure_deficit_finite_horizon"):
        full_existence_certificate(model, tau=1, delta_max=0.1, cd_max=0.1)
    with pytest.raises(ValueError, match="route_mismatch_finite_horizon"):
        route_mismatch(model, "decoded", tau=1)

    cd_h1 = closure_deficit_finite_horizon(model, tau=1, horizon=1, initial_state=0)
    cd_h5 = closure_deficit_finite_horizon(model, tau=1, horizon=5, initial_state=0)
    cd_h20 = closure_deficit_finite_horizon(model, tau=1, horizon=20, initial_state=0)

    assert np.isfinite(cd_h5)
    assert cd_h1 == pytest.approx(0.009891861549110613)
    assert cd_h5 == pytest.approx(0.02682316084930462)
    assert cd_h20 == pytest.approx(0.06901638537985477)
    assert cd_h1 != cd_h20


def test_route_mismatch_finite_horizon_converges_to_rep3_stationary_baseline():
    model = rep3_n1_model("minimum_weight", exact=True)

    rm = route_mismatch_finite_horizon(model, "decoded", tau=1, horizon=100, initial_state=0)

    assert abs(rm - float(Fraction(513, 8000))) <= 1e-6


def test_absorbing_n5_route_mismatch_finite_horizon_runs_and_grows():
    model = rep3_n5_model()

    with pytest.raises(ValueError, match="route_mismatch_finite_horizon"):
        route_mismatch(model, "decoded", tau=1)

    rm_h1 = route_mismatch_finite_horizon(model, "decoded", tau=1, horizon=1, initial_state=0)
    rm_h20 = route_mismatch_finite_horizon(model, "decoded", tau=1, horizon=20, initial_state=0)
    rm_h100 = route_mismatch_finite_horizon(model, "decoded", tau=1, horizon=100, initial_state=0)
    rm_syndrome = route_mismatch_finite_horizon(model, "syndrome", tau=1, horizon=5, initial_state=0)

    assert np.isfinite(rm_h1)
    assert np.isfinite(rm_h20)
    assert np.isfinite(rm_h100)
    assert rm_h1 >= 0.0
    assert rm_h20 >= 0.0
    assert rm_h100 >= 0.0
    assert rm_h1 < rm_h20 < rm_h100
    assert np.isfinite(rm_syndrome)
    assert rm_syndrome >= 0.0


def test_absorbing_n5_predictive_gap_requires_finite_horizon_variant():
    model = rep3_n5_model()

    with pytest.raises(ValueError, match="predictive_gap_finite_horizon"):
        predictive_gap(model, tau_stream_length=20000, seed=0)

    gap_h1 = predictive_gap_finite_horizon(model, tau_stream_length=20000, seed=0, horizon=1, initial_state=0)
    gap_h5 = predictive_gap_finite_horizon(model, tau_stream_length=20000, seed=0, horizon=5, initial_state=0)
    gap_h5_repeat = predictive_gap_finite_horizon(
        model,
        tau_stream_length=20000,
        seed=0,
        horizon=5,
        initial_state=0,
    )
    gap_h20 = predictive_gap_finite_horizon(model, tau_stream_length=20000, seed=0, horizon=20, initial_state=0)

    assert np.isfinite(gap_h5)
    assert gap_h5 == gap_h5_repeat
    assert gap_h1 != gap_h20


def test_predictive_gap_corrected_split_value_finite_and_deterministic():
    model = rep3_n1_model("minimum_weight", exact=True)

    gap1 = predictive_gap(model, tau_stream_length=20000, seed=0)
    gap2 = predictive_gap(model, tau_stream_length=20000, seed=0)

    assert np.isfinite(gap1)
    assert gap1 == pytest.approx(-0.00011741655582642174)
    assert gap1 == gap2


def test_predictive_gap_fit_counts_use_train_half_only():
    stream = np.array([0, 0, 0, 0, 1, 1, 1, 1], dtype=np.int64)
    split = stream.shape[0] // 2
    train = stream[:split]
    heldout = stream[split:]

    assert split == 4
    assert np.all(np.arange(train.shape[0]) < split)
    assert np.all(np.arange(split, split + heldout.shape[0]) >= split)

    counts1, counts2 = _predictive_fit_counts(train, n_labels=2)

    assert counts1[0, 0] == 4.0
    assert counts1[1, 1] == 1.0
    assert counts2[0, 0, 0] == 3.0
    assert counts2[1, 1, 1] == 1.0


def test_full_existence_certificate_certified_for_rep3_minimum_weight():
    model = rep3_n1_model("minimum_weight", exact=True)

    cert = full_existence_certificate(model, tau=1, delta_max=0.1, cd_max=0.1, seed=0)

    assert cert.status == "certified"
    assert cert.delta <= 0.1
    assert cert.cd_tau <= 0.1
    assert cert.multiplicity == 2


def test_full_existence_certificate_trivialized_for_broken_decoder():
    model = rep3_n1_model("broken", exact=True)

    cert = full_existence_certificate(model, tau=1, delta_max=0.0, cd_max=0.0, seed=0)

    assert cert.status == "trivialized"
