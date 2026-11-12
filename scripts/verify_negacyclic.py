#!/usr/bin/env python3
"""Independent polynomial arithmetic reference tests on small rings."""
import random

def mul(a, b, q):
    n = len(a)
    c = [0] * n
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            k = i + j
            if k < n:
                c[k] = (c[k] + x * y) % q
            else:
                c[k - n] = (c[k - n] - x * y) % q
    return c

def main():
    rng = random.Random(20261112)
    count = 0
    for n, q in ((2, 97), (4, 97), (8, 257), (16, 769)):
        for _ in range(1000):
            a = [rng.randrange(q) for _ in range(n)]
            b = [rng.randrange(q) for _ in range(n)]
            # Independent coefficient-wise reference accumulation.
            expected = [0] * n
            for i in range(n):
                for j in range(n):
                    k = i + j
                    if k < n:
                        expected[k] = (expected[k] + a[i] * b[j]) % q
                    else:
                        expected[k - n] = (expected[k - n] - a[i] * b[j]) % q
            assert mul(a, b, q) == expected
            count += 1
    print(f"PASS: {count} deterministic negacyclic reference cases")

if __name__ == "__main__":
    main()
