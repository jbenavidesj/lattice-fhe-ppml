#!/usr/bin/env python3
"""Exact toy-ring comparison of original and jointly transformed constraints.

Compares two ways to test a candidate secret against one synthetic transcript:
 A. all original evaluation-key residuals lie in the eta=2 support;
 B. public-key residual and level-0 error are checked, then the exact shared
    error recurrence e[j+1] = z[j] + B*e[j] is propagated through all
    adjacent transformed equations.

The recurrence preserves the joint support. It does not replace it with a
coordinatewise wide box. This is a tiny exhaustive consistency experiment,
not an attack or production-parameter complexity estimate.
"""
from itertools import product
from random import Random

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
    return [sum(rng.randrange(2) for _ in range(4)) - 2 for _ in range(n)]


def residual(b, a, secret, target, q):
    v = sub(add(b, negacyclic_mul(a, secret, q), q), target, q)
    return [centered(x, q) for x in v]


def exact_joint_support_from_differences(first_error, z_columns, B, q):
    current = list(first_error)
    if any(abs(x) > ETA for x in current):
        return False
    for z in z_columns:
        nxt = [centered(z_i + B * e_i, q) for z_i, e_i in zip(z, current)]
        if any(abs(x) > ETA for x in nxt):
            return False
        current = nxt
    return True


def one_instance(seed, n, q, B, levels):
    rng = Random(seed)
    secret = [rng.choice((-1, 0, 1)) for _ in range(n)]
    secret_sq = negacyclic_mul(secret, secret, q)
    apk = [rng.randrange(q) for _ in range(n)]
    epk = sample_error(rng, n)
    bpk = sub(epk, negacyclic_mul(apk, secret, q), q)

    aa, bb = [], []
    for j in range(levels):
        a = [rng.randrange(q) for _ in range(n)]
        e = sample_error(rng, n)
        target = scale(secret_sq, pow(B, j, q), q)
        b = add(sub(target, negacyclic_mul(a, secret, q), q), e, q)
        aa.append(a)
        bb.append(b)

    original, combined, coarse = set(), set(), set()
    coarse_radius = ETA * (B + 1)
    assert 2 * coarse_radius < q, "toy modulus must avoid centered-wrap ambiguity"

    for values in product((-1, 0, 1), repeat=n):
        cand = list(values)
        cand_sq = negacyclic_mul(cand, cand, q)
        pub_err = residual(bpk, apk, cand, [0] * n, q)
        if any(abs(x) > ETA for x in pub_err):
            continue

        eval_res = [
            residual(bb[j], aa[j], cand, scale(cand_sq, pow(B, j, q), q), q)
            for j in range(levels)
        ]
        if all(all(abs(x) <= ETA for x in r) for r in eval_res):
            original.add(values)

        z_cols = [
            [centered(eval_res[j + 1][k] - B * eval_res[j][k], q)
             for k in range(n)]
            for j in range(levels - 1)
        ]
        if (all(abs(x) <= coarse_radius for z in z_cols for x in z)
                and all(abs(x) <= ETA for x in eval_res[0])):
            coarse.add(values)

        if exact_joint_support_from_differences(eval_res[0], z_cols, B, q):
            combined.add(values)

    assert tuple(secret) in original
    assert tuple(secret) in combined
    assert original == combined, (seed, sorted(original), sorted(combined))
    assert original.issubset(coarse)
    return len(original), len(combined), len(coarse)


def run_case(label, n, q, B, levels, trials):
    rows = [one_instance(seed, n, q, B, levels) for seed in range(trials)]
    print(f"[{label}] N={n}; q={q}; B={B}; levels={levels}; trials={trials}")
    print(f"secret_space={3**n}")
    print(f"mean_original_survivors={sum(r[0] for r in rows)/trials:.4f}")
    print(f"mean_exact_joint_survivors={sum(r[1] for r in rows)/trials:.4f}")
    print(f"mean_coarse_transformed_survivors={sum(r[2] for r in rows)/trials:.4f}")
    print(f"original_equals_exact_joint_all_trials={all(a == b for a, b, _ in rows)}")
    print(f"coarse_extra_candidates_total={sum(c-a for a, _, c in rows)}")
    print("per_trial_original:exact_joint:coarse=" +
          ",".join(f"{a}:{b}:{c}" for a, b, c in rows))


def main():
    print("Exact joint original/transformed candidate-filter equivalence")
    print("eta=2 PMF numerator on [-2,-1,0,1,2] is [1,4,6,4,1], denominator 16")
    print("The exact transformed test pins e_0 and uses e[j+1]=z[j]+B*e[j].")
    print("It is deterministic post-processing, not extra information or an attack.")
    run_case("small_ring", n=2, q=23, B=4, levels=2, trials=40)
    run_case("medium_toy", n=5, q=65537, B=16, levels=6, trials=10)


if __name__ == "__main__":
    main()
