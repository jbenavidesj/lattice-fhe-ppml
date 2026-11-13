#!/usr/bin/env python3
"""Measure toy candidate filtering from the public key and successive eval-key levels.

This is an exhaustive, small-parameter diagnostic only. It is not a practical
key-recovery attack, a security estimator, or evidence about N=8192 hardness.
"""
from itertools import product
import random
import statistics

Q = 11
BASE = 3
LEVELS = 3
ETA = 2
TRIALS = 30
DEGREES = (4, 6, 8)


def centered(x):
    x %= Q
    return x - Q if x > Q // 2 else x


def negacyclic_mul(a, b):
    n = len(a)
    out = [0] * n
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            k = i + j
            sign = 1
            if k >= n:
                k -= n
                sign = -1
            out[k] = (out[k] + sign * x * y) % Q
    return out


def cbd_eta2(rng):
    return (rng.getrandbits(1) + rng.getrandbits(1)) - (
        rng.getrandbits(1) + rng.getrandbits(1)
    )


def sample_poly(rng, n):
    return [rng.randrange(Q) for _ in range(n)]


def sample_error(rng, n):
    return [cbd_eta2(rng) for _ in range(n)]


def residual_is_small(residual):
    return all(abs(centered(x)) <= ETA for x in residual)


def generate_instance(n, rng):
    secret = [rng.choice((-1, 0, 1)) for _ in range(n)]
    a_pk = sample_poly(rng, n)
    e_pk = sample_error(rng, n)
    a_s = negacyclic_mul(a_pk, secret)
    b_pk = [(e_pk[i] - a_s[i]) % Q for i in range(n)]

    square = negacyclic_mul(secret, secret)
    eval_samples = []
    for level in range(LEVELS):
        a_j = sample_poly(rng, n)
        e_j = sample_error(rng, n)
        a_s = negacyclic_mul(a_j, secret)
        factor = pow(BASE, level, Q)
        b_j = [
            (factor * square[i] + e_j[i] - a_s[i]) % Q
            for i in range(n)
        ]
        eval_samples.append((a_j, b_j))
    return secret, (a_pk, b_pk), eval_samples


def count_survivors(n, public_sample, eval_samples, secret):
    a_pk, b_pk = public_sample
    counts = [0] * (LEVELS + 1)
    planted_survival = [False] * (LEVELS + 1)

    for candidate in product((-1, 0, 1), repeat=n):
        a_t = negacyclic_mul(a_pk, candidate)
        public_residual = [
            (b_pk[i] + a_t[i]) % Q for i in range(n)
        ]
        if not residual_is_small(public_residual):
            continue

        counts[0] += 1
        if candidate == tuple(secret):
            planted_survival[0] = True

        square = negacyclic_mul(candidate, candidate)
        accepted = True
        for level, (a_j, b_j) in enumerate(eval_samples):
            a_t = negacyclic_mul(a_j, candidate)
            factor = pow(BASE, level, Q)
            residual = [
                (b_j[i] + a_t[i] - factor * square[i]) % Q
                for i in range(n)
            ]
            if not residual_is_small(residual):
                accepted = False
                break
            counts[level + 1] += 1
            if candidate == tuple(secret):
                planted_survival[level + 1] = True

    assert all(planted_survival), "the planted secret was rejected"
    assert all(counts[i + 1] <= counts[i] for i in range(LEVELS))
    return counts


def main():
    rng = random.Random(0xE7A1_2026)
    print(
        f"Toy eval-key filtering: q={Q}, B={BASE}, levels={LEVELS}, "
        f"eta={ETA}, trials={TRIALS}"
    )
    print("Counts are candidate secrets surviving the public equation, then")
    print("each successive evaluation-key level; planted secret always survives.")
    for n in DEGREES:
        # Generate each instance once and retain its planted secret.
        rows = []
        for _ in range(TRIALS):
            secret, public_sample, eval_samples = generate_instance(n, rng)
            rows.append(count_survivors(n, public_sample, eval_samples, secret))

        medians = [statistics.median(row[i] for row in rows)
                   for i in range(LEVELS + 1)]
        uniques = [sum(row[i] == 1 for row in rows)
                   for i in range(LEVELS + 1)]
        means = [statistics.mean(row[i] for row in rows)
                 for i in range(LEVELS + 1)]
        print(
            f"N={n}: median survivors={medians}; "
            f"mean survivors={[round(x, 3) for x in means]}; "
            f"unique trials={uniques}/{TRIALS}"
        )


if __name__ == "__main__":
    main()
