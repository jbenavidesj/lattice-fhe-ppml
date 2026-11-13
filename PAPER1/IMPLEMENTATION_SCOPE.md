# Paper 1 implementation scope and evidence ledger

## Added in this branch
- Rust arithmetic crate: modular operations, AsymRed candidate, schoolbook negacyclic multiplication, twisted iterative negacyclic NTT, four-lane RNS polynomial storage/addition/NTT multiplication, exact CRT reconstruction, centered CRT reconstruction, exact centered basis extension, BFV t/Q scale-and-round, three-component tensor multiplication, signed gadget decomposition, and exact-reference gadget relinearization.
- A separately namespaced tiny-ring BFV model with deterministic demonstration key generation, public-key encryption, decryption, homomorphic addition, centered-lift integer tensor multiplication, and gadget relinearization tests.
- An exact-rational worst-case correctness audit for one multiplication plus relinearization in the tiny-ring BFV model, including input-noise, lift-quotient, scale-bias, cross-term, rounding, and key-switch contributions.
- Experimental CSPRNG-backed RNS key generation with unbiased per-lane rejection sampling, ternary secret, eta=2 centered-binomial evaluation-key errors, exhaustive phase-relation tests, and secret-wrapper zeroization.
- Python parameter audit with deterministic Miller-Rabin for unsigned 64-bit candidates.
- Python arbitrary-precision differential test for AsymRed.
- Small-ring independent polynomial reference checks.
- Criterion microbenchmark comparing AsymRed and u128 remainder; it is compiled in CI but not used to assert a speedup.

## BFV model scope and limitations
The module `src/bfv/toy.rs` is a tiny-ring correctness model, not a complete or secure BFV implementation and not an implementation of the N=8192 RNS candidate parameters. It uses deterministic XorShift sampling and tiny ternary error solely for reproducible tests. It implements key generation, encryption, decryption, ciphertext addition, centered-lift integer tensor multiplication with coefficient-wise BFV scale-and-round, and toy gadget relinearization. The mathematical contract and limitations are recorded in `PAPER1/BFV_TOY_SPEC.md`.

The toy gadget relinearization and one-multiplication correctness proof are deterministic correctness experiments only; the latter is audited by `scripts/audit_toy_bfv_noise.py` using exact rational arithmetic. Production-grade key switching, modulus switching, arbitrary-depth noise management, and bootstrapping are absent. The toy proof has not been established for the N=8192 RNS basis. No security, production-readiness, or performance claim is made.

## Arithmetic-layer caveats
The RNS BFV relinearization accepts evaluation-key digit pairs satisfying b_j+a_j*s=B^j*s^2+e_j (mod Q). An experimental CSPRNG-backed generator now constructs such digits, but the construction has no ring-aware security estimate, independent cryptographic review, constant-time audit, or full BFV-RNS noise proof. Its gadget decomposition and key-switch accumulation remain correctness-oriented references. The RNS basis-extension and scale-and-round routines are correctness-oriented BigInt references: it reconstructs the signed representative in (-Q/2,Q/2] and reduces it into the target moduli. It is not an approximate fast base-conversion algorithm, nor does it implement BFV modulus switching or a complete RNS modulus chain.

## Correctness and benchmark caveats
AsymRed checks 0 <= z < q^2, checks intermediate arithmetic, and rejects any case where the two-fold result is not below 2q. This fails closed if the range lemma does not hold. Tests must pass before relying on the lemma in the paper.

A single release-mode Criterion session was collected in virtualized GitHub Actions CI and is documented in `PAPER1/BENCHMARK_PROTOCOL.md` and the manuscript, with raw artifact and environment metadata. It is a descriptive baseline only, not a multi-session campaign or evidence of competitiveness. The exact auxiliary NTT/CRT plus BigInt tensor multiplication is a correctness-reference path. AsymRed was about 4.42x slower than the u128 remainder baseline in the measured microbenchmark; no speedup is claimed.

## Security caveats
A pinned rough-profile scalar unstructured-LWE proxy diagnostic is recorded in `PAPER1/SECURITY_ESTIMATION_RESULTS.md`; it is not a ring-aware RLWE estimate and does not model the structured evaluation-key transcript. No concrete security level, constant-time audit, comprehensive memory-zeroization review, or side-channel evaluation is included. The secret-key wrapper zeroizes its owned RNS buffers on drop, but temporary copies and other memory remnants are not comprehensively controlled. The NTT is a correctness-oriented prototype, not an optimized or audited implementation.


## Editorial closure update (2026-11-13)

The manuscript's internal scope, claim discipline, bibliography [1]–[8], focused BEHZ/HPS comparison, and descriptive benchmark interpretation have been consolidated. The remaining items are external mathematical/cryptanalytic reviews and IEEE production typesetting; they are not missing code-validation tasks. The exact current status is recorded in `PAPER1/VALIDATION_STATUS.md`.
