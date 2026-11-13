#!/usr/bin/env python3
"""Exhaustive toy audit of original + transformed evaluation-key constraints.

Enumerate every coefficientwise ternary secret in tiny negacyclic rings.
Compare the original evaluation-key residual tests, adjacent target-cancelled
necessary tests, and their intersection, both alone and jointly with one
public-key sample. This is a correctness/logic audit, not an attack or a
production-parameter security estimate.
"""
from itertools import product
from random import Random

ETA = 2
B = 4


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
    # Difference of two Binomial(2, 1/2) variables.
    return [sum(rng.randrange(2) for _ in range(4)) - 2 for _ in range(n)]


def one_trial(seed, n, q, levels):
    assert q > 2 * ETA * (B + 1), "transformed support must fit centered interval"
    rng = Random(seed)
    secret = [rng.choice((-1, 0, 1)) for _ in range(n)]
    secret_sq = negacyclic_mul(secret, secret, q)

    a_pk = [rng.randrange(q) for _ in range(n)]
    e_pk = sample_error(rng, n)
    b_pk = add(scale(negacyclic_mul(a_pk, secret, q), -1, q), e_pk, q)

    a_levels, b_levels = [], []
    for j in range(levels):
        a = [rng.randrange(q) for _ in range(n)]
        e = sample_error(rng, n)
        target = scale(secret_sq, pow(B, j, q), q)
        b = add(sub(target, negacyclic_mul(a, secret, q), q), e, q)
        a_levels.append(a)
        b_levels.append(b)

    pk_only, original_only, transformed_only, combined_only = set(), set(), set(), set()
    pk_original, pk_transformed, pk_combined = set(), set(), set()

    for values in product((-1, 0, 1), repeat=n):
        candidate = list(values)
        candidate_sq = negacyclic_mul(candidate, candidate, q)

        pk_residual = add(b_pk, negacyclic_mul(a_pk, candidate, q), q)
        pk_ok = all(abs(centered(x, q)) <= ETA for x in pk_residual)
        if pk_ok:
            pk_only.add(values)

        original_ok = True
        for j in range(levels):
            residual = sub(
                add(b_levels[j], negacyclic_mul(a_levels[j], candidate, q), q),
                scale(candidate_sq, pow(B, j, q), q), q,
            )
            if any(abs(centered(x, q)) > ETA for x in residual):
                original_ok = False
                break
        if original_ok:
            original_only.add(values)
        if pk_ok and original_ok:
            pk_original.add(values)

        transformed_ok = True
        for j in range(levels - 1):
            a_delta = sub(a_levels[j + 1], scale(a_levels[j], B, q), q)
            b_delta = sub(b_levels[j + 1], scale(b_levels[j], B, q), q)
            residual = add(b_delta, negacyclic_mul(a_delta, candidate, q), q)
            if any(abs(centered(x, q)) > ETA * (B + 1) for x in residual):
                transformed_ok = False
                break
        if transformed_ok:
            transformed_only.add(values)
        if pk_ok and transformed_ok:
            pk_transformed.add(values)

        both = original_ok and transformed_ok
        if both:
            combined_only.add(values)
        if pk_ok and both:
            pk_combined.add(values)

    planted = tuple(secret)
    assert planted in pk_only and planted in original_only and planted in transformed_only
    assert planted in combined_only and planted in pk_original and planted in pk_transformed and planted in pk_combined
    # The transformed equations are exact consequences with the derived
    # support bound, so intersecting them with all originals is redundant.
    assert combined_only == original_only
    assert pk_combined == pk_original
    assert original_only.issubset(transformed_only)
    assert pk_original.issubset(pk_transformed)
    return tuple(map(len, (pk_only, original_only, transformed_only, combined_only,
                           pk_original, pk_transformed, pk_combined)))


def run_case(label, n, q, levels, trials):
    rows = [one_trial(seed, n, q, levels) for seed in range(trials)]
    names = ("public_only", "eval_original_only", "eval_transformed_only",
             "eval_original_intersection_transformed", "joint_pk_plus_original",
             "joint_pk_plus_transformed", "joint_pk_plus_both")
    print(f"[{label}] N={n}; q={q}; B={B}; eta={ETA}; levels={levels}; trials={trials}")
    print(f"ternary_secret_space={3**n}; transformed_support_radius={ETA*(B+1)}")
    for index, name in enumerate(names):
        vals = [row[index] for row in rows]
        print(f"{name}: total={sum(vals)}; max={max(vals)}; unique_trials={sum(v == 1 for v in vals)}/{trials}")
    print("per_trial(eval_original:eval_transformed:eval_intersection:joint_original:joint_transformed:joint_both)=")
    print(",".join(":".join(str(x) for x in (r[1], r[2], r[3], r[4], r[5], r[6])) for r in rows))


def main():
    print("Joint original/transformed evaluation-key constraint audit")
    print("Exact exhaustive ternary enumeration; centered modular residual tests.")
    print("The transformed test is necessary with radius eta*(B+1), not an independent source of information.")
    run_case("small_ambiguity_stress", n=2, q=257, levels=2, trials=20)
    run_case("larger_toy_ring", n=8, q=65537, levels=14, trials=10)


if __name__ == "__main__":
    main()
