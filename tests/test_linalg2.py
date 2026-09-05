import numpy as np

from sbqos.linalg2 import in_span_f2, rank_f2, row_reduce_f2


def test_rank_f2_hand_computable_dependent_rows():
    M = np.array(
        [
            [1, 0, 1],
            [0, 1, 1],
            [1, 1, 0],
        ],
        dtype=np.uint8,
    )

    # Over GF(2), row3 = row1 XOR row2, so only two rows are independent.
    assert rank_f2(M) == 2


def test_row_reduce_and_in_span_f2_hand_computable():
    M = np.array(
        [
            [1, 0, 1],
            [0, 1, 1],
            [1, 1, 0],
        ],
        dtype=np.uint8,
    )

    # The same hand relation row3 = row1 XOR row2 reduces the last row to zero.
    R, pivots = row_reduce_f2(M)
    assert pivots == [0, 1]
    np.testing.assert_array_equal(
        R,
        np.array(
            [
                [1, 0, 1],
                [0, 1, 1],
                [0, 0, 0],
            ],
            dtype=np.uint8,
        ),
    )
    assert in_span_f2(M, np.array([1, 1, 0], dtype=np.uint8))
    assert not in_span_f2(M, np.array([1, 0, 0], dtype=np.uint8))
