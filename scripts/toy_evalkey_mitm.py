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
SELECTED_COORDINATES = (1, 2, 3, 4)
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


def residual_product_is_small(a, candidate, offset, square=None, factor=0):
    """Check b + a*c - factor*c^2 coefficientwise, stopping at first failure.

    The caller supplies offset=b. If square is None, this checks b+a*c.
    Returns (accepted, number_of_coefficients_examined).
    """
    n = len(candidate)
    checked = 0
    for k in range(n):
        product_coefficient = sum(
            a[i] * candidate[k - i] for i in range(k + 1)
        ) - sum(
            a[i] * candidate[k - i + n] for i in range(k + 1, n)
        )
        value = offset[k] + product_coefficient
        if square is not None:
            value -= factor * square[k]
        checked += 1
        if abs(centered(value)) > ETA:
            return False, checked
    return True, checked



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


def mitm_candidates(n, public_sample, eval_samples, selected_coordinates=2, stats=None):
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
    if stats is not None:
        stats.clear()
        stats.update({
            "joined_pairs": 0,
            "public_full_pass": 0,
            "eval_level_checks": [0] * len(eval_samples),
            "eval_level_rejects": [0] * len(eval_samples),
            "survivors": 0,
            "public_coeff_checks": 0,
            "eval_coeff_checks": [0] * len(eval_samples),
        })
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
                if stats is not None:
                    stats["joined_pairs"] += 1
                candidate = left_half + right_half
                public_ok, public_checked = residual_product_is_small(
                    a_pk, candidate, b_pk
                )
                if stats is not None:
                    stats["public_coeff_checks"] += public_checked
                if not public_ok:
                    continue
                if stats is not None:
                    stats["public_full_pass"] += 1

                # Apply evaluation-key constraints in sequence. The first
                # failing level rejects the pair before later ring products.
                candidate_square = negacyclic_mul(candidate, candidate)
                accepted = True
                for level, (a_j, b_j) in enumerate(eval_samples):
                    if stats is not None:
                        stats["eval_level_checks"][level] += 1
                    factor = pow(BASE, level, Q)
                    level_ok, coeffs_checked = residual_product_is_small(
                        a_j, candidate, b_j, candidate_square, factor
                    )
                    if stats is not None:
                        stats["eval_coeff_checks"][level] += coeffs_checked
                    if not level_ok:
                        if stats is not None:
                            stats["eval_level_rejects"][level] += 1
                        accepted = False
                        break
                if accepted:
                    survivors.add(candidate)
                    if stats is not None:
                        stats["survivors"] += 1
    return survivors


def main():
    rng = random.Random(0xBF2)
    print(
        f"Toy MITM coordinate sweep: q={Q}, B={BASE}, levels={LEVELS}, "
        f"eta={ETA}, coordinates={SELECTED_COORDINATES}, trials={TRIALS}"
    )
    for n in DEGREES:
        exhaustive_times = []
        results = {
            k: {"times": [], "stats": []}
            for k in SELECTED_COORDINATES if k <= n
        }
        for _ in range(TRIALS):
            secret, public_sample, eval_samples = generate_instance(n, rng)

            start = time.perf_counter()
            exhaustive = exhaustive_candidates(n, public_sample, eval_samples)
            exhaustive_times.append(time.perf_counter() - start)

            for k, result in results.items():
                start = time.perf_counter()
                stats = {}
                mitm = mitm_candidates(n, public_sample, eval_samples, k, stats)
                result["times"].append(time.perf_counter() - start)
                result["stats"].append(stats)
                assert exhaustive == mitm, (
                    n, k, exhaustive, mitm,
                    exhaustive - mitm, mitm - exhaustive
                )
                assert tuple(secret) in mitm

        exhaustive_median = statistics.median(exhaustive_times)
        print(
            f"N={n}: exhaustive median={exhaustive_median:.6f}s; "
            f"exact-set agreement={TRIALS}/{TRIALS} for every k"
        )
        for k, result in results.items():
            mitm_median = statistics.median(result["times"])
            speedup = (
                exhaustive_median / mitm_median
                if mitm_median else float("inf")
            )
            trial_stats = result["stats"]

            def median(key):
                return statistics.median([item[key] for item in trial_stats])

            median_level_checks = [
                statistics.median(
                    [item["eval_level_checks"][level] for item in trial_stats]
                )
                for level in range(LEVELS)
            ]
            median_level_rejects = [
                statistics.median(
                    [item["eval_level_rejects"][level] for item in trial_stats]
                )
                for level in range(LEVELS)
            ]
            median_eval_coeff_checks = [
                statistics.median(
                    [item["eval_coeff_checks"][level] for item in trial_stats]
                )
                for level in range(LEVELS)
            ]
            print(
                f"  k={k}: probes/left={5**k}; MITM median={mitm_median:.6f}s; "
                f"ratio={speedup:.2f}x; joined={median('joined_pairs'):g}; "
                f"public-pass={median('public_full_pass'):g}; "
                f"survivors={median('survivors'):g}"
            )
            print(
                f"    eval checks={median_level_checks}; "
                f"eval rejects={median_level_rejects}; "
                f"eval coefficient checks={median_eval_coeff_checks}; "
                f"public coefficient checks={median('public_coeff_checks'):g}"
            )


if __name__ == "__main__":
    main()
