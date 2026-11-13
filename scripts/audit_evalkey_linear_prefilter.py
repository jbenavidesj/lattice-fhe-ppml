#!/usr/bin/env python3
"""Audit safe linear prefilters obtained by cancelling adjacent eval-key levels.

The cancellation removes s^2:
  (b[j+1]-B*b[j]) + (a[j+1]-B*a[j])*s = e[j+1]-B*e[j].
The transformed error support is bounded by 2*eta*(1+B). This is a
small-parameter exhaustive diagnostic, not a practical attack or estimator.
"""
from itertools import product
import random
import statistics

Q = 31
BASE = 3
LEVELS = 3
ETA = 2
CANCEL_RADIUS = ETA * (1 + BASE)
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


def small(residual, radius):
    return all(abs(centered(x)) <= radius for x in residual)


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


def candidate_stage_counts(n, public_sample, eval_samples, secret):
    a_pk, b_pk = public_sample
    counts = [0] * (1 + (LEVELS - 1) + LEVELS)
    planted = [False] * len(counts)

    # Precompute the two linearized adjacent-level equations.
    linear_samples = []
    for j in range(LEVELS - 1):
        a0, b0 = eval_samples[j]
        a1, b1 = eval_samples[j + 1]
        a_diff = [(a1[i] - BASE * a0[i]) % Q for i in range(n)]
        b_diff = [(b1[i] - BASE * b0[i]) % Q for i in range(n)]
        linear_samples.append((a_diff, b_diff))

    for candidate in product((-1, 0, 1), repeat=n):
        a_s = negacyclic_mul(a_pk, candidate)
        public_residual = [(b_pk[i] + a_s[i]) % Q for i in range(n)]
        if not small(public_residual, ETA):
            continue
        counts[0] += 1
        if candidate == tuple(secret):
            planted[0] = True

        rejected = False
        for j, (a_diff, b_diff) in enumerate(linear_samples):
            residual = [
                (b_diff[i] + negacyclic_mul(a_diff, candidate)[i]) % Q
                for i in range(n)
            ]
            if not small(residual, CANCEL_RADIUS):
                rejected = True
                break
            counts[1 + j] += 1
            if candidate == tuple(secret):
                planted[1 + j] = True
        if rejected:
            continue

        square = negacyclic_mul(candidate, candidate)
        for j, (a_j, b_j) in enumerate(eval_samples):
            a_s = negacyclic_mul(a_j, candidate)
            factor = pow(BASE, j, Q)
            residual = [
                (b_j[i] + a_s[i] - factor * square[i]) % Q
                for i in range(n)
            ]
            if not small(residual, ETA):
                rejected = True
                break
            counts[1 + (LEVELS - 1) + j] += 1
            if candidate == tuple(secret):
                planted[1 + (LEVELS - 1) + j] = True

    assert all(planted), "planted secret must survive every safe filter"
    assert all(counts[i + 1] <= counts[i] for i in range(len(counts) - 1))
    return counts


def main():
    rng = random.Random(0xCA11CE1)
    print(
        f"Adjacent-level linear prefilter audit: q={Q}, B={BASE}, "
        f"eta={ETA}, cancellation radius={CANCEL_RADIUS}, trials={TRIALS}"
    )
    print("Stages: public, cancel(0,1), cancel(1,2), then eval levels 0,1,2.")
    for n in DEGREES:
        rows = []
        for _ in range(TRIALS):
            secret, public_sample, eval_samples = generate_instance(n, rng)
            rows.append(candidate_stage_counts(
                n, public_sample, eval_samples, secret
            ))
        medians = [statistics.median(row[i] for row in rows)
                   for i in range(len(rows[0]))]
        means = [statistics.mean(row[i] for row in rows)
                 for i in range(len(rows[0]))]
        uniques = [sum(row[i] == 1 for row in rows)
                   for i in range(len(rows[0]))]
        print(
            f"N={n}: median={medians}; "
            f"mean={[round(x, 3) for x in means]}; "
            f"unique={uniques}/{TRIALS}"
        )


if __name__ == "__main__":
    main()
