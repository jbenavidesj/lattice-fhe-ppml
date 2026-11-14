#!/usr/bin/env python3
"""Audit the exact split-secret negacyclic-square identity."""
import random

DEGREES = (4, 6, 8, 10, 12, 16)
MODULI = (11, 65537)
TRIALS = 250


def negacyclic_mul(a, b, q):
    n = len(a)
    out = [0] * n
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            k = i + j
            sign = 1
            if k >= n:
                k -= n
                sign = -1
            out[k] = (out[k] + sign * x * y) % q
    return out


def shift_x(poly, amount, q):
    n = len(poly)
    out = [0] * n
    for i, value in enumerate(poly):
        degree, sign = i + amount, 1
        while degree >= n:
            degree -= n
            sign = -sign
        out[degree] = (out[degree] + sign * value) % q
    return out


def split_square(secret, q):
    n = len(secret)
    if n % 2:
        raise ValueError("The split identity requires even N.")
    m = n // 2
    u = list(secret[:m]) + [0] * m
    v = list(secret[m:]) + [0] * m
    u2 = negacyclic_mul(u, u, q)
    uv = negacyclic_mul(u, v, q)
    v2 = negacyclic_mul(v, v, q)
    cross = shift_x(uv, m, q)
    return [(u2[i] + 2 * cross[i] - v2[i]) % q for i in range(n)]


def eval_residual(a, b, secret, factor, q, square):
    a_secret = negacyclic_mul(a, secret, q)
    return [(b[i] + a_secret[i] - factor * square[i]) % q
            for i in range(len(secret))]


def main():
    rng = random.Random(0x51A17)
    checked = 0
    for q in MODULI:
        for n in DEGREES:
            for _ in range(TRIALS):
                for secret in (
                    [rng.choice((-1, 0, 1)) for _ in range(n)],
                    [rng.randrange(q) for _ in range(n)],
                ):
                    direct = negacyclic_mul(secret, secret, q)
                    split = split_square(secret, q)
                    assert direct == split, (q, n, secret, direct, split)
                    a = [rng.randrange(q) for _ in range(n)]
                    b = [rng.randrange(q) for _ in range(n)]
                    for level in range(4):
                        factor = pow(3, level, q)
                        assert eval_residual(a, b, secret, factor, q, direct) == (
                            eval_residual(a, b, secret, factor, q, split)
                        )
                    checked += 1
    print(f"Split-square identity and evaluation residuals: PASS ({checked} cases)")


if __name__ == "__main__":
    main()
