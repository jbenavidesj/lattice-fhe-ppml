#!/usr/bin/env python3
"""Toy exhaustive-search experiment for ternary secrets in a negacyclic ring.

This is an educational structural experiment, not a security estimator:
small N, a single public-key sample, and a few evaluation-key levels.
"""
from itertools import product
import random
import statistics

Q = 11
BASE = 3
LEVELS = 3
ETA = 2


def centered(x, q=Q):
    x %= q
    return x - q if x > q // 2 else x


def add(a, b):
    return [(x + y) % Q for x, y in zip(a, b)]


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
    # Difference of two independent Binomial(2, 1/2) variables.
    return (rng.getrandbits(1) + rng.getrandbits(1)) - (rng.getrandbits(1) + rng.getrandbits(1))


def sample_poly(rng, n):
    return [rng.randrange(Q) for _ in range(n)]


def sample_error(rng, n):
    return [cbd_eta2(rng) for _ in range(n)]


def residual_is_small(residual):
    return all(abs(centered(x)) <= ETA for x in residual)


def candidate_matches(candidate, public_sample, eval_samples):
    a_pk, b_pk = public_sample
    t = candidate
    public_residual = [(b_pk[i] + negacyclic_mul(a_pk, t)[i]) % Q
                       for i in range(len(t))]
    if not residual_is_small(public_residual):
        return False

    t_square = negacyclic_mul(t, t)
    for level, (a_j, b_j) in enumerate(eval_samples):
        a_t = negacyclic_mul(a_j, t)
        factor = pow(BASE, level, Q)
        residual = [(b_j[i] + a_t[i] - factor * t_square[i]) % Q
                    for i in range(len(t))]
        if not residual_is_small(residual):
            return False
    return True


def run_trial(n, rng):
    secret = [rng.choice((-1, 0, 1)) for _ in range(n)]
    a_pk = sample_poly(rng, n)
    e_pk = sample_error(rng, n)
    a_times_s = negacyclic_mul(a_pk, secret)
    b_pk = [(e_pk[i] - a_times_s[i]) % Q for i in range(n)]

    secret_square = negacyclic_mul(secret, secret)
    eval_samples = []
    for level in range(LEVELS):
        a_j = sample_poly(rng, n)
        e_j = sample_error(rng, n)
        a_s = negacyclic_mul(a_j, secret)
        factor = pow(BASE, level, Q)
        b_j = [(factor * secret_square[i] + e_j[i] - a_s[i]) % Q
               for i in range(n)]
        eval_samples.append((a_j, b_j))

    public_only = 0
    with_eval = 0
    for candidate in product((-1, 0, 1), repeat=n):
        a_t = negacyclic_mul(a_pk, candidate)
        pub_res = [(b_pk[i] + a_t[i]) % Q for i in range(n)]
        matches_public = residual_is_small(pub_res)
        if matches_public:
            public_only += 1
            if candidate_matches(candidate, (a_pk, b_pk), eval_samples):
                with_eval += 1

    # The planted secret must always remain consistent.
    assert candidate_matches(secret, (a_pk, b_pk), eval_samples)
    assert with_eval <= public_only
    return public_only, with_eval


def main():
    rng = random.Random(0xB_F2)
    trials = 30
    print(f"Toy exhaustive search: q={Q}, B={BASE}, levels={LEVELS}, eta=2")
    for n in (4, 6, 8):
        results = [run_trial(n, rng) for _ in range(trials)]
        public_counts = [x[0] for x in results]
        eval_counts = [x[1] for x in results]
        print(
            f"N={n}: trials={trials}; "
            f"public-only median={statistics.median(public_counts):g}, "
            f"with-eval median={statistics.median(eval_counts):g}, "
            f"public-only unique={sum(x == 1 for x in public_counts)}/{trials}, "
            f"with-eval unique={sum(x == 1 for x in eval_counts)}/{trials}"
        )


if __name__ == "__main__":
    main()
