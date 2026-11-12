# Paper 1 implementation scope and evidence ledger

## Added in this branch
- Rust arithmetic crate (with pinned BigInt/benchmark dependencies): modular operations, AsymRed candidate, schoolbook negacyclic multiplication, twisted iterative negacyclic NTT, and four-lane RNS polynomial storage/addition/NTT multiplication.
- Python parameter audit with deterministic Miller-Rabin for unsigned 64-bit candidates.
- Python arbitrary-precision differential test for AsymRed.
- Small-ring independent polynomial reference checks.
- Criterion microbenchmark comparing AsymRed and u128 remainder; it is compiled in CI but not used to assert a speedup.

## Not implemented
RNS lane arithmetic and exact per-coefficient CRT reconstruction are implemented. RNS basis extension is not. This is not a complete BFV implementation. Key generation, encryption, decryption, ciphertext multiplication, BFV scale-and-round, gadget decomposition, relinearization, modulus switching, noise tracking, and bootstrapping are not implemented. It is not production cryptography.

## Correctness and benchmark caveats
AsymRed checks 0 <= z < q^2, checks intermediate arithmetic, and rejects any case where the two-fold result is not below 2q. This fails closed if the range lemma does not hold. Tests must pass before relying on the lemma in the paper.

The Criterion benchmark harness is exploratory and currently only compiled by CI; no release benchmark campaign, raw timing dataset, confidence intervals, CPU/compiler metadata, or end-to-end BFV measurement has been published. It cannot support a speedup claim.

## Security caveats
No RLWE estimator, concrete security level, constant-time audit, memory-zeroization review, or side-channel evaluation is included. The NTT is a correctness-oriented prototype, not an optimized or audited implementation.
