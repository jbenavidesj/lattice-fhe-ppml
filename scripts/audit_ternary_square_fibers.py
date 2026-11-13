#!/usr/bin/env python3
"""Exhaustively measure fibers of the ternary negacyclic-square map.

This isolates what the s^2 component can and cannot reveal about a ternary
secret. It is a toy-domain combinatorial audit, not a key-recovery attack.
"""
from collections import Counter, defaultdict
from itertools import product

Q = 65537
DEGREES = (2, 4, 6, 8)


def negacyclic_mul_integer(a, b):
    """Return the integer-lift negacyclic product, without modular reduction."""
    n = len(a)
    out = [0] * n
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            k = i + j
            sign = 1
            if k >= n:
                k -= n
                sign = -1
            out[k] += sign * x * y
    return tuple(out)


def negacyclic_mul_mod(a, b, q):
    return tuple(x % q for x in negacyclic_mul_integer(a, b))


def square_parity_identity(secret, integer_square):
    """Check parity on the integer lift; parity is not well-defined mod odd q."""
    n = len(secret)
    for i in range(n):
        expected = 0
        if i % 2 == 0:
            r = i // 2
            expected = (secret[r] + secret[r + n // 2]) & 1
        if (integer_square[i] & 1) != expected:
            return False
    return True


def analyze(n):
    fibers = defaultdict(list)
    parity_checks = 0
    for secret in product((-1, 0, 1), repeat=n):
        integer_square = negacyclic_mul_integer(secret, secret)
        square = tuple(x % Q for x in integer_square)
        assert square_parity_identity(secret, integer_square)
        parity_checks += 1
        fibers[square].append(secret)

    sizes = Counter(len(v) for v in fibers.values())
    max_size = max(sizes)
    mean_fiber = (3 ** n) / len(fibers)
    singleton = sizes.get(1, 0)
    sign_pairs = 0
    extra_collisions = 0
    for members in fibers.values():
        member_set = set(members)
        if members and tuple(-x for x in members[0]) in member_set:
            sign_pairs += 1
        # Every nonzero secret has at least the unavoidable {s,-s} collision.
        expected_min = 1 if all(x == 0 for x in members[0]) else 2
        if len(members) > expected_min:
            extra_collisions += 1

    print(
        f"N={n}: secrets={3**n}; distinct_squares={len(fibers)}; "
        f"mean_fiber={mean_fiber:.4f}; max_fiber={max_size}; "
        f"singleton_fibers={singleton}; fiber_size_histogram={dict(sorted(sizes.items()))}; "
        f"fibers_with_sign_partner={sign_pairs}; "
        f"fibers_with_collisions_beyond_sign={extra_collisions}; "
        f"parity_checks={parity_checks}"
    )
    # Square is invariant under global sign. For every nonzero s, -s is distinct.
    assert len(fibers[(0,) * n]) >= 1
    assert sum(size * multiplicity for size, multiplicity in sizes.items()) == 3 ** n
    assert parity_checks == 3 ** n


def main():
    print(f"Ternary negacyclic-square fiber audit over Z/{Q}Z")
    print("The square map is sign-invariant; counts are exact for each toy N.")
    for n in DEGREES:
        analyze(n)


if __name__ == "__main__":
    main()
