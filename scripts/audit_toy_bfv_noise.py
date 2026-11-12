#!/usr/bin/env python3
"""Exact-rational audit of the tiny-ring BFV one-multiplication noise bound.

This audits the conservative analytical bound, not a security parameter set.
"""
from fractions import Fraction


def audit(n: int, q: int, t: int, base: int) -> dict[str, Fraction | int]:
    assert n > 0 and q > t >= 2 and q % (2 * n) == 1 and base >= 2
    delta, r = divmod(q, t)
    levels, capacity = 0, 1
    while capacity < q:
        capacity *= base
        levels += 1
    # Ternary public-key encryption: eps = e1 + e2*s - e*u.
    eps = 1 + 2 * n
    m = t - 1
    bias = Fraction(delta * r * n * m * m, q)
    cross = Fraction(2 * t * delta * n * m * eps, q)
    noise_product = Fraction(t * n * eps * eps, q)
    rounding = Fraction(1 + n + n * n, 2)
    key_switch = n * levels * (base - 1)
    total = bias + cross + noise_product + rounding + key_switch
    margin = Fraction(q, 2 * t) - Fraction(r * m, t)
    assert total < margin, (total, margin)
    return {
        "delta": delta, "remainder": r, "gadget_levels": levels,
        "input_error_inf_bound": eps, "bias": bias, "cross": cross,
        "noise_product": noise_product, "rounding": rounding,
        "key_switch": key_switch, "total_error_bound": total,
        "decoding_margin": margin,
    }


if __name__ == "__main__":
    result = audit(n=8, q=786433, t=17, base=2)
    for key, value in result.items():
        print(f"{key}={value}")
    print("PASS: analytical one-multiplication bound is below the decoding margin")
