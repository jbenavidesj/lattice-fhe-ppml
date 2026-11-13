#!/usr/bin/env python3
"""Exact coefficient-error PMF for selected evaluation-key cancellation vectors.

For eta=2, X has masses (1,4,6,4,1)/16 on {-2,-1,0,1,2},
equivalently X = Binomial(4,1/2)-2. Thus sum_j w_j X_j can be
computed exactly by integer dynamic programming over 4*len(w) Bernoulli
variables. This is a one-coefficient marginal; it does not model dependencies
across derived equations or constitute an attack/security estimate.
"""
from math import isclose

B = 1 << 16
LEVELS = 14
Q_PRIMES = [
    36028797002170369,
    36028796951838721,
    18014398508400641,
    18014398507892737,
]
Q = 1
for prime in Q_PRIMES:
    Q *= prime

# Rank-6 vector from the recorded exact-integer LLL run: lowest L2^2 among
# the 14 displayed reduced basis rows.
LOW_VARIANCE_VECTOR = [
    16395, -2246, 11538, -2352, -15966, -4494, 13649,
    15421, 21740, -8852, 532, 11216, -2, 11264,
]


def modular_relation(weights):
    return sum(int(w) * pow(B, j, Q) for j, w in enumerate(weights)) % Q == 0


def exact_centered_pmf(weights):
    """Return exact integer counts indexed by uncentered weighted Bernoulli sum."""
    expanded = [abs(int(w)) for w in weights for _ in range(4)]
    counts = [1]
    for weight in expanded:
        updated = [0] * (len(counts) + weight)
        for index, count in enumerate(counts):
            updated[index] += count
            updated[index + weight] += count
        counts = updated
    total = sum(counts)
    assert total == 1 << len(expanded)
    radius = 2 * sum(abs(int(w)) for w in weights)
    assert len(counts) == 2 * radius + 1
    return counts, radius, total


def central_quantile(counts, radius, total, probability):
    cumulative = []
    running = 0
    for count in counts:
        running += count
        cumulative.append(running)
    lo, hi = 0, radius
    while lo < hi:
        mid = (lo + hi) // 2
        left = radius - mid
        right = radius + mid
        inside = cumulative[right] - (cumulative[left - 1] if left else 0)
        if inside / total >= probability:
            hi = mid
        else:
            lo = mid + 1
    left, right = radius - lo, radius + lo
    inside = cumulative[right] - (cumulative[left - 1] if left else 0)
    return lo, inside / total


def tail_probability(counts, radius, total, threshold):
    left = max(0, radius - threshold)
    right = min(len(counts) - 1, radius + threshold)
    inside = sum(counts[left:right + 1])
    return (total - inside) / total


def report(label, weights):
    assert len(weights) == LEVELS
    assert modular_relation(weights), f"{label}: target does not cancel modulo Q"
    counts, radius, total = exact_centered_pmf(weights)
    l1 = sum(abs(w) for w in weights)
    l2_sq = sum(w * w for w in weights)
    assert l2_sq == sum((w * w) for w in weights)
    print(f"[{label}]")
    print(f"L1={l1}; L2_squared={l2_sq}; variance={l2_sq}; exact_support_radius={radius}")
    print(f"exact_integer_outcomes={total}; pmf_length={len(counts)}")
    for p in (0.99, 0.999, 0.9999):
        q, mass = central_quantile(counts, radius, total, p)
        print(f"central_quantile_{p}={q}; achieved_mass={mass:.12f}")
    for threshold in (50000, 100000, 131074, 160000):
        print(f"Pr_abs_error_gt_{threshold}={tail_probability(counts, radius, total, threshold):.12g}")


def main():
    adjacent = [0] * LEVELS
    adjacent[0], adjacent[1] = -B, 1
    assert modular_relation(adjacent)
    print("Exact weighted eta=2 one-coefficient error distributions")
    print("Each eta=2 variable is represented exactly as Binomial(4,1/2)-2.")
    print("Counts are integer-exact; probabilities are ratios of integer counts.")
    print("The PMF is a marginal for one polynomial coefficient, not a full transcript model.")
    report("adjacent_baseline", adjacent)
    report("lowest_L2_squared_LLL_row", LOW_VARIANCE_VECTOR)


if __name__ == "__main__":
    main()
