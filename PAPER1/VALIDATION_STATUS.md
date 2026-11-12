# Paper 1 — validation status

**Status: experimental RNS-BFV research prototype; not submission-ready.**

The selected architecture remains leveled RNS-BFV as the core, with refresh/bootstrapping kept as a separate future extension.

## Implemented

- Four-lane RNS arithmetic for N=8192, candidate NTT primes and roots, exact CRT reconstruction, centered basis extension, and AsymRed modular reduction.
- Exact integer-lift BFV tensor multiplication: ciphertext components are lifted to centered integers, integer negacyclic products are computed with a nine-prime auxiliary NTT/CRT basis, and only then is coefficientwise t/Q scale-and-round applied. This preserves the integer product quotient required by the BFV multiplication convention.
- Experimental OS-CSPRNG-backed ternary secret and eta=2 centered-binomial error samplers; unbiased per-lane uniform R_Q sampling.
- RNS public-key generation, encryption, decryption, and homomorphic addition.
- Evaluation-key generation, exhaustive coefficientwise phase-relation tests, gadget decomposition, and relinearization.
- Multiply-then-relinearize RNS-BFV API and an N=8192 integration test comparing the decrypted result with an independent sparse negacyclic plaintext-ring product.
- Secret-key wrapper zeroization on drop. This does not erase all possible temporary copies and is not a side-channel audit.

## Mathematical validation

- The public-key encryption phase error has deterministic coefficient bound E0 = 4N+2 = 32770 for the specified bounded samplers.
- The conditional key-switch contribution bound is 15,032,156,160 for eta=2, N=8192, B=2^16, and L=14.
- A deterministic one-multiplication-plus-relinearization noise derivation is documented in `PAPER1/RNS_BFV_MULTIPLICATION_NOISE_PROOF.md`.
- The exact-rational audit script `scripts/audit_rns_bfv_noise.py` computes a total error upper bound of 91,700,891,552,753,113,897 and compares it with a decoding margin of approximately 3.2138270414e60.
- The nine-prime auxiliary NTT/CRT product is 468 bits and is checked to exceed twice the worst-case integer tensor coefficient bound (N(Q/2)^2).
- The proof covers one multiplication and one relinearization only. It does not establish arbitrary multiplicative depth.

## Reproducible validation

CI run 272 on code commit `47ee02f2e87a7dd7ab4fd7731ed5583e78d63ddb` completed successfully:
- 32 Rust unit tests passed, including encryption/decryption, addition, tensor-phase decryption, and multiply/relinearize comparison against the sparse plaintext oracle.
- Rust formatting passed.
- Clippy passed with warnings denied.
- Benchmark target compilation passed.
- Python arithmetic audits passed, including the auxiliary NTT prime/root and CRT-range audit.

CI run 288 on code commit `92542f5ca42a761445512e59db4bacf26e851eaa` completed successfully with the new exact-rational RNS-BFV noise audit included. Both CI jobs passed: all 32 Rust unit tests, formatting, Clippy, benchmark-target compilation, and all Python arithmetic/noise audits.

## Not established

- A concrete RLWE security estimate or 128-bit security claim.
- Independent cryptographic review or a proof against ring-structure attacks.
- Constant-time behavior, side-channel resistance, or comprehensive memory-remanence protection.
- Arbitrary multiplicative depth, modulus switching, or bootstrapping.
- A production-optimized RNS tensor multiplication and scale-and-round implementation; the current exact auxiliary NTT/CRT and BigInt path is a correctness reference.
- Release benchmark measurements, raw timing datasets, confidence intervals, documented hardware/compiler metadata, or any speedup claim.
- IEEE submission readiness.

AsymRed is exact modular reduction; it does not intrinsically reduce cryptographic noise. The tiny-ring BFV module uses deterministic test-only sampling and must never protect real data.

## Remaining gates

1. Pass the newly added exact-rational RNS noise audit in CI on the current branch head.
2. Obtain an independent review of the one-multiplication derivation, especially centered-lift quotient handling and the decoding-margin argument.
3. Run and record a current lattice-estimator diagnostic with immutable estimator version, attack model, and cost assumptions; assess the ring-LWE heuristic and structural attacks.
4. Replace the correctness-reference multiplication with an optimized, proven RNS implementation only after differential validation against the exact reference.
5. Run release benchmarks with repeated samples and complete hardware/compiler metadata.
6. Review secret-dependent control flow, memory access, temporary copies, and side-channel exposure.

Until these gates are passed, describe the work as an experimental RNS-BFV prototype with a one-multiplication correctness argument—not as a production-secure or fully validated new FHE scheme.
