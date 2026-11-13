# An Experimental RNS-BFV Implementation with Exact Integer-Lift Multiplication and Reproducible Correctness Audits

**Manuscript status:** working draft for internal development; not submission-ready. The abstract and novelty claims must be revisited after related-work analysis, independent review, SageMath estimation, and release benchmarking.

## Abstract (provisional)

This work presents an experimental implementation and correctness study of a leveled Ring-LWE-based BFV prototype using a four-lane residue number system (RNS) representation at polynomial degree N=8192. The multiplication reference path lifts ciphertext components to centered integers, computes negacyclic tensor products through an auxiliary NTT/CRT basis, and retains the integer quotient information required for coefficientwise BFV scale-and-round. Deterministic audits check arithmetic identities, auxiliary reconstruction range, and a conservative noise bound for one multiplication followed by relinearization. The public evaluation-key format is analyzed as a structured collection of related-secret equations involving (s,s^2), for which no concrete security estimate is claimed. Small-degree exhaustive and meet-in-the-middle experiments are included only as algorithmic diagnostics. The implementation is an experimental correctness prototype: it does not establish a concrete Ring-LWE security level, arbitrary multiplicative depth, side-channel resistance, or production performance.

## 1. Introduction

Fully homomorphic encryption requires arithmetic over polynomial rings together with careful control of ciphertext noise. Implementations based on BFV commonly combine number-theoretic transforms, residue number systems, gadget decomposition, and relinearization. The interaction between integer representatives, quotient information, and scale-and-round is particularly important in multiplication: reducing an intermediate tensor product modulo the ciphertext modulus before scaling can discard information needed by the intended BFV operation.

This paper studies an experimental leveled RNS-BFV implementation and emphasizes auditable correctness rather than a premature performance or security claim. Its central engineering choice is an exact integer-lift multiplication reference path: centered ciphertext components are multiplied over the integer negacyclic ring using an auxiliary NTT/CRT basis whose product range is checked before reconstruction and scale-and-round.

The paper also records a structured security issue in the evaluation-key transcript. The published relations have the form b_j+a_j s=B^j s^2+e_j (mod Q). These are not simply additional independent ordinary RLWE samples: the target s^2 is related to the same secret s. We therefore keep the security assessment separate from the implementation correctness evidence.

### Contributions and scope

The defensible contributions investigated here are:

1. An experimental four-lane RNS arithmetic implementation targeting N=8192, with candidate NTT parameters, CRT reconstruction, centered basis extension, and modular reduction routines.
2. An exact integer-lift BFV tensor-multiplication reference path using an auxiliary NTT/CRT basis and coefficientwise scale-and-round.
3. Executable arithmetic and noise audits, including a deterministic one-multiplication-plus-relinearization correctness bound under the specified bounded samplers.
4. An explicit joint-transcript formulation for the structured evaluation key and a careful statement of what current unstructured-LWE proxy analysis does not cover.
5. Reproducible small-parameter exhaustive and MITM candidate-search diagnostics, with exact candidate-set comparisons.

These claims describe implementation and validation work. A literature comparison is still required to establish novelty relative to existing BFV/RNS implementations.

## 2. Mathematical and cryptographic setting

Let R_Q=Z_Q[X]/(X^N+1), with N=8192 for the implementation target. The prototype uses a four-lane RNS representation of the ciphertext modulus, plaintext modulus t=65537, ternary secret coefficients, and centered-binomial error coefficients supported on [-2,2]. The relinearization gadget uses base B=2^16 and L=14 levels.

The public-key relation is b_pk+a_pk s=e_pk (mod Q), with sign convention as implemented. The evaluation-key relations are b_j+a_j s=B^j s^2+e_j (mod Q). Each a_j is sampled uniformly in the RNS representation and each error coefficient follows the specified eta=2 bounded distribution.

**Parameter table to complete:** list every RNS prime, their product Q, NTT roots, plaintext modulus, gadget base and level count, sampler distributions, and exact implementation revision. Values must be checked against the source and parameter audit before submission.

## 3. Implementation architecture

The implementation separates modular arithmetic, negacyclic polynomial operations, RNS/CRT conversion, key generation, encryption/decryption, and evaluation-key operations. Four RNS lanes represent the ciphertext modulus. Candidate NTT primes and roots are checked by deterministic parameter audits. CRT reconstruction and centered basis extension are implemented explicitly.

The tensor multiplication path is a correctness reference. It lifts each ciphertext component to its centered integer representative, forms the three integer negacyclic tensor components, computes their coefficients using an auxiliary NTT/CRT basis, reconstructs the exact integer coefficients, and only then applies coefficientwise t/Q scale-and-round. For each individual negacyclic product, the auxiliary basis product is checked to exceed twice the worst-case coefficient bound. The cross component is formed by two separately reconstructed exact products, whose signed BigInt coefficient vectors are added only after reconstruction; therefore no combined two-product coefficient is passed through the smaller single-product CRT bound. This design preserves the quotient information that would be lost by prematurely reducing the tensor product modulo Q.

## 4. Correctness argument for one multiplication and relinearization

The public-key encryption phase error is bounded coefficientwise by E0=4N+2=32770 under the specified ternary and eta=2 samplers. The multiplication analysis bounds the integer tensor coefficients, the quotient/carry contribution, scale bias, cross terms, input-error product, and scale-rounding residuals. The relinearization error is bounded using the centered gadget-digit magnitude and the l1 norm of each bounded error polynomial.

The executable exact-rational audit reports a total error upper bound of 91,700,891,552,753,113,897 and a decoding margin of approximately 3.2138270414e60 for the stated parameter instance. The auxiliary CRT product is 468 bits and is checked against twice the worst-case tensor coefficient bound.

This argument covers one multiplication followed by one relinearization only. It does not establish arbitrary multiplicative depth. The proof and its centered-lift quotient handling require independent mathematical review before publication.

## 5. Evaluation-key structure and security limitations

The evaluation-key transcript contains fourteen equations sharing the same secret s and related target s^2. It is therefore not justified to count them as fourteen ordinary independent RLWE samples or to apply an unstructured-LWE estimator to them without a valid distributional argument.

Adjacent-level subtraction cancels the formal s^2 target, but creates correlated transformed errors. The exact identity and covariance structure are documented in PAPER1/EVALUATION_KEY_SECURITY_ANALYSIS.md. This algebraic observation is not, by itself, a demonstrated attack or security reduction.

The pinned lattice-estimator diagnostic has not yet been executed in a SageMath environment. Even if executed, the current unstructured-LWE proxy would not cover the structured evaluation-key samples or prove Ring-LWE security. No concrete bit-security claim is made.

## 6. Implementation validation

The validation suite includes Rust unit and integration tests, formatting, Clippy, benchmark-target compilation, and deterministic Python audits. The audits cover candidate parameters, AsymRed, negacyclic arithmetic, toy and N=8192 noise bounds, ternary-square parity, split-secret square identities, exhaustive toy evaluation-key candidate search, and MITM candidate-set equality.

The CI workflow runs Rust unit tests, formatting, Clippy, benchmark-target compilation, and the Python arithmetic audits. The last fully completed validation before the present proof-documentation refinements passed on commit 4800c0dc279c17bbfb0f7aca8a1f6e820645b1d4, including the N=8192 noise audit, adaptive-selector parameter-grid audit, and held-out selector experiment. CI for the current proof refinements is running; its result must be recorded against the exact final manuscript commit before this section is frozen.

## 7. Toy meet-in-the-middle diagnostics

The toy MITM experiment splits an even-degree ternary candidate into two halves and hashes right-half public-key contributions on selected coefficient coordinates. It enumerates bounded error patterns on those coordinates, then verifies the full public-key and evaluation-key residuals. For N=4,6,8, the candidate set matched exhaustive enumeration in all 90 original deterministic trials.

The evaluation-key residual under the split contains the cross term 2 X^(N/2) u v. This term couples the halves, so independent half-list evaluation-key hashes are not valid unless the cross term is represented exactly. The current MITM method therefore uses the public-key relation for joining and applies evaluation-key constraints after each pair is retrieved. It does not claim production-parameter key recovery or security impact.

The adaptive coordinate selector uses a heuristic cost proxy. A frozen lambda=4 selector was tested on ten held-out toy instances per degree at q=11 and eta=2, using seed 0xC0FFEE. It selected k=(1,2,2) for N=(4,6,8), matching the fastest fixed-k median in this sample; median regret was 1.000 at each degree. This is a small-sample toy result, not evidence of generalization across q, eta, or production dimensions.

## 8. Performance evaluation

No headline performance claim is currently supported. CI compiles the Criterion benchmark target but does not run a release benchmark campaign. A publishable evaluation must compare equivalent operations and parameters, use release builds, record CPU/compiler/OS/source metadata, preserve raw samples, repeat independent sessions, and report dispersion or confidence intervals. Setup/key-generation time must be separated from steady-state operations. Debug or CI timings must not be used as headline results.

## 9. Limitations and responsible claims

- No concrete Ring-LWE security level or 128-bit security claim.
- No independent cryptanalytic review of the joint public/evaluation-key transcript.
- No arbitrary multiplicative-depth proof, modulus switching, or bootstrapping.
- No production-optimized BFV multiplication or release benchmark campaign.
- No constant-time, side-channel-resistance, or comprehensive memory-remanence claim.
- No production-parameter attack demonstrated by the toy exhaustive/MITM experiments.
- No independent review of the multiplication/noise proof completed yet.

## 10. Conclusion

This work provides an auditable experimental RNS-BFV implementation and a set of deterministic correctness checks, with particular attention to exact integer-lift multiplication and the structured evaluation-key transcript. The current evidence supports a bounded correctness statement and reproducible toy diagnostics, not a concrete security level or production-readiness claim. Independent mathematical and cryptanalytic review, estimator execution with careful scope, release benchmarking, and a related-work comparison remain necessary before submission.

## References

**To complete:** add primary BFV, RNS/NTT, lattice-estimator, and homomorphic-encryption-standard references. Verify bibliographic metadata and ensure every claim is supported by an appropriate primary source.