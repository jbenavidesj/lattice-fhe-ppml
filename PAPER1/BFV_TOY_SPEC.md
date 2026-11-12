# Tiny-ring BFV model: mathematical contract and limits

## Purpose

This module is a small-ring executable correctness model. It is deliberately separate from the four-lane, N=8192 RNS arithmetic candidates. It is not the Paper 1 production parameter set, does not establish security, and is not suitable for protecting data.

## Ring and parameters

The toy ring is R_q = (Z/qZ)[X]/(X^N+1), with power-of-two N, odd q, q congruent to 1 modulo 2N, and 2 <= t < q. The plaintext ring is R_t = (Z/tZ)[X]/(X^N+1). Let Delta = floor(q/t). Coefficients are stored as canonical residues in [0,q) or [0,t), as appropriate.

## Secret and public key

The demonstration secret s has coefficients represented by 0, 1, and q-1 (the signed values 0, 1, and -1). A is sampled uniformly by a deterministic demonstration generator. The error e is sampled from the same tiny ternary support; this is not a discrete Gaussian sampler.

The public key is (b,a), where b = -(a*s + e) in R_q. Consequently b+a*s = -e (mod q).

## Encryption

For plaintext m in R_t, the implementation lifts its coefficients as Delta*m in R_q. It samples demonstration polynomials u,e1,e2 and returns:
- c0 = b*u + e1 + Delta*m (mod q)
- c1 = a*u + e2 (mod q)

The decryption phase is c0+c1*s = Delta*m + e1 + e2*s - e*u (mod q). This identity is the correctness starting point; successful decoding additionally requires the centered phase error to remain within the rounding margin. The included fixed-seed tests exercise only selected toy instances.

## Decryption and rounding convention

The implementation maps each phase coefficient to its centered integer representative in (-q/2,q/2], computes nearest-integer rounding of t*z/q, with ties rounded away from zero, and reduces modulo t. This explicit convention is part of the implementation contract. It is not a substitute for a general BFV correctness/noise proof.

## Homomorphic addition

Ciphertexts add componentwise modulo q. The test checks that decrypting the sum agrees coefficientwise with plaintext addition modulo t for the selected toy vectors.

## Explicitly not implemented

This module does not implement ciphertext multiplication, BFV tensor-product scale-and-round, gadget decomposition, relinearization/key switching, modulus switching, noise-budget estimation, bootstrapping/refresh, secure randomness, Gaussian sampling, constant-time arithmetic, or a security estimator. It has no cryptographic security claim. Deterministic seeds and the tiny ternary generator are strictly for reproducible unit tests.

## Next correctness gates

1. Add independent property tests over many toy seeds and plaintexts, including boundary coefficients and failure cases.
2. Derive and test a conservative correctness bound for the exact implemented noise distribution and ring norm.
3. Implement multiplication only after specifying centered integer lifts and the scale-and-round rule; do not reduce tensor components modulo q before the required centered-lift calculation.
4. Add gadget decomposition and relinearization with explicit key-switch error accounting.
5. Replace demonstration sampling with a reviewed CSPRNG and precisely specified error sampler before any security-oriented experiment.
6. Port only after toy correctness is established, then validate against the N=8192 RNS basis with a complete parameter/security analysis.


## Ciphertext multiplication: unrelinearized tensor result

The toy module now includes a first tensor-product experiment. For input ciphertexts (c0,c1) and (d0,d1), it computes in R_q:
- U0 = c0*d0
- U1 = c0*d1 + c1*d0
- U2 = c1*d1

Before any reduction modulo q, every coefficient of each input ciphertext component is lifted to its centered integer representative. The three polynomial products U_k are then computed over the integers in Z[X]/(X^N+1), retaining all quotient information. Each integer coefficient is multiplied by t/q using nearest-integer rounding (ties away from zero), and only then reduced modulo q. The implementation uses checked i128 arithmetic and returns an error on overflow. The output retains all three components; no gadget decomposition or relinearization is applied. Decryption evaluates c0' + c1'*s + c2'*s^2 and then performs the ordinary BFV t/q decoding step.

The test compares this unrelinearized result against direct negacyclic multiplication in the plaintext ring for one fixed toy vector. This is an initial executable check, not a proof of correctness for all messages, seeds, or parameter sets. Reducing U_k modulo q before scale-and-round is incorrect because it discards quotient information; the implementation deliberately preserves centered integer lifts through the tensor products. A formal bound on accumulated noise and component-wise rounding error remains outstanding.
