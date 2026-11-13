#!/usr/bin/env python3
"""Exact toy meet-in-the-middle join, cross-checked against exhaustive search.

This is a small-parameter algorithm experiment, not a production attack.
"""
from itertools import product
import random
import statistics
import time

Q = 11
BASE = 3
LEVELS = 3
ETA = 2
SELECTED_COORDINATES = 2
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


def candidate_matches(candidate, public_sample, eval_samples):
    a_pk, b_pk = public_sample
    a_times_candidate = negacyclic_mul(a_pk, candidate)
    public_residual = [
        (b_pk[i] + a_times_candidate[i]) % Q for i in range(len(candidate))
    ]
    if not residual_is_small(public_residual):
        return False

    candidate_square = negacyclic_mul(candidate, candidate)
    for level, (a_j, b_j) in enumerate(eval_samples):
        a_times_candidate = negacyclic_mul(a_j, candidate)
        factor = pow(BASE, level, Q)
        residual = [
            (b_j[i] + a_times_candidate[i] - factor * candidate_square[i]) % Q
            for i in range(len(candidate))
        ]
        if not residual_is_small(residual):
            return False
    return True


def generate_instance(n, rng):
    secret = [rng.choice((-1, 0, 1)) for _ in range(n)]
    a_pk = sample_poly(rng, n)
    e_pk = sample_error(rng, n)
    a_times_secret = negacyclic_mul(a_pk, secret)
    b_pk = [(e_pk[i] - a_times_secret[i]) % Q for i in range(n)]

    secret_square = negacyclic_mul(secret, secret)
    eval_samples = []
    for level in range(LEVELS):
        a_j = sample_poly(rng, n)
        e_j = sample_error(rng, n)
        a_times_secret = negacyclic_mul(a_j, secret)
        factor = pow(BASE, level, Q)
        b_j = [
            (factor * secret_square[i] + e_j[i] - a_times_secret[i]) % Q
            for i in range(n)
        ]
        eval_samples.append((a_j, b_j))
    return secret, (a_pk, b_pk), eval_samples


def exhaustive_candidates(n, public_sample, eval_samples):
    a_pk, b_pk = public_sample
    survivors = set()
    for candidate in product((-1, 0, 1), repeat=n):
        a_times_candidate = negacyclic_mul(a_pk, candidate)
        residual = [
            (b_pk[i] + a_times_candidate[i]) % Q for i in range(n)
        ]
        if residual_is_small(residual) and candidate_matches(
            candidate, public_sample, eval_samples
        ):
            survivors.add(candidate)
    return survivors


def mitm_candidates(n, public_sample, eval_samples, selected_coordinates=2):
    """Join two 3^(N/2) lists using a bounded-error hash on selected coordinates.

    For each left half, enumerate all 5^k centered error patterns on k selected
    coordinates, retrieve matching right-half buckets, then verify the full
    public residual and every evaluation-key equation.
    """
    if n % 2:
        raise ValueError("The toy MITM split requires an even degree.")
    if not 1 <= selected_coordinates <= n:
        raise ValueError("Invalid number of selected coordinates.")

    m = n // 2
    a_pk, b_pk = public_sample

    left_entries = []
    for left_half in product((-1, 0, 1), repeat=m):
        left_poly = tuple(left_half) + (0,) * m
        left_entries.append((tuple(left_half), negacyclic_mul(a_pk, left_poly)))

    right_buckets = {}
    for right_half in product((-1, 0, 1), repeat=m):
        right_poly = (0,) * m + tuple(right_half)
        contribution = negacyclic_mul(a_pk, right_poly)
        key = tuple(contribution[i] for i in range(selected_coordinates))
        right_buckets.setdefault(key, []).append((tuple(right_half), contribution))

    survivors = set()
    error_patterns = product(range(-ETA, ETA + 1), repeat=selected_coordinates)
    error_patterns = tuple(error_patterns)

    for left_half, left_contribution in left_entries:
        target = [
            (-b_pk[i] - left_contribution[i]) % Q
            for i in range(selected_coordinates)
        ]
        for error in error_patterns:
            key = tuple(
                (target[i] + error[i]) % Q
                for i in range(selected_coordinates)
            )
            for right_half, right_contribution in right_buckets.get(key, ()):
                candidate = left_half + right_half
                full_residual = [
                    (b_pk[i] + left_contribution[i] + right_contribution[i]) % Q
                    for i in range(n)
                ]
                if residual_is_small(full_residual) and candidate_matches(
                    candidate, public_sample, eval_samples
                ):
                    survivors.add(candidate)
    return survivors


def main():
    rng = random.Random(0xBF2)
    print(
        f"Toy MITM: q={Q}, B={BASE}, levels={LEVELS}, eta=2, "
        f"selected_coordinates={SELECTED_COORDINATES}, trials={TRIALS}"
    )
    for n in DEGREES:
        exhaustive_times = []
        mitm_times = []
        for _ in range(TRIALS):
            secret, public_sample, eval_samples = generate_instance(n, rng)

            start = time.perf_counter()
            exhaustive = exhaustive_candidates(n, public_sample, eval_samples)
            exhaustive_times.append(time.perf_counter() - start)

            start = time.perf_counter()
            mitm = mitm_candidates(
                n, public_sample, eval_samples, SELECTED_COORDINATES
            )
            mitm_times.append(time.perf_counter() - start)

            assert exhaustive == mitm, (
                n, exhaustive, mitm, exhaustive - mitm, mitm - exhaustive
            )
            assert tuple(secret) in mitm

        exhaustive_median = statistics.median(exhaustive_times)
        mitm_median = statistics.median(mitm_times)
        speedup = exhaustive_median / mitm_median if mitm_median else float("inf")
        print(
            f"N={n}: exact-set agreement={TRIALS}/{TRIALS}; "
            f"median exhaustive={exhaustive_median:.6f}s; "
            f"median MITM={mitm_median:.6f}s; "
            f"observed speed ratio={speedup:.2f}x"
        )


if __name__ == "__main__":
    main()
