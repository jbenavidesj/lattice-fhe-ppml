#!/usr/bin/env python3
"""Cross-parameter held-out robustness audit for the frozen toy MITM selector.

The selector weight lambda=4 is fixed in advance. Each (q, eta, N) cell uses
fresh deterministic instances; every fixed k is timed on the same instances
and its candidate set is compared with exhaustive enumeration. This is a
small toy diagnostic, not a production complexity or security estimate.
"""
import random
import statistics
import time

import toy_evalkey_mitm as mitm

SEED = 0x5E1EC7
TRIALS = 8
REPEATS = 2
Q_VALUES = (17, 31)
ETA_VALUES = (1, 2)
DEGREES = (4, 6, 8)
CANDIDATE_KS = (1, 2, 3, 4)
PAIR_WEIGHT = 4.0


def main():
    rng = random.Random(SEED)
    cells = 0
    print(
        f"Cross-parameter MITM selector robustness: seed={SEED:#x}, "
        f"trials/cell={TRIALS}, repeats={REPEATS}, lambda={PAIR_WEIGHT}"
    )
    for q in Q_VALUES:
        for eta in ETA_VALUES:
            if q <= 2 * eta:
                continue
            # The toy generator and checker read these module-level parameters.
            mitm.Q = q
            mitm.ETA = eta
            for n in DEGREES:
                selected = mitm.choose_coordinates(
                    n, q=q, eta=eta, candidate_ks=CANDIDATE_KS,
                    pair_weight=PAIR_WEIGHT
                )["k"]
                per_k = {k: [] for k in CANDIDATE_KS}
                exact = 0
                instance_medians = {k: [] for k in CANDIDATE_KS}
                for _ in range(TRIALS):
                    secret, public_sample, eval_samples = mitm.generate_instance(n, rng)
                    expected = mitm.exhaustive_candidates(
                        n, public_sample, eval_samples
                    )
                    assert tuple(secret) in expected
                    for k in CANDIDATE_KS:
                        samples = []
                        for _repeat in range(REPEATS):
                            start = time.perf_counter()
                            actual = mitm.mitm_candidates(
                                n, public_sample, eval_samples, k
                            )
                            samples.append(time.perf_counter() - start)
                            assert actual == expected, (
                                q, eta, n, k, expected - actual, actual - expected
                            )
                            exact += 1
                        instance_medians[k].append(statistics.median(samples))
                        per_k[k].extend(samples)
                medians = {
                    k: statistics.median(instance_medians[k])
                    for k in CANDIDATE_KS
                }
                best = min(medians, key=medians.get)
                regret = medians[selected] / medians[best]
                print(
                    f"q={q}, eta={eta}, N={n}: selected_k={selected}; "
                    f"best_median_k={best}; regret={regret:.3f}; "
                    + ",".join(f"k{k}:{medians[k]:.6f}s" for k in CANDIDATE_KS)
                    + f"; exact comparisons={exact}/{TRIALS * len(CANDIDATE_KS) * REPEATS}"
                )
                cells += 1
    print(f"Cross-parameter held-out audit passed: {cells} cells.")


if __name__ == "__main__":
    main()
