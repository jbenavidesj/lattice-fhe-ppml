#!/usr/bin/env python3
"""Held-out evaluation of the frozen adaptive MITM coordinate selector.

The selector weight and model are frozen at the previously used lambda=4.
Instances use a disjoint deterministic seed from the development experiment.
This is a toy-scale held-out check, not evidence of generalization to other
(q, eta) values or production ring dimensions.
"""
import random
import statistics
import time

import toy_evalkey_mitm as mitm

HELD_OUT_SEED = 0xC0FFEE
HELD_OUT_TRIALS = 10
REPEATS = 2
CANDIDATE_KS = (1, 2, 3, 4)


def median_runtime(n, public_sample, eval_samples, expected, k):
    samples = []
    for _ in range(REPEATS):
        start = time.perf_counter()
        actual = mitm.mitm_candidates(n, public_sample, eval_samples, k)
        samples.append(time.perf_counter() - start)
        assert actual == expected, (n, k, expected - actual, actual - expected)
    return statistics.median(samples)


def main():
    rng = random.Random(HELD_OUT_SEED)
    print(
        f"Held-out MITM selector evaluation: seed={HELD_OUT_SEED:#x}, "
        f"trials={HELD_OUT_TRIALS}, repeats={REPEATS}, "
        f"frozen lambda=4, q={mitm.Q}, eta={mitm.ETA}"
    )
    for n in (4, 6, 8):
        selected = mitm.choose_coordinates(
            n, candidate_ks=CANDIDATE_KS, pair_weight=4.0
        )["k"]
        timings = {k: [] for k in CANDIDATE_KS}
        exact_checks = 0
        for _ in range(HELD_OUT_TRIALS):
            secret, public_sample, eval_samples = mitm.generate_instance(n, rng)
            expected = mitm.exhaustive_candidates(n, public_sample, eval_samples)
            assert tuple(secret) in expected
            for k in CANDIDATE_KS:
                elapsed = median_runtime(n, public_sample, eval_samples, expected, k)
                timings[k].append(elapsed)
                exact_checks += 1
        medians = {k: statistics.median(v) for k, v in timings.items()}
        best_k = min(medians, key=medians.get)
        regret = medians[selected] / medians[best_k]
        print(
            f"N={n}: frozen_selector_k={selected}; heldout_best_k={best_k}; "
            f"regret={regret:.3f}; medians="
            + ",".join(f"k{k}:{medians[k]:.6f}s" for k in CANDIDATE_KS)
            + f"; exact comparisons={exact_checks}/{exact_checks}"
        )


if __name__ == "__main__":
    main()
