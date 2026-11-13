#!/usr/bin/env sage -python
"""Exact weighted eta=2 error laws for LLL modular target-cancellation relations.

For w in Z^14 with sum_j w_j B^j = 0 mod Q, the derived equation cancels
the common B^j*s^2 target. Its one-coefficient error is sum_j w_j*e_j.
This script computes exact integer PMFs for the Pareto frontier of the LLL
reduced modular-kernel basis, and compares them with adjacent cancellation.

This is distribution analysis of derived samples, not a key-recovery attack.
"""
from sage.all import ZZ, matrix

B = 1 << 16
LEVELS = 14
Q_PRIMES = [
    36028797002170369,
    36028796951838721,
    18014398508400641,
    18014398507892737,
]
Q = ZZ.prod(Q_PRIMES)


def kernel_basis():
    powers = [pow(B, j, Q) for j in range(LEVELS)]
    inv_last = ZZ(powers[-1]).inverse_mod(Q)
    basis = matrix(ZZ, LEVELS, LEVELS)
    for i in range(LEVELS - 1):
        basis[i, i] = 1
        basis[i, LEVELS - 1] = (-powers[i] * inv_last) % Q
    basis[LEVELS - 1, LEVELS - 1] = Q
    assert abs(basis.det()) == Q
    return basis, powers


def exact_counts(weights):
    """PMF counts for sum w_j*(Binomial(4,1/2)-2), exactly."""
    abs_weights = [abs(ZZ(w)) for w in weights]
    radius = 2 * sum(abs_weights)
    # The uncentered weighted Bernoulli sum has total weight 4*sum |w|.
    counts = [ZZ(1)]
    for weight in abs_weights:
        for _ in range(4):
            updated = [ZZ(0)] * (len(counts) + int(weight))
            for i, count in enumerate(counts):
                updated[i] += count
                updated[i + int(weight)] += count
            counts = updated
    assert len(counts) == 2 * int(radius) + 1
    total = ZZ(2) ** (4 * LEVELS)
    assert sum(counts) == total
    # Exact first two moments cross-check the coefficient law.
    mean_num = sum(ZZ(i - radius) * count for i, count in enumerate(counts))
    second_num = sum(ZZ(i - radius) ** 2 * count for i, count in enumerate(counts))
    assert mean_num == 0
    expected_variance = 2 * sum(ZZ(w) ** 2 for w in weights)
    assert second_num == total * expected_variance
    assert counts == list(reversed(counts)), "PMF must be symmetric"
    return counts, int(radius), total


def central_quantile(counts, radius, total, probability_num, probability_den):
    # Find smallest r with P(|E|<=r) >= probability_num/probability_den.
    cumulative = []
    running = ZZ(0)
    for count in counts:
        running += count
        cumulative.append(running)
    lo, hi = 0, radius
    while lo < hi:
        mid = (lo + hi) // 2
        left, right = radius - mid, radius + mid
        inside = cumulative[right] - (cumulative[left - 1] if left else 0)
        if inside * probability_den >= total * probability_num:
            hi = mid
        else:
            lo = mid + 1
    left, right = radius - lo, radius + lo
    inside = cumulative[right] - (cumulative[left - 1] if left else 0)
    return lo, float(inside / total)


def tail_probability(counts, radius, total, threshold):
    left = max(0, radius - threshold)
    right = min(len(counts) - 1, radius + threshold)
    inside = sum(counts[left:right + 1])
    return float((total - inside) / total)


def relation_holds(w, powers):
    return sum(ZZ(w[j]) * powers[j] for j in range(LEVELS)) % Q == 0


def pareto(rows):
    # Minimize L1 (worst-case support radius) and L2^2 (variance).
    out = []
    for row in rows:
        l1, l2, _, _ = row
        dominated = any(
            other[0] <= l1 and other[1] <= l2
            and (other[0] < l1 or other[1] < l2)
            for other in rows
        )
        if not dominated:
            out.append(row)
    return sorted(out, key=lambda x: (x[0], x[1]))


def report(label, row, powers):
    l1, l2, max_abs, w = row
    assert relation_holds(w, powers), "nonzero target remains"
    counts, radius, total = exact_counts(w)
    print(f"[{label}]")
    print(f"w={w}")
    print(f"L1={l1}; L2_squared={l2}; max_abs={max_abs}; exact_support_radius={radius}")
    for num, den, name in (
        (99, 100, "q99"),
        (999, 1000, "q999"),
        (9999, 10000, "q9999"),
        (999999, 1000000, "q999999"),
    ):
        q, mass = central_quantile(counts, radius, total, num, den)
        print(f"{name}={q}; achieved_mass={mass:.12f}")
    for threshold in (50000, 100000, 131074, 160000, 200000, 250000):
        print(f"Pr_abs_error_gt_{threshold}={tail_probability(counts, radius, total, threshold):.12g}")


def main():
    basis, powers = kernel_basis()
    reduced = basis.LLL(delta=0.99)
    rows = []
    for i in range(LEVELS):
        w = [ZZ(reduced[i, j]) for j in range(LEVELS)]
        if not any(w):
            continue
        assert relation_holds(w, powers)
        l1 = sum(abs(x) for x in w)
        l2 = sum(x*x for x in w)
        rows.append((int(l1), int(l2), int(max(abs(x) for x in w)), w))

    adjacent = [ZZ(0)] * LEVELS
    adjacent[0], adjacent[1] = -B, ZZ(1)
    baseline = (int(sum(abs(x) for x in adjacent)),
                int(sum(x*x for x in adjacent)),
                B, adjacent)

    frontier = pareto(rows + [baseline])
    print("Exact Pareto analysis of weighted eta=2 cancellation errors")
    print(f"N=8192; Q_bits={Q.nbits()}; B={B}; levels={LEVELS}; CBD_eta2")
    print("All w satisfy sum_j w_j*B^j = 0 (mod Q).")
    print("Variance is L2^2; exact support radius is 2*L1.")
    print("Pareto frontier is restricted to the adjacent baseline plus the displayed LLL basis rows.")
    print(f"LLL_basis_rows={len(rows)}; pareto_frontier_size={len(frontier)}")
    for rank, row in enumerate(frontier, 1):
        report(f"pareto_{rank}", row, powers)
    print("These are one-coefficient marginals; derived equations remain correlated.")
    print("No attack cost, secret recovery, or concrete security estimate is computed.")


if __name__ == "__main__":
    main()
