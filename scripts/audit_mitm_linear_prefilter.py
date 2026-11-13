#!/usr/bin/env python3
"""Measure adjacent-level linear prefilters inside the toy MITM candidate pipeline.

The filters are evaluated only after a pair has joined and passed the complete
public-key equation. They cannot reduce MITM list sizes or joined-pair counts.
This audit measures whether they reduce later square/evaluation work enough to
justify their own polynomial products. Toy parameters only; not an attack.
"""
from itertools import product
import random
import statistics
import time

import toy_evalkey_mitm as mitm

Q = 29
ETA = 3
BASE = 3
LEVELS = 3
TRIALS = 10
DEGREES = (4, 6, 8)
SELECTED_COORDINATES = 2
LINEAR_RADIUS = ETA * (1 + BASE)


def small_with_radius(residual, radius):
    return all(abs(mitm.centered(x)) <= radius for x in residual)


def linear_prefilter(candidate, eval_samples, linear_samples):
    for a_diff, b_diff in linear_samples:
        product = mitm.negacyclic_mul(a_diff, candidate)
        residual = [(b_diff[i] + product[i]) % Q
                    for i in range(len(candidate))]
        if not small_with_radius(residual, LINEAR_RADIUS):
            return False
    return True


def mitm_with_linear_prefilter(n, public_sample, eval_samples, k, stats):
    """MITM public join, then linear filters, then square/eval verification."""
    m = n // 2
    a_pk, b_pk = public_sample

    left_entries = []
    for left_half in product((-1, 0, 1), repeat=m):
        left_poly = tuple(left_half) + (0,) * m
        left_entries.append((tuple(left_half),
                             mitm.negacyclic_mul(a_pk, left_poly)))

    right_buckets = {}
    for right_half in product((-1, 0, 1), repeat=m):
        right_poly = (0,) * m + tuple(right_half)
        contribution = mitm.negacyclic_mul(a_pk, right_poly)
        key = tuple(contribution[i] for i in range(k))
        right_buckets.setdefault(key, []).append((tuple(right_half), contribution))

    linear_samples = []
    for j in range(LEVELS - 1):
        a0, b0 = eval_samples[j]
        a1, b1 = eval_samples[j + 1]
        linear_samples.append((
            [(a1[i] - BASE * a0[i]) % Q for i in range(n)],
            [(b1[i] - BASE * b0[i]) % Q for i in range(n)],
        ))

    error_patterns = tuple(product(range(-ETA, ETA + 1), repeat=k))
    survivors = set()
    stats.clear()
    stats.update({
        "joined_pairs": 0,
        "public_pass": 0,
        "linear_candidates": 0,
        "linear_rejects": 0,
        "linear_ring_products": 0,
        "square_computations": 0,
        "eval_ring_products": 0,
        "eval_rejects": [0] * LEVELS,
    })

    for left_half, left_contribution in left_entries:
        target = [(-b_pk[i] - left_contribution[i]) % Q for i in range(k)]
        for error in error_patterns:
            key = tuple((target[i] + error[i]) % Q for i in range(k))
            for right_half, _right_contribution in right_buckets.get(key, ()):
                stats["joined_pairs"] += 1
                candidate = left_half + right_half
                public_ok, _ = mitm.residual_product_is_small(
                    a_pk, candidate, b_pk
                )
                if not public_ok:
                    continue
                stats["public_pass"] += 1
                stats["linear_candidates"] += 1
                stats["linear_ring_products"] += len(linear_samples)
                if not linear_prefilter(candidate, eval_samples, linear_samples):
                    stats["linear_rejects"] += 1
                    continue

                stats["square_computations"] += 1
                square = mitm.negacyclic_mul(candidate, candidate)
                accepted = True
                for level, (a_j, b_j) in enumerate(eval_samples):
                    stats["eval_ring_products"] += 1
                    factor = pow(BASE, level, Q)
                    level_ok, _ = mitm.residual_product_is_small(
                        a_j, candidate, b_j, square, factor
                    )
                    if not level_ok:
                        stats["eval_rejects"][level] += 1
                        accepted = False
                        break
                if accepted:
                    survivors.add(candidate)
    return survivors


def generate_stress_instance(n, rng):
    """Generate a true eta=3 instance (the legacy MITM helper is eta=2)."""
    secret = [rng.choice((-1, 0, 1)) for _ in range(n)]
    a_pk = [rng.randrange(Q) for _ in range(n)]
    error = [sum(rng.getrandbits(1) for _ in range(ETA))
             - sum(rng.getrandbits(1) for _ in range(ETA)) for _ in range(n)]
    a_secret = mitm.negacyclic_mul(a_pk, secret)
    b_pk = [(error[i] - a_secret[i]) % Q for i in range(n)]
    square = mitm.negacyclic_mul(secret, secret)
    eval_samples = []
    for level in range(LEVELS):
        a_j = [rng.randrange(Q) for _ in range(n)]
        e_j = [sum(rng.getrandbits(1) for _ in range(ETA))
               - sum(rng.getrandbits(1) for _ in range(ETA)) for _ in range(n)]
        a_s = mitm.negacyclic_mul(a_j, secret)
        factor = pow(BASE, level, Q)
        b_j = [(factor * square[i] + e_j[i] - a_s[i]) % Q
               for i in range(n)]
        eval_samples.append((a_j, b_j))
    return secret, (a_pk, b_pk), eval_samples


def main():
    # The imported prototype uses module globals; override them explicitly so
    # all baseline and exhaustive routines share the declared stress instance.
    mitm.Q = Q
    mitm.ETA = ETA
    mitm.BASE = BASE
    mitm.LEVELS = LEVELS

    rng = random.Random(0x11EA_2026)
    print(
        f"MITM linear-prefilter audit: q={Q}, eta={ETA}, B={BASE}, "
        f"levels={LEVELS}, radius={LINEAR_RADIUS}, trials={TRIALS}"
    )
    print("Filters run after public join; no claim of fewer joined pairs/list entries.")
    for n in DEGREES:
        rows = []
        baseline_times = []
        filtered_times = []
        for _ in range(TRIALS):
            secret, public_sample, eval_samples = generate_stress_instance(n, rng)
            expected = mitm.exhaustive_candidates(n, public_sample, eval_samples)
            baseline_stats = {}
            start = time.perf_counter()
            baseline = mitm.mitm_candidates(
                n, public_sample, eval_samples, SELECTED_COORDINATES,
                baseline_stats
            )
            baseline_times.append(time.perf_counter() - start)
            filtered_stats = {}
            start = time.perf_counter()
            filtered = mitm_with_linear_prefilter(
                n, public_sample, eval_samples, SELECTED_COORDINATES,
                filtered_stats
            )
            filtered_times.append(time.perf_counter() - start)
            assert baseline == expected == filtered, (
                n, expected - filtered, filtered - expected
            )
            assert tuple(secret) in filtered
            assert filtered_stats["joined_pairs"] == baseline_stats["joined_pairs"]
            rows.append((baseline_stats, filtered_stats))

        def med(field, which=1):
            return statistics.median(row[which][field] for row in rows)

        base_products = med("public_full_pass", 0) * (1 + LEVELS)
        filtered_products = (
            med("linear_ring_products") + med("square_computations")
            + med("eval_ring_products")
        )
        print(
            f"N={n}: exact sets agree in {TRIALS}/{TRIALS}; "
            f"median joined pairs={med('joined_pairs', 0):g}; "
            f"public-pass={med('public_full_pass', 0):g}; "
            f"linear rejects={med('linear_rejects'):g}; "
            f"squares baseline/filtered={med('public_full_pass', 0):g}/"
            f"{med('square_computations'):g}; "
            f"ring-product proxy baseline/filtered="
            f"{base_products:g}/{filtered_products:g}; "
            f"median seconds baseline/filtered="
            f"{statistics.median(baseline_times):.6f}/"
            f"{statistics.median(filtered_times):.6f}"
        )


if __name__ == "__main__":
    main()
