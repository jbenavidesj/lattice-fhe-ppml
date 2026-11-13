#!/usr/bin/env python3
"""Check the mod-2 parity identity for negacyclic squares of ternary polynomials."""
import random


def negacyclic_square_mod2(secret):
    n = len(secret)
    out = [0] * n
    for i, a in enumerate(secret):
        for j, b in enumerate(secret):
            k = i + j
            sign = 1
            if k >= n:
                k -= n
                sign = -1
            out[k] = (out[k] + sign * a * b) & 1
    return out


def check(n, trials, rng):
    assert n > 0 and n % 2 == 0
    for _ in range(trials):
        secret = [rng.choice((-1, 0, 1)) for _ in range(n)]
        square = negacyclic_square_mod2(secret)
        expected = [0] * n
        for r in range(n // 2):
            expected[2 * r] = (secret[r] + secret[r + n // 2]) & 1
        assert square == expected, (n, secret, square, expected)


def main():
    rng = random.Random(0xBFV)  # deterministic seed
    for n in (2, 4, 8, 16, 32, 64, 128):
        check(n, 200, rng)
    print("Ternary negacyclic-square parity identity: PASS")


if __name__ == "__main__":
    main()
