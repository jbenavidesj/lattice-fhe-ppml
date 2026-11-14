#!/usr/bin/env python3
"""Train/holdout evaluation of the toy MITM coordinate-cost selector.

This is an empirical selector study only for the module's fixed q=11, eta=2
instance generator. It deliberately does not claim cross-(q, eta) generality.
"""
import random
import statistics
import time

import toy_evalkey_mitm as mitm

DEGREES = (4, 6, 8)
K_VALUES = (1, 2, 3, 4)
LAMBDA_GRID = (0.0, 0.5, 1.0, 2.0, 4.0, 8.0, 16.0, 32.0)
TRAIN_TRIALS = 8
HOLDOUT_TRIALS = 8
REPEATS = 3


def measure_split(seed, trials, split_name):
    rng = random.Random(seed)
    measured = {n: [] for n in DEGREES}
    for n in DEGREES:
        for trial in range(trials):
            secret, public, eval_samples = mitm.generate_instance(n, rng)
            start = time.perf_counter()
            exact = mitm.exhaustive_candidates(n, public, eval_samples)
            exhaustive_time = time.perf_counter() - start
            times = {}
            for k in K_VALUES:
                samples = []
                for _ in range(REPEATS):
                    start = time.perf_counter()
                    got = mitm.mitm_candidates(n, public, eval_samples, k)
                    samples.append(time.perf_counter() - start)
                    assert got == exact, (split_name, n, trial, k)
                    assert tuple(secret) in got
                times[k] = statistics.median(samples)
            measured[n].append((exhaustive_time, times))
    return measured


def select_lambda(training):
    scores = {}
    for weight in LAMBDA_GRID:
        regrets = []
        for n, rows in training.items():
            for _exhaustive, times in rows:
                k = mitm.choose_coordinates(
                    n, q=mitm.Q, eta=mitm.ETA,
                    candidate_ks=K_VALUES, pair_weight=weight
                )["k"]
                best = min(times.values())
                regrets.append(times[k] / best)
        scores[weight] = statistics.mean(regrets)
    return min(scores, key=lambda weight: (scores[weight], weight)), scores


def evaluate_holdout(holdout, weight):
    all_regrets = []
    print(f"Frozen lambda={weight:g}; holdout results (q={mitm.Q}, eta={mitm.ETA})")
    for n, rows in holdout.items():
        regrets = []
        selected_ks = []
        exact_fastest = []
        for _exhaustive, times in rows:
            k = mitm.choose_coordinates(
                n, q=mitm.Q, eta=mitm.ETA,
                candidate_ks=K_VALUES, pair_weight=weight
            )["k"]
            regret = times[k] / min(times.values())
            regrets.append(regret)
            selected_ks.append(k)
            exact_fastest.append(min(times, key=times.get))
        all_regrets.extend(regrets)
        print(
            f"N={n}: mean regret={statistics.mean(regrets):.3f}, "
            f"median regret={statistics.median(regrets):.3f}, "
            f"selected k={selected_ks}, empirical fastest k={exact_fastest}"
        )
    print(
        f"Aggregate holdout: mean regret={statistics.mean(all_regrets):.3f}; "
        f"median regret={statistics.median(all_regrets):.3f}; "
        f"instances={len(all_regrets)}"
    )


def main():
    print(
        "MITM selector train/holdout study: "
        f"train={TRAIN_TRIALS}/degree, holdout={HOLDOUT_TRIALS}/degree, "
        f"repeats={REPEATS}, K={K_VALUES}, lambda_grid={LAMBDA_GRID}"
    )
    training = measure_split(0x51EC70, TRAIN_TRIALS, "train")
    holdout = measure_split(0xA11CE, HOLDOUT_TRIALS, "holdout")
    weight, scores = select_lambda(training)
    print("Training mean-regret by lambda:")
    for candidate in LAMBDA_GRID:
        print(f"  lambda={candidate:g}: {scores[candidate]:.4f}")
    print(f"Selected lambda on training split: {weight:g}")
    evaluate_holdout(holdout, weight)


if __name__ == "__main__":
    main()
