#!/usr/bin/env python3
"""Exact-rational, one-multiplication BFV correctness audit for the toy model.

The proof uses centered lifts of ciphertext components and integer tensor products
before t/q scale-and-round. It is a deterministic correctness bound, not a security
estimate and not a proof for the N=8192 RNS parameter candidates.
"""
from fractions import Fraction


def ceil_fraction(x: Fraction) -> int:
    return (x.numerator + x.denominator - 1) // x.denominator


def audit(n: int, q: int, t: int, base: int) -> dict[str, Fraction | int]:
    assert n > 0 and q > t >= 2 and q % (2 * n) == 1 and base >= 2
    delta, r = divmod(q, t)
    # All secret, ephemeral, and error coefficients are in {-1,0,1}.
    eps = 1 + 2 * n  # ||e1 + e2*s - e*u||_infinity
    # A centered ciphertext component is at most q/2; hence
    # ||c0 + c1*s||_infinity <= q(1+n)/2.
    k_lift = (q * (1 + n) // 2 + delta * (t - 1) + eps) // q
    # x = c0+c1*s = Delta*(m+t*k) + (eps_poly+r*k).
    m_lift = (t - 1) + t * k_lift
    e_lift = eps + r * k_lift

    # Product plaintext representative m12 is centered modulo t.
    product_bound = n * m_lift * m_lift
    h_bound = ceil_fraction(Fraction(product_bound + t // 2, t))
    plaintext_quotient = r * h_bound
    scale_bias = Fraction(delta * r * product_bound, q)
    cross_noise = Fraction(2 * t * delta * n * m_lift * e_lift, q)
    product_noise = Fraction(t * n * e_lift * e_lift, q)

    levels, capacity = 0, 1
    while capacity < q:
        capacity *= base
        levels += 1
    rounding = Fraction(1 + n + n * n, 2)
    key_switch = n * levels * (base - 1)
    total = (plaintext_quotient + scale_bias + cross_noise + product_noise
             + rounding + key_switch)
    decoding_margin = Fraction(q, 2 * t) - Fraction(r * (t // 2), t)
    assert total < decoding_margin, (total, decoding_margin)
    return {
        "delta": delta, "remainder": r, "lift_quotient_bound": k_lift,
        "lifted_plaintext_inf_bound": m_lift,
        "lifted_error_inf_bound": e_lift,
        "plaintext_product_quotient_bound": h_bound,
        "plaintext_quotient_error": plaintext_quotient,
        "scale_bias_error": scale_bias,
        "cross_noise": cross_noise,
        "error_product": product_noise,
        "rounding_error": rounding,
        "gadget_levels": levels,
        "key_switch_error": key_switch,
        "total_error_bound": total,
        "decoding_margin": decoding_margin,
    }


if __name__ == "__main__":
    result = audit(n=8, q=1099511627873, t=17, base=2)
    for key, value in result.items():
        print(f"{key}={value}")
    print("PASS: one-multiplication BFV error bound is below the decoding margin")
