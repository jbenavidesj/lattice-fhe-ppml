#!/usr/bin/env python3
"""Exhaustive toy-ring comparison of original and transformed key equations.

This is a deliberately tiny, non-cryptographic experiment. It enumerates all
ternary secrets in R_q = Z_q[x]/(x^N+1), constructs synthetic evaluation-key
samples, and compares candidate sets obtained from:
  (i) the original equations with eta=2 error support [-2,2], and
  (ii) adjacent target-cancelled equations with exact worst-case support
       [-2(B+1),2(B+1)].

The transformed equations are deterministic consequences of the original
ones. The transformed candidate set must therefore contain the original
candidate set when these support tests are used. Counts illustrate information
lost by eliminating the shared s^2 target; they are not an attack or a
security estimate for the real parameter set.
"""
from itertools import product
from random import Random

B = 4
ETA = 2


def negacyclic_mul(a, b, q):
    n = len(a)
    out = [0] * n
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            k = i + j
            out[k if k < n else k - n] += x * y * (1 if k < n else -1)
    return [v % q for v in out]


def add(a, b, q):
    return [(x + y) % q for x, y in zip(a, b)]


def sub(a, b, q):
    return [(x - y) % q for x, y in zip(a, b)]


def scale(a, c, q):
    return [(c * x) % q for x in a]


def centered(x, q):
    x %= q
    return x - q if x > q // 2 else x


def sample_error(rng, n):
    # Exact centered-binomial eta=2: Binomial(4,1/2)-2.
    return [sum(rng.randrange(2) for _ in range(4)) - 2 for _ in range(n)]


def candidate_sets(seed, n, q, levels):
    rng = Random(seed)
    secret = [rng.choice((-1, 0, 1)) for _ in range(n)]
    secret_sq = negacyclic_mul(secret, secret, q)
    public_a, public_b = [], []

    for j in range(levels):
        a = [rng.randrange(q) for _ in range(n)]
        error = sample_error(rng, n)
        target = scale(secret_sq, pow(B, j, q), q)
        b = add(sub(target, negacyclic_mul(a, secret, q), q), error, q)
        public_a.append(a)
        public_b.append(b)

    original, transformed = [], []
    for values in product((-1, 0, 1), repeat=n):
        candidate = list(values)
        candidate_sq = negacyclic_mul(candidate, candidate, q)

        original_ok = True
        for j in range(levels):
            residual = sub(
                add(public_b[j], negacyclic_mul(public_a[j], candidate, q), q),
                scale(candidate_sq, pow(B, j, q), q),
                q,
            )
            if any(abs(centered(x, q)) > ETA for x in residual):
                original_ok = False
                break
        if original_ok:
            original.append(values)

        transformed_ok = True
        for j in range(levels - 1):
            a_delta = sub(public_a[j + 1], scale(public_a[j], B, q), q)
            b_delta = sub(public_b[j + 1], scale(public_b[j], B, q), q)
            residual = add(b_delta, negacyclic_mul(a_delta, candidate, q), q)
            if any(abs(centered(x, q)) > ETA * (B + 1) for x in residual):
                transformed_ok = False
                break
        if transformed_ok:
            transformed.append(values)

    secret_tuple = tuple(secret)
    assert secret_tuple in original
    assert secret_tuple in transformed
    assert set(original).issubset(set(transformed))
    return len(original), len(transformed)


def run_case(label, n, q, levels, trials):
    rows = [candidate_sets(seed, n, q, levels) for seed in range(trials)]
    original_counts = [x[0] for x in rows]
    transformed_counts = [x[1] for x in rows]
    extra = sum(t - o for o, t in rows)
    ambiguous = sum(t > o for o, t in rows)
    print(f"[{label}] N={n}; q={q}; B={B}; levels={levels}; trials={trials}")
    print(f"ternary_secret_space={3**n}")
    print(f"original_survivors_total={sum(original_counts)}")
    print(f"transformed_survivors_total={sum(transformed_counts)}")
    print(f"trials_with_extra_transformed_candidates={ambiguous}")
    print(f"extra_transformed_candidates_total={extra}")
    print(f"max_original_survivors={max(original_counts)}")
    print(f"max_transformed_survivors={max(transformed_counts)}")
    print("per_trial_counts=" + ",".join(f"{o}:{t}" for o, t in rows))


def main():
    print("Exhaustive ternary-secret candidate filtering in tiny negacyclic rings")
    print("Original support: [-2,2]; transformed support: [-10,10].")
    print("All counts are exact exhaustive counts; this is not a cryptographic benchmark.")
    run_case("small_ambiguity_stress", n=2, q=257, levels=2, trials=20)
    run_case("scaled_sanity", n=8, q=65537, levels=14, trials=10)


if __name__ == "__main__":
    main()
