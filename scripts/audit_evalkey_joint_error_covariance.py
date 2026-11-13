#!/usr/bin/env python3
"""Exact joint covariance and characteristic-function audit.

For independent eta=2 errors e_0,...,e_13, define
z_j=e_{j+1}-B e_j, j=0,...,12.
The coefficient-level transformation is z=D e, where D is 13x14
with entries (-B,1) in each row. This script audits the exact covariance
D D^T (eta=2 has variance one) and the exact joint characteristic-function
factorization. It is not a key-recovery attack or security estimate.
"""
from math import cos, pi, prod, sqrt

B = 1 << 16
N = 8192
ROWS = 13
COLS = 14


def matmul_transpose_determinant():
    # C = D D^T: tridiagonal with B^2+1 on the diagonal and -B
    # on the two adjacent diagonals. Compute determinant exactly by
    # the continuant recurrence.
    diagonal = B * B + 1
    offdiag_sq = B * B
    d_prev2 = 1
    d_prev1 = diagonal
    for _ in range(2, ROWS + 1):
        d_prev2, d_prev1 = d_prev1, diagonal * d_prev1 - offdiag_sq * d_prev2
    return d_prev1


def exact_covariance():
    return [
        [B * B + 1 if i == j else (-B if abs(i - j) == 1 else 0)
         for j in range(ROWS)]
        for i in range(ROWS)
    ]


def joint_characteristic(t):
    """Evaluate exact-form product numerically for a supplied real vector t.

    eta=2 X has characteristic function cos(u/2)^4. For z=D e,
    phi_z(t)=product_k cos((D^T t)_k/2)^4.
    """
    if len(t) != ROWS:
        raise ValueError(f"expected {ROWS} arguments")
    projected = []
    for k in range(COLS):
        if k == 0:
            value = -B * t[0]
        elif k == COLS - 1:
            value = t[ROWS - 1]
        else:
            value = t[k - 1] - B * t[k]
        projected.append(value)
    return prod(cos(value / 2.0) ** 4 for value in projected)


def main():
    C = exact_covariance()
    det = matmul_transpose_determinant()
    assert det > 0
    assert all(C[i][j] == C[j][i] for i in range(ROWS) for j in range(ROWS))
    assert all(C[i][j] == 0 for i in range(ROWS) for j in range(ROWS) if abs(i-j) > 1)

    # Gershgorin bounds establish positive definiteness because
    # diagonal - sum(abs(off-diagonal)) = (B-1)^2 > 0.
    strict_margin = (B - 1) ** 2
    assert strict_margin > 0

    print(f"N={N}; B={B}; transformed_equations={ROWS}; original_errors={COLS}")
    print("eta=2 coefficient law: P(X=-2,-1,0,1,2)=(1,4,6,4,1)/16")
    print("Covariance matrix C = D D^T (exact integer entries):")
    for row in C:
        print(" ".join(str(x) for x in row))
    print(f"diagonal={B*B+1}")
    print(f"adjacent_covariance={-B}")
    print("nonadjacent_covariance=0")
    print(f"strict_diagonal_dominance_margin={strict_margin}")
    print(f"determinant_exact={det}")
    print("positive_definite=True")
    print("joint characteristic function:")
    print("phi(t_0,...,t_12) = product_{k=0}^{13} cos((D^T t)_k/2)^4")
    print("This factorization retains the exact eta=2 discrete law.")
    print("It proves dependence between adjacent transformed errors; covariance alone is not the full law.")
    print("Coefficient positions are independent under the independent coefficient sampler.")
    print("No attack cost, distinguisher, or secret-recovery result is computed.")


if __name__ == "__main__":
    main()
