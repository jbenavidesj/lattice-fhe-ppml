# Paper 1 — validation status

**Status: research prototype / not submission-ready.** This document separates established design facts, previously reported computational checks, and work that remains unverified.

## Selected architecture

- Core: leveled RNS-BFV; bootstrapping/refresh is a separate experimental extension, not a required part of the core construction.
- Candidate optimizations: AsymRed modular reduction, negacyclic NTT, RNS arithmetic, lazy relinearization and adaptive noise/error tracking.
- These are design choices and candidates, not evidence of a faster or more secure scheme.

## Evidence currently available in the research record

The prior development record reports the following Python checks:
- candidate modulus primality and congruence checks, plus exact-order checks for the proposed negacyclic NTT roots;
- differential testing of AsymRed against the language remainder operation (reported total: 800,156 cases);
- negacyclic multiplication checks (reported total: 2,800 polynomial products);
- NTT multiplication and round-trip checks (reported total: 320 products and 320 round trips).

These counts are historical reports, not a fresh execution performed by this commit. The corresponding scripts, raw logs, tool versions, and reproducible commands must be present in the repository before these results are treated as independently reproducible evidence.

## Not established

The following claims must not be presented as demonstrated results:
- any measured speedup, including 34%, 34.2%, or a 4.12 ms versus 2.71 ms comparison;
- 128-bit security or any other concrete security level;
- constant-time execution;
- a proven reduction in cryptographic noise from AsymRed;
- a fully integrated and tested BFV encryption/evaluation/decryption pipeline;
- a validated bootstrapping/refresh implementation.

AsymRed is an exact modular-reduction candidate. Exact modular arithmetic does not, by itself, reduce BFV noise.

## Repository status at this revision

The default branch previously contained only the top-level README and STABILITY note. No Cargo manifest or Rust source tree was visible at the time this validation branch was prepared. Therefore Rust compilation, unit tests, clippy, Criterion benchmarks, and CI have **not** been run from this repository.

## Minimum gates before IEEE submission

1. Commit the complete Rust crate and Python reference/audit scripts.
2. Re-run all Python checks from a clean environment and preserve logs, versions, seeds, and commands.
3. Compile and test the Rust implementation on a documented toolchain.
4. Independently verify the BFV scale-and-round, key switching/relinearization, decryption correctness, and noise bounds for the exact parameter set.
5. Run benchmarks against clearly specified baselines on documented hardware; publish raw measurements and statistical summaries.
6. Perform a current lattice-security estimate using the exact secret/error distributions and complete parameter set.
7. Audit side-channel behavior before making any constant-time claim.

Until these gates are met, describe the work as a candidate architecture and reproducibility effort, not as a validated new FHE scheme.
