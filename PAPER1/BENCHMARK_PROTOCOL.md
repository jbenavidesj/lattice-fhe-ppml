# Paper 1 — benchmark protocol

No performance result is asserted by this document. It defines the evidence required before reporting one.

## Implementations to compare

Compare the same mathematical operation and input distribution across:
1. a simple, auditable reference implementation (for example, canonical remainder reduction or schoolbook negacyclic multiplication);
2. the optimized candidate (AsymRed or NTT/RNS path);
3. where appropriate, a recognized external implementation with matching parameters and semantics.

Do not compare different security levels, ring dimensions, modulus sizes, operation counts, or compiler settings as if they were equivalent.

## Build and execution conditions

Record:
- CPU model, microarchitecture, core count, memory, operating system and kernel;
- Rust compiler version, target triple, optimization flags, dependency lockfile and crate versions;
- benchmark source revision and exact command line;
- thread pinning/parallelism, frequency governor, thermal state where available;
- Criterion warm-up, measurement time, sample size, and outlier policy.

Use release builds. Run multiple independent benchmark sessions. Report distributions (median and dispersion or confidence intervals), not only a best-case timing. Preserve raw Criterion output.

## Required benchmark groups

- modular reduction: AsymRed versus canonical remainder, with identical valid input range;
- modular add/subtract and multiplication;
- forward/inverse negacyclic NTT;
- polynomial multiplication: schoolbook versus NTT, with identical ring and modulus;
- RNS basis operations and CRT reconstruction;
- BFV encryption, decryption, multiplication, and relinearization only after the full pipeline is implemented and correctness-tested.

Measure setup/key-generation separately from steady-state evaluation. Include allocation and serialization costs only when explicitly identified.

## Reporting rules

- A GitHub Actions runner is suitable for compile/test automation, not for a headline performance claim.
- Never infer a general speedup from one machine or one run.
- Publish baseline and candidate timings, sample counts, variability, hardware and compiler metadata.
- Do not claim a 34% speedup unless a reproducible benchmark directly supports that exact comparison.
- A microbenchmark speedup for modular reduction or NTT is not an end-to-end BFV speedup.

## Current status

The repository revision inspected before this branch did not contain a Cargo manifest or Rust source tree. No Rust benchmark could therefore be run from the repository at that point. Add the complete crate first, then execute this protocol and attach raw results.
