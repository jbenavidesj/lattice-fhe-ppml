# Structured evaluation-key exposure: preliminary cryptanalytic analysis

## Status and scope

This note analyzes the public relinearization-key format implemented by `src/keygen.rs`. It is a threat-model and algebraic-structure note, **not** a security proof, attack implementation, or security estimate. No claim of IND-CPA security or a bit-security level is made.

## Exact public relation

The secret is a coefficientwise ternary polynomial
`s in R = Z_Q[X]/(X^8192+1)`. For each gadget level j, the implementation samples independent uniform `a_j in R_Q` and a centered-binomial error `e_j` with coefficient support [-2,2], and publishes `(b_j,a_j)` satisfying

```
b_j + a_j*s = B^j*s^2 + e_j  (mod Q),  B=2^16.
```

There are L=14 levels. Thus the adversary receives 14 related RLWE-like equations with:
- one common secret s;
- a common, secret-dependent target polynomial s^2;
- public, known multipliers B^j;
- independent uniform a_j;
- small bounded errors e_j.

This is not the ordinary LWE/RLWE sample model `b+a*s=e`. In particular, treating all 14 pairs as 14 ordinary RLWE samples with zero target is incorrect. The current `scripts/estimate_lwe_proxy.py` intentionally omits these samples and cannot estimate their contribution.

## Algebraic observations

1. The target is not an independent random message: it is the square of the same secret used in the linear term. This creates a related-key / auxiliary-input structure.
2. Since s is ternary, the coefficients of the integer negacyclic square s^2 have magnitude at most N, but this fact alone does not establish a useful attack or a security reduction.
3. For any j,k, public linear combinations can eliminate the formal s^2 target modulo Q, e.g.
   `B^k(b_j+a_j*s)-B^j(b_k+a_k*s)=B^k*e_j-B^j*e_k (mod Q)`.
   However, the corresponding coefficient of s is `B^k*a_j-B^j*a_k`, and the error is multiplied by large powers of B. This identity is not automatically a standard small-error RLWE sample: centered-lift sizes, modular wraparound, and the distribution of the combined error must be analyzed before treating it as an attack.
4. Multiplying each equation by B^{-j} modulo Q makes the target common, but also multiplies the small error by B^{-j} modulo Q. The centered representatives of these modular inverses are not generally small. This normalization therefore does not directly produce a standard small-error sample either.
5. Because the public key also exposes a conventional relation `b_pk+a_pk*s=e_pk`, the evaluation key must be assessed jointly with the public key, not in isolation.

## Required attack analysis

A cryptographic reviewer should investigate, at minimum:

- Joint recovery of s and/or s^2 from the public-key RLWE sample and all 14 evaluation-key equations.
- Whether the algebraic relation s^2 in the power-of-two cyclotomic ring yields exploitable polynomial constraints, including negacyclic convolution equations and the ternary coefficient restriction.
- Multi-sample, multi-target, related-message, hybrid, primal, dual, and algebraic attacks with the actual error and secret distributions.
- Whether linear combinations across gadget levels yield any useful low-noise equations after exact centered-lift analysis.
- The impact of publishing additional evaluation keys, repeated key generation under one secret, or multiple ciphertext/key-switch interfaces.
- Classical and quantum costs, attack-model assumptions, and the estimator's coverage limits.

The reviewer must work with the exact four-prime Q, N=8192, t=65537, B=2^16, L=14, ternary secret, and eta=2 centered-binomial error. Any proposed transformation must preserve the actual modular distribution; heuristic statements about "14 samples" are insufficient.

## Implementation implications

- Keep the evaluation key clearly classified as public auxiliary key material, but do not assume that "public" means harmless.
- Do not add more evaluation-key levels or publish additional related keys without re-running the security analysis.
- Do not claim that the unstructured-LWE estimator covers the evaluation key.
- The code's exhaustive coefficientwise test verifies the correctness of the key relation and small-error support. It does not test hardness.
- The secret-key wrapper's zeroization and the absence of a constant-time audit are separate implementation concerns.

## Current conclusion

The format exposes 14 structured, related RLWE-like samples with a common secret-dependent target s^2. The simple linear-combination identities above do not by themselves demonstrate a break, but they also prevent us from silently treating the samples as ordinary RLWE. Security remains unresolved pending a ring-aware, joint public-key/evaluation-key analysis and independent cryptographic review.

Until then, describe the construction as an experimental RNS-BFV prototype, not a security-validated FHE scheme.
