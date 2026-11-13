#!/usr/bin/env sage -python
"""LLL search for short gadget-level relations cancelling the shared s^2 target.

For w in Z^14 with sum_j w_j B^j = 0 mod Q, the corresponding public
linear combination of evaluation-key equations cancels s^2. Its error is
sum_j w_j e_j, with coefficient support bounded by 2*||w||_1 and variance
||w||_2^2 under independent eta=2 coefficient errors.

This is a relation-search diagnostic, not a key-recovery attack or a security
estimate. A short relation only supplies another derived sample; its usefulness
depends on the error size, ring structure, and joint-sample analysis.
"""
from sage.all import ZZ, matrix

N = 8192
BASE = 1 << 16
LEVELS = 14
Q_PRIMES = [
    36028797002170369,
    36028796951838721,
    18014398508400641,
    18014398507892737,
]
Q = ZZ.prod(Q_PRIMES)


def build_kernel_lattice():
    powers = [pow(BASE, j, Q) for j in range(LEVELS)]
    # BASE is invertible modulo odd Q. Every vector in this row lattice
    # satisfies dot(w, powers) == 0 (mod Q).
    inv_last = ZZ(powers[-1]).inverse_mod(Q)
    basis = matrix(ZZ, LEVELS, LEVELS)
    for i in range(LEVELS - 1):
        basis[i, i] = 1
        basis[i, LEVELS - 1] = (-powers[i] * inv_last) % Q
    basis[LEVELS - 1, LEVELS - 1] = Q
    return basis, powers


def main():
    basis, powers = build_kernel_lattice()
    determinant = abs(basis.det())
    assert determinant == Q, "kernel lattice determinant must equal Q"
    print(f"N={N}; Q_bits={Q.nbits()}; B={BASE}; levels={LEVELS}")
    print(f"kernel lattice determinant bits={determinant.nbits()}")
    print("Running exact-integer LLL on the 14-dimensional modular-kernel lattice...")
    reduced = basis.LLL(delta=0.99)
    rows = []
    for i in range(LEVELS):
        w = [ZZ(reduced[i, j]) for j in range(LEVELS)]
        if not any(w):
            continue
        relation = sum(w[j] * powers[j] for j in range(LEVELS)) % Q
        assert relation == 0, f"LLL row {i} is not a modular relation"
        l1 = sum(abs(x) for x in w)
        l2_sq = sum(x*x for x in w)
        max_abs = max(abs(x) for x in w)
        rows.append((l1, l2_sq, max_abs, w))
    rows.sort(key=lambda x: (x[0], x[1], x[2]))
    adjacent_l1 = BASE + 1
    print(f"adjacent-pair baseline: ||w||_1={adjacent_l1}; error_support_radius<={2*adjacent_l1}")
    print("Shortest LLL-reduced modular relations (sorted by L1):")
    for rank, (l1, l2_sq, max_abs, w) in enumerate(rows[:LEVELS], 1):
        print(
            f"rank={rank}; L1={l1}; L2_squared={l2_sq}; "
            f"max_abs={max_abs}; error_support_radius<={2*l1}; "
            f"error_variance={l2_sq}; w={w}"
        )
    print("All reported rows satisfy the exact modular target-cancellation relation.")
    print("Caution: these are derived correlated samples from one transcript, not independent keys.")
    print("No secret-recovery attack or concrete security estimate is performed.")


if __name__ == "__main__":
    main()
