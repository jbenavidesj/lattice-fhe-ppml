# Experimental RNS-BFV end-to-end integration

## Scope and status

This note records the first integrated N=8192 RNS-BFV path in `src/keygen.rs`. It is an experimental correctness prototype. It is not security-reviewed, does not have a concrete RLWE security estimate, and is not suitable for protecting data.

## Parameters and representation

- Ring: R = Z[X]/(X^8192+1).
- Ciphertext modulus: Q = product of the four configured pairwise-coprime NTT primes (218 bits).
- Plaintext modulus used by the integration test: t = 65537.
- Plaintext embedding: Delta = floor(Q/t).
- Secret coefficients: independent uniform ternary {-1,0,1}.
- Public-key and encryption errors: eta=2 centered-binomial, support [-2,2].
- Ephemeral encryption polynomial: independent uniform ternary.
- Uniform R_Q elements are sampled as independent uniform residues in each CRT lane. By CRT, the product distribution is uniform over the aggregate residue ring.

## Key generation and encryption equations

The public key is generated from a uniform a in R_Q and error e:
`b = -a*s + e (mod Q)`.

For plaintext m in R_t, ephemeral u and errors e1,e2, encryption returns:
`c0 = b*u + e1 + Delta*m (mod Q)`,
`c1 = a*u + e2 (mod Q)`.

The decryption phase is:
`c0 + c1*s = Delta*m + e*u + e1 + e2*s (mod Q)`.

Since ||e||_infinity <= 2, ||u||_1 <= N, ||e2||_infinity <= 2, ||s||_1 <= N, and ||e1||_infinity <= 2, the encryption phase error has the deterministic bound
`||e*u + e1 + e2*s||_infinity <= 4N + 2 = 32770`.
For t=65537, the exact Q/(2t) decoding half-margin is approximately 3.21e60, so this isolated encryption-error bound is comfortably inside the one-encryption decoding margin. This is a bound for the specified bounded samplers, not a security estimate and not a multiplication-noise theorem. Decryption uses the centered CRT representative and exact coefficientwise round(t*x/Q), then reduces modulo t.

Homomorphic addition is componentwise modulo Q.

## Multiplication and relinearization

The implemented multiply/relinearize API performs:
1. Lift every input ciphertext component to its centered integer coefficient representative.
2. Form the three integer negacyclic tensor products over Z[X]/(X^N+1), retaining all quotient information.
3. Recover each exact integer product coefficient with a nine-prime auxiliary NTT/CRT basis, then apply coefficientwise round(t*U/Q) and encode the result in the four RNS lanes.
4. Centered gadget decomposition of the scaled quadratic component.
5. Key switching using evaluation-key digits satisfying
   `b_j + a_j*s = B^j*s^2 + e_j (mod Q)`.

The key-switch phase contribution is `sum_j d_j*e_j`. Its current deterministic conditional infinity-norm bound is documented in `PAPER1/SECURITY_AND_NOISE_REVIEW.md`.

The input centered lifts and final scale-and-round use exact BigInt CRT. Integer negacyclic products are recovered by a nine-prime auxiliary NTT/CRT basis whose product exceeds twice the bound N*(Q/2)^2 for the current parameter set. This preserves the integer-product quotient required by BFV multiplication. It is a correctness reference, not a fast RNS base-conversion/rounding algorithm.

## Executable checks

- An N=8192 test generates the secret/evaluation key, generates a public key, encrypts two sparse plaintext vectors, decrypts both, and verifies homomorphic addition.
- A second test extension compares multiply-plus-relinearize decryption with an independent sparse negacyclic plaintext-ring product modulo t.
- CI must pass for the exact commit containing these tests before treating the checks as validated.
- These finite tests do not replace a complete worst-case RNS-BFV multiplication-noise proof or independent cryptographic review.

## Remaining requirements

1. Complete a formal RNS multiplication correctness derivation under the exact centered-input-lift, integer-product, scale-and-round, and gadget conventions implemented here.
2. Establish a deterministic or probabilistic bound for every input-noise, product, quotient/carry, scale-rounding, and key-switch term.
3. Validate the bound against the exact decoding margin for the chosen Q and t.
4. Run and record a current lattice-estimator diagnostic with immutable estimator version and cost model; justify the ring-LWE heuristic and assess structural attacks.
5. Audit secret-dependent control flow, memory access, temporary copies, and side-channel exposure.
6. Replace BigInt reference operations with a proven efficient RNS implementation only after differential tests against this reference.
7. Run independent tests and release benchmarks with raw data and reproducible hardware/compiler metadata.

Do not claim production security, a concrete security level, arbitrary multiplicative depth, or a performance improvement from this prototype.
