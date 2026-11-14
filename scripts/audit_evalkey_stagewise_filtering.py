#!/usr/bin/env python3
"""Stagewise exhaustive filtering of a synthetic public/evaluation-key transcript.

Enumerates ternary secrets only for tiny N. Reports survivors after the public
key and after each original evaluation-key equation. The planted secret is
always retained. This is a toy information-accounting experiment, not an
attack or a security estimate.
"""
from itertools import product
from random import Random

ETA = 2
Q = 65537
B = 16
LEVELS = 14


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


def centered(x, q):
    x %= q
    return x - q if x > q // 2 else x


def sample_error(rng, n):
    return [sum(rng.randrange(2) for _ in range(4)) - 2 for _ in range(n)]


def residual(b, a, candidate, target, q):
    # Transcript convention: b = target - a*s + e, so b + a*c - target = e.
    r = sub(add(b, negacyclic_mul(a, candidate, q), q), target, q)
    return tuple(centered(x, q) for x in r)


def one_trial(seed, n, q, levels):
    rng = Random(seed)
    secret = tuple(rng.choice((-1, 0, 1)) for _ in range(n))
    secret_sq = negacyclic_mul(secret, secret, q)

    apk = [rng.randrange(q) for _ in range(n)]
    epk = sample_error(rng, n)
    bpk = sub(epk, negacyclic_mul(apk, secret, q), q)

    eval_rows = []
    for j in range(levels):
        aj = [rng.randrange(q) for _ in range(n)]
        ej = sample_error(rng, n)
        target = [(pow(B, j, q) * x) % q for x in secret_sq]
        bj = add(sub(target, negacyclic_mul(aj, secret, q), q), ej, q)
        eval_rows.append((aj, bj, target))

    stages = [0] * (levels + 1)
    survivors = []
    for values in product((-1, 0, 1), repeat=n):
        cand = list(values)
        pub = residual(bpk, apk, cand, [0] * n, q)
        if any(abs(x) > ETA for x in pub):
            continue
        survivors.append(values)
    stages[0] = len(survivors)
    assert secret in survivors

    per_level = []
    for j, (aj, bj, _) in enumerate(eval_rows):
        kept = []
        for values in survivors:
            cand = list(values)
            cand_sq = negacyclic_mul(cand, cand, q)
            target = [(pow(B, j, q) * x) % q for x in cand_sq]
            r = residual(bj, aj, cand, target, q)
            if all(abs(x) <= ETA for x in r):
                kept.append(values)
        survivors = kept
        per_level.append(len(survivors))
        assert secret in survivors
    return stages[0], per_level


def run_case(label, n, q, levels, trials):
    rows = [one_trial(seed + 1000 * n, n, q, levels) for seed in range(trials)]
    pub = [x[0] for x in rows]
    print(f"[{label}] N={n}; q={q}; B={B}; eta={ETA}; levels={levels}; trials={trials}")
    print(f"ternary_secret_space={3**n}")
    print(f"mean_after_public_key={sum(pub)/trials:.4f}; max_after_public_key={max(pub)}")
    means = [sum(row[1][j] for row in rows) / trials for j in range(levels)]
    print("mean_survivors_after_eval_level_0_to_last=" + ",".join(f"{x:.4f}" for x in means))
    print("max_survivors_after_eval_level_0_to_last=" + ",".join(str(max(row[1][j] for row in rows)) for j in range(levels)))
    print(f"all_trials_end_with_one_candidate={all(row[1][-1] == 1 for row in rows)}")
    print(f"planted_secret_survives_all_stages={all(row[1][-1] >= 1 for row in rows)}")


def main():
    print("Stagewise public-key and original evaluation-key filtering")
    print("Every stage tests the exact original eta=2 residual support.")
    print("The synthetic samples are independent uniform a-vectors with centered-binomial errors.")
    print("This independence is a toy transcript-generation choice, not a proof about real key generation.")
    run_case("tiny_ring", n=2, q=23, levels=2, trials=40)
    run_case("toy_14_levels", n=4, q=65537, levels=14, trials=30)
    run_case("toy_14_levels_larger", n=6, q=65537, levels=14, trials=10)


if __name__ == "__main__":
    main()
