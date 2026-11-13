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

A bounded diagnostic unstructured-LWE script is provided at `scripts/estimate_lwe_proxy.py`. It pins lattice-estimator commit `7d59f866655362ea8eab803dbc833710c2bc362a`. The recorded SageMath 10.10 run used `LWE.estimate.rough()` with ADPS16/GSA assumptions and m=N=8192; it reports minimum log2(rop)=93.732 for the candidate and 97.236 for the HE Standard v2 comparison profile. Full output and parameters are recorded in `PAPER1/SECURITY_ESTIMATION_RESULTS.md`. These are conditional scalar unstructured-LWE proxy outputs only, not a Ring-LWE estimate, security lower bound, or scheme-level security claim. They do not model the evaluation-key samples targeting s^2, nor the joint ring-structured transcript. The candidate's larger Q and narrower eta=2 error are reasons for further analysis, not grounds for inferring security.

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
- [x] Execute and record the pinned rough-profile unstructured-LWE proxy diagnostic; it is explicitly not a Ring-LWE estimate.\n- [ ] Obtain ring-aware independent cryptographic review.
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


## Status reconciliation (2026-11-13)

The older statements above that the estimator had not yet been run are superseded by `PAPER1/SECURITY_ESTIMATION_RESULTS.md`. The run produced only the bounded unstructured-LWE proxy outputs described there. The structured evaluation-key transcript remains unanalyzed by a validated ring-aware security model and requires specialist review. The one-multiplication noise derivation has passed internal source-to-proof consistency checks and exact-rational CI audit, but has not received independent mathematical certification.


## Completed CI #851 transcript diagnostics (2026-11-13)

The current branch head `dc484e496ee9deda1ce8ec256b60e4848b89ba5f` passed all three CI jobs in workflow run #851 (ID 43527761531), including the pinned SageMath job. The SageMath artifact is `sage-lwe-proxy-diagnostic` (artifact ID 14086391421; SHA-256 `a2ac2f4f992c3486869705e32230bc3d767108872bc3ff2b79d3d762a641ae22`).

The run reproduced the rough scalar unstructured-LWE proxy output `log2(rop)=93.7320` (ADPS16/GSA; pinned estimator commit `7d59f866655362ea8eab803dbc833710c2bc362a`; SageMath 10.10). The script explicitly excludes evaluation-key samples. This output is not a Ring-LWE estimate, not a security lower bound, and not a scheme-level security claim.

Additional exact/transcript diagnostics completed:

- The transformed eta=2 evaluation-key error vector has exact tridiagonal covariance: diagonal 4,294,967,297, adjacent covariance -65,536, and zero non-adjacent covariance in the displayed 13-coordinate representation. Exact positive-definiteness check passed. The joint characteristic function retains the shared underlying-error dependence.
- The weighted modular-kernel search found exact short relations, including the adjacent-level baseline (L1=65,537; support radius 131,074) and longer non-adjacent combinations. Every reported relation satisfies the modular cancellation identity. These are correlated transformations of one transcript, not independent samples.
- Exact transformed candidate constraints agreed with the original constraints in all tested toy cases. Coarse approximations sometimes retained extra candidates, which is why they cannot replace exact feasibility checks.
- The ternary-transcript MILP and exhaustive oracle produced identical feasible sets in all tested unique and ambiguity-stress toy cases, including checks with redundant parity constraints.

These results improve the transcript's algebraic and finite-toy-model characterization. They do not provide a production-parameter secret-recovery attack, a ring-aware security estimate, or a proof of security. Independent specialist cryptanalysis of the joint public/evaluation-key transcript remains mandatory; the candidate must not be assigned a concrete security level from this CI run.
