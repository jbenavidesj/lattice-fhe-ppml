# Paper 1 — benchmark protocol

No headline performance result is asserted by this protocol.

## Comparisons
Compare the same mathematical operation and input distribution across:
1. a simple auditable reference (canonical remainder or schoolbook negacyclic multiplication);
2. the optimized candidate (AsymRed or NTT/RNS path);
3. where appropriate, a recognized implementation with matching semantics and parameters.

Do not compare different ring dimensions, modulus sizes, security levels, operation counts, or compiler settings as if equivalent.

## Environment and procedure
Record CPU model/microarchitecture, cores, memory, OS/kernel, Rust compiler, target triple, optimization flags, dependency lockfile, source revision, command line, thread settings, and thermal/frequency conditions where available.

Use release builds. Perform multiple independent sessions. Report median and dispersion/confidence intervals, sample counts, and raw results. Separate setup/key generation from steady-state evaluation.

## Required groups
- AsymRed versus canonical remainder, same valid input range.
- Modular add/subtract/multiply.
- Forward/inverse negacyclic NTT.
- Schoolbook versus NTT polynomial multiplication.
- RNS basis conversion and CRT reconstruction.
- BFV encryption/decryption/multiplication/relinearization only after full-pipeline correctness tests.

## Reporting rules
- CI is for build and correctness gates, not headline performance.
- A debug-mode timing is not publishable benchmark evidence.
- A microbenchmark improvement is not an end-to-end BFV improvement.
- Do not claim 34% or any other speedup without repeated release measurements and statistical reporting.

## First release-mode benchmark campaign (single CI session)

A first end-to-end Criterion release run completed successfully on source commit
be820f044647e8e2444d5e415503172bb1498a6f, workflow run #3
(43351911212). The workflow recorded environment metadata and uploaded the raw
Criterion tree and logs as artifact
paper1-release-benchmarks-be820f044647e8e2444d5e415503172bb1498a6f
(artifact ID 14004805733).

Environment: GitHub-hosted Azure Linux VM, Linux kernel 7.0.0-1017-azure,
x86_64, virtualized AMD EPYC 9V74, 4 visible vCPUs, approximately 16 GiB RAM;
rustc/cargo 1.100.0, LLVM 23.1.5. Run timestamp: 2026-11-13 02:24 UTC.
These are virtualized CI measurements, not bare-metal measurements. CPU
frequency, co-tenancy, and thermal state were not controlled.

Criterion estimates from this one session (point estimate and reported 95%
confidence interval; intervals are within-run statistical estimates, not
between-machine or between-session uncertainty):

| Operation | Estimate | 95% CI |
|---|---:|---:|
| AsymRed, 20,000 reductions per iteration | 170.20 µs | 169.85–170.67 µs |
| u128 remainder baseline, same 20,000 inputs | 38.52 µs | 38.285–38.840 µs |
| Four-lane RNS negacyclic NTT multiplication, N=8192 | 6.948 ms | 6.938–6.969 ms |
| Exact-reference BFV tensor multiplication, N=8192, t=65537 | 415.90 ms | 415.06–416.73 ms |
| BFV encryption, N=8192, t=65537 | 22.460 ms | 22.449–22.470 ms |
| BFV decryption, N=8192, t=65537 | 54.348 ms | 54.314–54.418 ms |
| BFV addition, N=8192, t=65537 | 163.37 µs | 163.02–163.88 µs |
| BFV multiply plus relinearization, exact-reference path | 685.83 ms | 685.48–686.20 ms |
| Relinearization-key generation, N=8192 | 375.69 ms | 375.42–376.04 ms |

The AsymRed candidate is about 4.42x slower than the canonical u128 remainder
baseline in this specific same-input microbenchmark. This is a negative result:
the current AsymRed implementation should not be described as a speed
optimization on this evidence. It may still be useful as an exact arithmetic
candidate, but any performance rationale requires redesign and repeat testing.

The tensor multiplication and multiply/relinearize numbers characterize the
current exact auxiliary NTT/CRT plus BigInt correctness-reference path; they
must not be generalized to an optimized BFV implementation. Encryption,
decryption, and key-generation timings are also implementation- and
environment-specific.

This is one CI session with one machine allocation. The reported Criterion
confidence intervals do not replace multiple independent sessions, another
machine, raw-data analysis across sessions, or controlled frequency settings.
Accordingly, these results are a reproducible baseline and diagnostic, not a
headline performance evaluation or a claim of competitiveness. The raw
artifact should be retained with the manuscript's source revision.

A second independent session, bare-metal comparison, broader primitive groups
(modular add/sub/multiply, forward/inverse NTT, basis conversion/CRT, and
schoolbook-vs-NTT), and a recognized BFV implementation with matching semantics
remain future work.
