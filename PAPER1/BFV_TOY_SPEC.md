# Tiny-ring BFV model: mathematical contract and limits

## Purpose

This module is a small-ring executable correctness model. It is deliberately separate from the four-lane, N=8192 RNS arithmetic candidates. It is not the Paper 1 production parameter set, does not establish security, and is not suitable for protecting data.

## Ring and parameters

The toy ring is R_q = (Z/qZ)[X]/(X^N+1), with power-of-two N, odd q, q congruent to 1 modulo 2N, and 2 <= t < q. The plaintext ring is R_t = (Z/tZ)[X]/(X^N+1). Let Delta = floor(q/t). Coefficients are stored as canonical residues in [0,q) or [0,t), as appropriate.

## Secret and public key

The demonstration secret s, ephemeral u, and error terms use coefficients represented by 0, 1, and q-1 (the signed values 0, 1, and -1). A is sampled uniformly by a deterministic demonstration generator. The error distribution is this tiny ternary law, not a discrete Gaussian sampler.

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

For ciphertexts c=(c0,c1) and d=(d0,d1), the implementation first chooses the centered integer lift of every coefficient of each input component. It forms the three negacyclic tensor products over Z[X]/(X^N+1):
- U0 = c0*d0
- U1 = c0*d1 + c1*d0
- U2 = c1*d1

The integer coefficients U_k are then mapped by W_k = round(t*U_k/q), with ties away from zero, and reduced modulo q. The quotient information from the integer products is deliberately retained until after scale-and-round; reducing U_k modulo q first would implement a different operation. Intermediate arithmetic is checked i128 and fails closed on overflow.

For each coefficient, define the rounding residual rho_k = W_k - t*U_k/q. By the specified nearest-integer rule, |rho_k| <= 1/2. This is an exact local rounding statement; it is not by itself a proof that the decrypted plaintext product is correct, because the full BFV phase also contains the input encryption errors, representative-lift terms, and plaintext-modulus reduction terms.

The regression suite compares the unrelinearized result with direct negacyclic plaintext multiplication for one fixed vector and a deterministic 64-seed sweep. The multiplication tests use N=8, q=786433, t=17; the basic encryption/addition tests use N=8, q=65537, t=17. These finite deterministic tests are regression evidence, not a universal correctness proof.

## Gadget relinearization (toy model)

The module now contains a coefficient-wise base-B relinearization experiment. For L = ceil(log_B(q)) digit levels, it generates evaluation-key pairs (b_j,a_j) satisfying:
`b_j + a_j*s = B^j*s^2 + e_j (mod q)`.
For each coefficient of c2, canonical base-B digits d_j are computed so that c2 = sum_j d_j B^j exactly as an integer in [0,q). The digit polynomials are then used to form:
- c0' = c0 + sum_j d_j*b_j
- c1' = c1 + sum_j d_j*a_j

Thus the switched phase is c0' + c1'*s = c0 + c1*s + c2*s^2 + sum_j d_j*e_j (mod q). The added key-switch error is the negacyclic polynomial sum of digit polynomials times the evaluation-key errors. The implementation is deterministic and uses tiny toy errors; it is not a secure evaluation key.

The regression test compares decryption before and after switching and compares the switched decryption to direct plaintext multiplication. This is only a selected toy test, not a proof of a general noise bound. A production implementation would need a reviewed error distribution, secure randomness, a carefully chosen gadget base and decomposition convention, and a formal bound for the resulting key-switch noise.

The relinearization regression suite additionally checks bases B in {2,4,16} over 16 deterministic seeds per base. These finite tests are useful for catching implementation mistakes but do not replace a worst-case or probabilistic key-switch noise analysis.

## Deterministic key-switch error bound for the toy sampler

For the implemented toy sampler, each evaluation-key error coefficient satisfies |e_{j,k}| <= 1. Each unsigned gadget digit coefficient satisfies 0 <= d_{j,k} <= B-1. For a negacyclic ring of dimension N, each coefficient of d_j*e_j is a signed sum of N products, hence
`||d_j*e_j||_infinity <= N(B-1)`.
With L = ceil(log_B(q)) digit levels, the coefficient-wise triangle inequality gives the deterministic bound
`||e_ks||_infinity <= L*N*(B-1)`.
For the toy test parameters N=8 and q=786433, this conservative bound is 160 for B=2 (L=20), 240 for B=4 (L=10), and 600 for B=16 (L=5).

This bounds only the added key-switch error polynomial under the exact toy sampler and unsigned digit convention. It is not the complete post-multiplication noise bound, does not account for all BFV tensor-product and rounding terms, and cannot be transferred to the N=8192 RNS candidate parameters or a Gaussian RLWE implementation.

## Exact bound for rounding and relinearization perturbations

Let rho_0,rho_1,rho_2 be the coefficientwise scale-and-round residual polynomials, with ||rho_k||_infinity <= 1/2. Let s be the secret polynomial and let e_ks = sum_j d_j*e_j be the key-switch error polynomial. The perturbation contributed by these two mechanisms to the unrelinearized/relinearized phase comparison is
`E_add = rho_0 + rho_1*s + rho_2*s^2 + e_ks`.
For negacyclic convolution, ||a*b||_infinity <= ||a||_infinity ||b||_1. Therefore
`||E_add||_infinity <= (1/2)(1 + ||s||_1 + ||s^2||_1) + ||e_ks||_infinity`.
For the toy ternary secret, ||s||_1 <= N and ||s^2||_1 <= ||s||_1^2 <= N^2. Combining this with the previous toy key-switch bound gives
`||E_add||_infinity <= (1/2)(1+N+N^2) + L*N*(B-1)`.
At N=8, q=786433, B=2, L=20, this is at most 196.5. This is a rigorous bound on the rounding-plus-key-switch contribution only, under the stated integer-lift and ternary-error conventions.

For a phase of the form Delta*m_bar + E, where m_bar is the centered plaintext representative and q=t*Delta+r with 0<=r<t, nearest-integer decryption is guaranteed if
`||E||_infinity < q/(2t) - (r/t)*||m_bar||_infinity`.
This follows from t(Delta*m_bar+E)/q - m_bar = (tE-r*m_bar)/q. It is a decoding condition, not a claim that the entire BFV multiplication error equals E_add. The input-encryption noise, plaintext-product quotient/reduction terms, and representative-lift contributions must still be included in a complete post-multiplication E bound. That complete bound remains open and is a required validation gate.
