#!/usr/bin/env python3
"""Controlled four-way candidate filtering on identical toy transcripts.

For each transcript, enumerate the full ternary candidate space and compare:
  1) public-key equation only;
  2) all original evaluation-key equations only;
  3) public key plus all original evaluation-key equations;
  4) public key plus the exact transformed evaluation-key system.

The transformed system anchors the first original residual and propagates
the exact adjacent differences z_j = r_{j+1} - B*r_j. It reconstructs each
original residual and checks its exact eta=2 support. Thus it preserves the
joint error law; it is not a coordinatewise widened-box approximation.
"""
from itertools import product
from random import Random
from statistics import mean, median

ETA = 2
Q = 65537
B = 16
LEVELS = 14
DIMENSIONS = (2, 3, 4, 5)
TRIALS = {2: 40, 3: 30, 4: 30, 5: 20}


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
    # Exact centered-binomial eta=2: Binomial(4,1/2)-2.
    return [sum(rng.randrange(2) for _ in range(4)) - 2 for _ in range(n)]


def residual(b, a, candidate, target, q):
    raw = sub(add(b, negacyclic_mul(a, candidate, q), q), target, q)
    return [centered(x, q) for x in raw]


def within_support(poly):
    return all(abs(x) <= ETA for x in poly)


def exact_transformed_test(eval_residuals, q):
    """Test the invertibly transformed joint residual vector without loss."""
    if not within_support(eval_residuals[0]):
        return False
    previous = eval_residuals[0]
    for j in range(LEVELS - 1):
        z = [
            centered(eval_residuals[j + 1][i] - B * eval_residuals[j][i], q)
            for i in range(len(previous))
        ]
        reconstructed = [
            centered(z[i] + B * previous[i], q)
            for i in range(len(previous))
        ]
        if not within_support(reconstructed):
            return False
        previous = reconstructed
    return True


def make_transcript(seed, n):
    rng = Random(seed)
    secret = [rng.choice((-1, 0, 1)) for _ in range(n)]
    square = negacyclic_mul(secret, secret, Q)

    a_pk = [rng.randrange(Q) for _ in range(n)]
    e_pk = sample_error(rng, n)
    b_pk = sub(e_pk, negacyclic_mul(a_pk, secret, Q), Q)

    eval_rows = []
    for j in range(LEVELS):
        a_j = [rng.randrange(Q) for _ in range(n)]
        e_j = sample_error(rng, n)
        target = [(pow(B, j, Q) * x) % Q for x in square]
        b_j = add(sub(target, negacyclic_mul(a_j, secret, Q), Q), e_j, Q)
        eval_rows.append((a_j, b_j))
    return tuple(secret), (a_pk, b_pk), eval_rows


def filter_one(seed, n):
    planted, public_row, eval_rows = make_transcript(seed, n)
    a_pk, b_pk = public_row
    survivors = {"pk": set(), "eval": set(), "joint": set(), "transformed": set()}

    for candidate_tuple in product((-1, 0, 1), repeat=n):
        candidate = list(candidate_tuple)
        public_res = residual(b_pk, a_pk, candidate, [0] * n, Q)
        pk_ok = within_support(public_res)

        candidate_sq = negacyclic_mul(candidate, candidate, Q)
        eval_res = []
        for j, (a_j, b_j) in enumerate(eval_rows):
            target = [(pow(B, j, Q) * x) % Q for x in candidate_sq]
            eval_res.append(residual(b_j, a_j, candidate, target, Q))
        eval_ok = all(within_support(r) for r in eval_res)
        transformed_ok = exact_transformed_test(eval_res, Q)

        if pk_ok:
            survivors["pk"].add(candidate_tuple)
        if eval_ok:
            survivors["eval"].add(candidate_tuple)
        if pk_ok and eval_ok:
            survivors["joint"].add(candidate_tuple)
        if pk_ok and transformed_ok:
            survivors["transformed"].add(candidate_tuple)

    assert planted in survivors["pk"]
    assert planted in survivors["eval"]
    assert planted in survivors["joint"]
    assert planted in survivors["transformed"]
    assert survivors["joint"] == survivors["transformed"], (
        seed, survivors["joint"], survivors["transformed"]
    )
    return {key: len(value) for key, value in survivors.items()}


def main():
    print("Controlled four-way ternary candidate filtering")
    print(f"q={Q}; B={B}; eta={ETA}; levels={LEVELS}; error law=CBD_eta2")
    print("All four scenarios use the same generated transcript per trial.")
    print("Transformed test anchors r_0 and uses exact z_j=r_(j+1)-B*r_j recurrence.")
    print("Exact transformed test is an invertible reparameterization, not extra information.")
    for n in DIMENSIONS:
        rows = [filter_one(0xE7A1 + 10000 * n + trial, n)
                for trial in range(TRIALS[n])]
        print(f"[N={n}] secret_space={3**n}; trials={TRIALS[n]}")
        for key in ("pk", "eval", "joint", "transformed"):
            vals = [row[key] for row in rows]
            print(f"{key}: mean={mean(vals):.4f}; median={median(vals):.2f}; "
                  f"max={max(vals)}; unique={sum(v == 1 for v in vals)}/{len(vals)}")
        print(f"joint_equals_exact_transformed={all(r['joint']==r['transformed'] for r in rows)}")
        print(f"joint_survivors_le_min_of_marginals={all(r['joint'] <= min(r['pk'],r['eval']) for r in rows)}")


if __name__ == "__main__":
    main()
