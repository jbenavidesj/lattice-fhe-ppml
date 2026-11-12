#!/usr/bin/env python3
"""Exact-rational one-multiplication noise audit for the N=8192 RNS-BFV candidate."""
from fractions import Fraction
from math import ceil, floor, prod

Q_LANES = [
    36028797002170369,
    36028796951838721,
    18014398508400641,
    18014398507892737,
]
N = 8192
T = 65537
BASE = 1 << 16
LEVELS = 14
ETA = 2

Q = prod(Q_LANES)
DELTA, R = divmod(Q, T)
assert Q.bit_length() == 218
assert LEVELS == 14 and BASE**LEVELS >= Q and BASE**(LEVELS - 1) < Q

# Public-key and encryption phase error:
# e*u + e1 + e2*s, with ||e||inf,||e2||inf,||e1||inf <= ETA
# and ||u||1,||s||1 <= N.
E0 = 2 * ETA * N + ETA
assert E0 == 32770

# For centered ciphertext-component lifts:
# ||c0_hat + c1_hat*s||inf <= Q*(N+1)/2.
# x = Delta*m + e + Q*k, with ||m||inf <= T-1.
K_REAL_BOUND = Fraction(N + 1, 2) + Fraction(DELTA * (T - 1) + E0, Q)
K = floor(K_REAL_BOUND)
assert K == 4097 and K_REAL_BOUND < Fraction(8195, 2)

M = (T - 1) + T * K
E = E0 + R * K
PRODUCT_BOUND = N * M * M
M12_BOUND = T // 2
H = ceil(Fraction(PRODUCT_BOUND + M12_BOUND, T))

# Error terms after integer tensor multiplication and t/Q scale-and-round:
quotient_term = Fraction(R * H)
scale_bias_term = Fraction(DELTA * R * PRODUCT_BOUND, Q)
cross_term = Fraction(2 * N * M * E)  # t*Delta/Q < 1
error_product_term = Fraction(T * N * E * E, Q)
rounding_term = Fraction(1 + N + N * N, 2)
key_switch_term = Fraction(LEVELS * (BASE - 1) * (ETA * N))

TOTAL = (quotient_term + scale_bias_term + cross_term
         + error_product_term + rounding_term + key_switch_term)
DECODING_MARGIN = Fraction(Q, 2 * T) - Fraction(R * M12_BOUND, T)

assert TOTAL < DECODING_MARGIN
TOTAL_CEILING = ceil(TOTAL)
assert TOTAL_CEILING == 91700891552753113897

print(f"Q bits: {Q.bit_length()}")
print(f"Delta: {DELTA}")
print(f"Q mod t: {R}")
print(f"initial encryption phase-error bound E0: {E0}")
print(f"centered-lift quotient bound K: {K}")
print(f"lifted plaintext bound M: {M}")
print(f"lifted input-error bound E: {E}")
print(f"plaintext-product bound: {PRODUCT_BOUND}")
print(f"plaintext quotient bound H: {H}")
print(f"quotient/carry contribution: {float(quotient_term):.12e}")
print(f"scale-bias contribution: {float(scale_bias_term):.12e}")
print(f"cross-term contribution: {float(cross_term):.12e}")
print(f"input-error product contribution: {float(error_product_term):.12e}")
print(f"scale-rounding contribution: {float(rounding_term):.12e}")
print(f"key-switch contribution: {int(key_switch_term)}")
print(f"total error upper bound (ceil): {TOTAL_CEILING}")
print(f"decoding margin: {float(DECODING_MARGIN):.12e}")
print(f"bound/margin ratio: {float(TOTAL / DECODING_MARGIN):.12e}")
print("RNS-BFV one-multiplication deterministic correctness bound: PASS")
