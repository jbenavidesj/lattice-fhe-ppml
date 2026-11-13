# Security review and complete BFV noise-proof gate

## Status

This document separates implemented correctness properties from security claims. The current N=8192, four-prime RNS candidate is **not assigned a concrete security level**. The experimental key generator is not approved for protecting data.

## 1. Exact instance to be assessed

- Cyclotomic ring: R = Z[X]/(X^8192+1).
- Aggregate modulus: Q = 421249165630599354127590185589164472945208468246547404789529362433 (218 bits).
- Plaintext modulus: t = 65537.
- Secret: independent coefficientwise uniform ternary, {-1,0,1}.
- Evaluation-key error: centered binomial eta=2, defined as the sum of two independent fair bits minus the sum of two independent fair bits; support [-2,2], coefficient standard deviation 1.
- RNS representation: four independent uniform residues per coefficient, one in each pairwise-coprime lane; CRT identifies this with a uniform element of R_Q.
- Gadget base candidate: B=2^16; L=14 digits for this Q.

The sampler implementation and algebraic phase tests are experimental. The error distribution is unusually narrow compared with commonly cited HE parameter sets; do not infer adequate hardness from ring dimension and modulus alone.

## 2. Security-estimation protocol and limitation

A publication-quality estimate must record:
1. estimator repository and immutable commit/version;
2. exact scheme and attack model (ring-LWE, including ring/module structure assumptions);
3. N, cyclotomic polynomial, exact Q, secret and error distributions, sample-count assumptions, and all public/key-switch samples exposed to an attacker;
4. primal, dual, hybrid, algebraic/structural and applicable key-recovery attacks;
5. classical and quantum cost models, BKZ simulator assumptions, and output logs.

The Albrecht lattice-estimator project documents LWE, NTRU and SIS estimators and evolving attack coverage. The Homomorphic Encryption Standard discusses using corresponding LWE estimates as a proxy for power-of-two cyclotomic RLWE under the explicit heuristic that no better ring-structure attacks are known for the considered instantiations. Therefore an unstructured LWE run with n=8192, q=Q, ternary secret and eta=2 centered-binomial error is useful as a diagnostic baseline, but the report must state the heuristic and attack-model limitations; it is not a proof against all ring-structure attacks. The estimator's documentation recommends recording the exact version/commit because estimates can change.

A diagnostic unstructured-LWE script is provided at scripts/estimate_lwe_proxy.py. It pins lattice-estimator commit 7d59f866655362ea8eab803dbc833710c2bc362a and compares the candidate with the HE Standard v2 N=8192 ternary/Gaussian-3.19 reference. It runs two sample-count settings (m=N and m=infinity). The m=N case models one flattened RLWE sample as an LWE proxy; the unlimited-sample case is a sensitivity/conservative setting. Neither models the evaluation-key samples, whose target includes s^2, as ordinary LWE samples. The script is intentionally not run in CI because it requires SageMath and a potentially long estimator execution. No estimator has yet been run for this candidate, so this document reports no bit-security figure and makes no 128-bit claim. The candidate has a larger Q (218 bits) and a narrower error (eta=2 centered-binomial, standard deviation 1) than the HE Standard v2 reference (q=2^214, Gaussian standard deviation 3.19); these differences are a reason to investigate the error distribution, not a basis for inferring security.

See `PAPER1/SECURITY_ESTIMATION_PROTOCOL.md` for the pinned estimator and `PAPER1/EVALUATION_KEY_SECURITY_ANALYSIS.md` for the structured evaluation-key threat model. The unstructured-LWE script does not model the evaluation-key samples.

References:
- https://github.com/malb/lattice-estimator
- https://github.com/malb/lattice-estimator/commit/7d59f866655362ea8eab803dbc833710c2bc362a
- https://eprint.iacr.org/2024/463
- https://homomorphicencryption.org/wp-content/uploads/2024/08/Homomorphic-Encryption-Standard-v1.1.pdf

## 3. Secret-memory handling and side-channel threat model

The RnsSecretKey wrapper now overwrites its four coefficient buffers on Drop using the zeroize crate. The underlying RNS type has an explicit zeroization method and a unit test checks that all lane coefficients become zero. The secret polynomial accessor is crate-private.

This is defense-in-depth, not a complete memory-safety guarantee:
- transient copies, compiler spills, allocator copies, swap, crash dumps and process snapshots are not comprehensively controlled;
- evaluation-key material is public-key material and is not zeroized by this wrapper;
- rejection sampling and error generation have data-dependent retry/branch behavior;
- arithmetic, CRT reconstruction, NTT, polynomial operations and error paths have not received a constant-time audit;
- no cache, power, electromagnetic, fault-injection or microarchitectural side-channel evaluation has been performed.

Before production use, review all secret-dependent branches and memory accesses, use audited constant-time primitives where required, define process/OS memory policy, and commission an independent implementation review. Do not label the implementation constant-time or side-channel resistant.

## 4. RNS key-switch error theorem (implemented algebra, conditional bound)

For evaluation-key digits satisfying
b_j + a_j*s = B^j*s^2 + e_j (mod Q),
and gadget decomposition c_2 = sum_j d_j B^j (mod Q), relinearization changes the decryption phase by
e_ks = sum_j d_j e_j (mod Q).

For negacyclic multiplication,
||u*v||_infinity <= ||u||_infinity * ||v||_1.
Consequently, if every digit coefficient satisfies ||d_j||_infinity <= B-1 and every key error has ||e_j||_1 <= E_1, then
||e_ks||_infinity <= sum_j ||d_j||_infinity ||e_j||_1 <= L(B-1)E_1.

For the current candidate, L=14, B=65536, N=8192, and the implemented eta=2 error has coefficient support [-2,2], hence E_1 <= 2N = 16384 and
||e_ks||_infinity <= 15,032,156,160.

This proves only the key-switch contribution under the stated digit/error bounds. It does not bound the complete BFV multiplication error.

## 5. Complete one-multiplication BFV correctness result

For a ciphertext with phase c_0+c_1*s = Delta*m + e (mod Q), a complete multiplication proof must fix the exact centered-lift convention and derive every term in the phase after tensor multiplication, BFV scale-and-round, and relinearization. The final condition is a strict coefficientwise decoding-margin inequality of the form
||E_mul + e_ks||_infinity < Q/(2t),
with the precise rounding and message-representative convention stated alongside it.

The completed derivation in `PAPER1/RNS_BFV_MULTIPLICATION_NOISE_PROOF.md` and its exact-rational CI audit account for:
- both input ciphertext error polynomials and their multiplication by the opposite message/phase;
- the product of the two input error polynomials;
- centered-lift quotient/carry terms from each ciphertext component;
- BFV scale-and-round residuals for all three tensor components;
- multiplication by s and s^2 of the respective residuals;
- any plaintext-product reduction modulo t;
- the exact key-switch digit convention and e_ks.

The tiny-ring model's proof in `PAPER1/BFV_TOY_SPEC.md` remains specific to N=8, q=1099511627873, and t=17; it is not the basis of the N=8192 result. The integrated RNS proof covers one multiplication and one relinearization only. Its exact-rational audit passed CI run 288 on code commit `92542f5ca42a761445512e59db4bacf26e851eaa`; independent proof review remains pending. No arbitrary-depth theorem is claimed.

## 6. Gate checklist

- [x] OS-backed entropy source wired into experimental sampler.
- [x] Unbiased per-lane uniform rejection sampler.
- [x] Explicit ternary secret and eta=2 error distributions.
- [x] Evaluation-key phase relation tested; exhaustive coefficient test included.
- [x] Secret buffer zeroization on wrapper drop, with direct buffer test.
- [ ] Execute the pinned unstructured-LWE diagnostic and obtain ring-aware independent cryptographic review.
- [x] Document the evaluation-key sample relation and its conditional key-switch noise bound.
- [ ] Analyze the security impact of the structured, related evaluation-key samples (multi-target RLWE, chosen-message/auxiliary-input exposure, and applicable ring-specific attacks); the current LWE proxy deliberately does not include these samples.
- [ ] Constant-time and side-channel audit.
- [x] Integrated RNS encryption/decryption with centered input lifts and exact integer tensor products.
- [x] One-multiplication RNS noise derivation and exact-rational audit script added.
- [x] Exact-rational RNS noise audit passed CI run 288 on the proof commit; the later CI run 311 also completed successfully on the updated branch head.
- [ ] Independent cryptographic review and reproducibility of the security/correctness analysis.

Until every relevant gate is passed, describe the work as an experimental RNS arithmetic/key-generation prototype, not as a secure or publication-validated FHE scheme.


## Structured evaluation-key model

See `PAPER1/EVALUATION_KEY_SECURITY_ANALYSIS.md` for the joint related-secret formulation of the evaluation-key transcript, implementation-grounded decomposition bounds, and unresolved algebraic attack questions. The 14 equations are not ordinary independent RLWE samples; the known scalar sequence `B^j` and dependent secret pair `(s,s^2)` must be modeled jointly with the public-key sample. No concrete security estimate is established.
