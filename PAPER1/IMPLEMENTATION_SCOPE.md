# Paper 1 implementation scope and evidence ledger

## Added in this branch
- Rust arithmetic crate: modular operations, AsymRed candidate, schoolbook negacyclic multiplication, twisted iterative negacyclic NTT, four-lane RNS polynomial storage/addition/NTT multiplication, exact CRT reconstruction, centered CRT reconstruction, and exact centered basis extension into a supplied target basis.
- A separately namespaced tiny-ring BFV model with deterministic demonstration key generation, public-key encryption, decryption, and homomorphic ciphertext addition tests.
- Python parameter audit with deterministic Miller-Rabin for unsigned 64-bit candidates.
- Python arbitrary-precision differential test for AsymRed.
- Small-ring independent polynomial reference checks.
- Criterion microbenchmark comparing AsymRed and u128 remainder; it is compiled in CI but not used to assert a speedup.

## BFV model scope and limitations
The module `src/bfv/toy.rs` is a tiny-ring correctness model, not a complete or secure BFV implementation and not an implementation of the N=8192 RNS candidate parameters. It uses deterministic XorShift sampling and tiny ternary error solely for reproducible tests. It implements key generation, encryption, decryption, ciphertext addition, and an unrelinearized three-component tensor multiplication with coefficient-wise BFV scale-and-round. The mathematical contract and limitations are recorded in `PAPER1/BFV_TOY_SPEC.md`.

The toy gadget relinearization and one-multiplication correctness proof are deterministic correctness experiments only. Production-grade key switching, modulus switching, arbitrary-depth noise management, and bootstrapping are absent. The toy proof has not been established for the N=8192 RNS basis. No security, production-readiness, or performance claim is made.

## Arithmetic-layer caveats
The RNS basis-extension routine is a correctness-oriented BigInt reference: it reconstructs the signed representative in (-Q/2,Q/2] and reduces it into the target moduli. It is not an approximate fast base-conversion algorithm, nor does it implement BFV modulus switching or a complete RNS modulus chain.

## Correctness and benchmark caveats
AsymRed checks 0 <= z < q^2, checks intermediate arithmetic, and rejects any case where the two-fold result is not below 2q. This fails closed if the range lemma does not hold. Tests must pass before relying on the lemma in the paper.

The Criterion benchmark harness is exploratory and currently only compiled by CI; no release benchmark campaign, raw timing dataset, confidence intervals, CPU/compiler metadata, or end-to-end BFV measurement has been published. It cannot support a speedup claim.

## Security caveats
No RLWE estimator, concrete security level, constant-time audit, memory-zeroization review, or side-channel evaluation is included. The NTT is a correctness-oriented prototype, not an optimized or audited implementation.
