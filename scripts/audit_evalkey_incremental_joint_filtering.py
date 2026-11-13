#!/usr/bin/env python3
"""Stagewise information accounting for original and transformed eval-key filters.

For each identical synthetic transcript, this exhaustively enumerates ternary
candidate secrets and records survivors after:
  * the public-key equation;
  * each original evaluation-key equation in sequence;
  * the exact anchor-plus-adjacent-differences representation;
  * the coarse marginal difference bound |z_j| <= 2*ETA*(B+1).

Both evaluation-only and public-plus-evaluation filters are measured. The
exact transformed sets must equal the original sets at every stage. The coarse
sets are supersets and may contain false candidates. This is a tiny toy audit,
not a scalable attack or security estimate.
"""
from itertools import product
from random import Random
from statistics import mean

ETA = 2


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
    # CBD_eta2 = Binomial(4, 1/2) - 2; support [-2,2].
    return [sum(rng.randrange(2) for _ in range(4)) - 2 for _ in range(n)]


def residual(b, a, candidate, target, q):
    raw = sub(add(b, negacyclic_mul(a, candidate, q), q), target, q)
    return tuple(centered(x, q) for x in raw)


def in_support(r):
    return all(abs(x) <= ETA for x in r)


def make_transcript(seed, n, q, B, levels):
    rng = Random(seed)
    planted = tuple(rng.choice((-1, 0, 1)) for _ in range(n))
    planted_sq = negacyclic_mul(planted, planted, q)

    a_pk = [rng.randrange(q) for _ in range(n)]
    e_pk = sample_error(rng, n)
    b_pk = sub(e_pk, negacyclic_mul(a_pk, planted, q), q)

    eval_rows = []
    for j in range(levels):
        a_j = [rng.randrange(q) for _ in range(n)]
        e_j = sample_error(rng, n)
        target = [(pow(B, j, q) * x) % q for x in planted_sq]
        b_j = add(sub(target, negacyclic_mul(a_j, planted, q), q), e_j, q)
        eval_rows.append((a_j, b_j))
    return planted, (a_pk, b_pk), eval_rows


def one_trial(seed, n, q, B, levels):
    planted, (a_pk, b_pk), eval_rows = make_transcript(seed, n, q, B, levels)
    candidates = list(product((-1, 0, 1), repeat=n))

    # Residuals are computed once, so all filters compare identical data.
    public_ok = set()
    eval_residuals = {}
    for cand_tuple in candidates:
        cand = list(cand_tuple)
        pub_r = residual(b_pk, a_pk, cand, [0] * n, q)
        if in_support(pub_r):
            public_ok.add(cand_tuple)

        cand_sq = negacyclic_mul(cand, cand, q)
        rows = []
        for j, (a_j, b_j) in enumerate(eval_rows):
            target = [(pow(B, j, q) * x) % q for x in cand_sq]
            rows.append(residual(b_j, a_j, cand, target, q))
        eval_residuals[cand_tuple] = rows

    # Stage 0: anchor residual r_0. Later stages add one level/difference.
    eval_original = set(candidates)
    eval_exact = set(candidates)
    eval_coarse = set(candidates)
    joint_original = set(public_ok)
    joint_exact = set(public_ok)
    joint_coarse = set(public_ok)

    counts = {
        "eval_original": [],
        "eval_exact": [],
        "eval_coarse": [],
        "joint_original": [],
        "joint_exact": [],
        "joint_coarse": [],
    }
    extras = {"eval": [], "joint": []}

    for j in range(levels):
        if j == 0:
            eval_original = {c for c in eval_original if in_support(eval_residuals[c][0])}
            eval_exact = {c for c in eval_exact if in_support(eval_residuals[c][0])}
            eval_coarse = {c for c in eval_coarse if in_support(eval_residuals[c][0])}
            joint_original = {c for c in joint_original if in_support(eval_residuals[c][0])}
            joint_exact = {c for c in joint_exact if in_support(eval_residuals[c][0])}
            joint_coarse = {c for c in joint_coarse if in_support(eval_residuals[c][0])}
        else:
            def exact_step(c):
                prev = eval_residuals[c][j - 1]
                nxt = eval_residuals[c][j]
                z = tuple(centered(nxt[k] - B * prev[k], q) for k in range(n))
                reconstructed = tuple(centered(z[k] + B * prev[k], q) for k in range(n))
                return reconstructed == nxt and in_support(reconstructed)

            def coarse_step(c):
                prev = eval_residuals[c][j - 1]
                nxt = eval_residuals[c][j]
                z = (centered(nxt[k] - B * prev[k], q) for k in range(n))
                return all(abs(v) <= ETA * (B + 1) for v in z)

            eval_original = {c for c in eval_original if in_support(eval_residuals[c][j])}
            eval_exact = {c for c in eval_exact if exact_step(c)}
            eval_coarse = {c for c in eval_coarse if coarse_step(c)}
            joint_original = {c for c in joint_original if in_support(eval_residuals[c][j])}
            joint_exact = {c for c in joint_exact if exact_step(c)}
            joint_coarse = {c for c in joint_coarse if coarse_step(c)}

        assert eval_original == {
            c for c in candidates
            if all(in_support(eval_residuals[c][k]) for k in range(j + 1))
        }
        assert eval_original == eval_exact, (seed, j, eval_original, eval_exact)
        assert joint_original == joint_exact, (seed, j, joint_original, joint_exact)
        assert joint_original.issubset(joint_coarse)
        assert eval_original.issubset(eval_coarse)

        counts["eval_original"].append(len(eval_original))
        counts["eval_exact"].append(len(eval_exact))
        counts["eval_coarse"].append(len(eval_coarse))
        counts["joint_original"].append(len(joint_original))
        counts["joint_exact"].append(len(joint_exact))
        counts["joint_coarse"].append(len(joint_coarse))
        extras["eval"].append(len(eval_coarse - eval_original))
        extras["joint"].append(len(joint_coarse - joint_original))

    assert planted in public_ok
    assert planted in eval_original and planted in joint_original
    return len(public_ok), counts, extras


def run_case(label, n, q, B, levels, trials):
    rows = [one_trial(seed + 0xA11CE + 1009 * n, n, q, B, levels)
            for seed in range(trials)]
    pub_counts = [r[0] for r in rows]
    print(f"[{label}] N={n}; q={q}; B={B}; eta={ETA}; levels={levels}; trials={trials}")
    print(f"ternary_secret_space={3**n}")
    print(f"mean_after_public_key={mean(pub_counts):.4f}; max_after_public_key={max(pub_counts)}")
    print("stage,eval_original_mean,eval_exact_mean,eval_coarse_mean,eval_coarse_extra_mean,"
          "joint_original_mean,joint_exact_mean,joint_coarse_mean,joint_coarse_extra_mean")
    for j in range(levels):
        avg = {key: mean(r[1][key][j] for r in rows) for key in rows[0][1]}
        ex_eval = mean(r[2]["eval"][j] for r in rows)
        ex_joint = mean(r[2]["joint"][j] for r in rows)
        print(f"{j},{avg['eval_original']:.4f},{avg['eval_exact']:.4f},"
              f"{avg['eval_coarse']:.4f},{ex_eval:.4f},"
              f"{avg['joint_original']:.4f},{avg['joint_exact']:.4f},"
              f"{avg['joint_coarse']:.4f},{ex_joint:.4f}")
    print(f"exact_eval_equals_original_at_every_stage="
          f"{all(r[1]['eval_original'] == r[1]['eval_exact'] for r in rows)}")
    print(f"exact_joint_equals_original_at_every_stage="
          f"{all(r[1]['joint_original'] == r[1]['joint_exact'] for r in rows)}")
    print(f"trials_with_any_eval_only_coarse_extra="
          f"{sum(any(v > 0 for v in r[2]['eval']) for r in rows)}/{trials}")
    print(f"trials_with_any_joint_coarse_extra="
          f"{sum(any(v > 0 for v in r[2]['joint']) for r in rows)}/{trials}")
    print(f"max_eval_only_coarse_extra={max(max(r[2]['eval']) for r in rows)}")
    print(f"max_joint_coarse_extra={max(max(r[2]['joint']) for r in rows)}")


def main():
    print("Stagewise comparison of original, exact-joint, and coarse transformed filters")
    print("The exact transform is a bijective reparameterization; it must match original filters.")
    print("The coarse bound is a marginal support relaxation, not an equivalent joint law.")
    run_case("low_modulus_q17", n=2, q=17, B=2, levels=6, trials=200)
    run_case("low_modulus_q19", n=2, q=19, B=2, levels=6, trials=200)
    run_case("ambiguity_q257", n=2, q=257, B=4, levels=6, trials=40)
    run_case("small_q65537", n=4, q=65537, B=16, levels=14, trials=20)
    run_case("medium_q65537", n=6, q=65537, B=16, levels=14, trials=10)
    run_case("larger_q65537", n=8, q=65537, B=16, levels=14, trials=3)


if __name__ == "__main__":
    main()
