# Toy meet-in-the-middle prototype

## Purpose

This prototype implements a two-list join for the small noisy negacyclic toy model. It tests algorithmic correctness and candidate-set equivalence, not a practical attack against Paper 1 parameters.

## Method

For even degree N=2m, split a ternary candidate as t=u+X^m v. By linearity of multiplication by the public polynomial a_pk, the public-key residual is the sum of the left and right contributions plus b_pk.

The implementation:
1. Enumerates two lists of size 3^m, one for each half.
2. Hashes right-half contributions on two selected coefficient coordinates.
3. For each left-half entry, probes all 5^2 centered error values on those coordinates.
4. Verifies every retrieved pair against the complete public-key residual and all evaluation-key residuals.
5. Compares the resulting candidate set against full exhaustive enumeration.

The selected coordinates are only a filter. Full residual verification prevents false positives; every valid full residual is within [-2,2] on the selected coordinates, so the filter cannot discard a valid candidate.

## Reproducible toy results

The CI experiment uses q=11, base B=3, three evaluation-key levels, eta=2 errors, deterministic seed 0xBF2, and 30 trials at each even degree. The instrumented implementation applies evaluation-key residual checks sequentially and records the number of checks and rejections at each level.

| N | Exact candidate-set agreement | Median exhaustive time | Median staged MITM time | Observed speed ratio |
|---:|---:|---:|---:|---:|
| 4 | 30/30 | 0.000219 s | 0.000166 s | 1.32x |
| 6 | 30/30 | 0.002845 s | 0.000683 s | 4.17x |
| 8 | 30/30 | 0.036167 s | 0.003381 s | 10.70x |

Median candidate-flow diagnostics:

| N | Joined pairs | Full public residual passes | Evaluation-key checks by level | Rejections by level | Final survivors |
|---:|---:|---:|---:|---:|---:|
| 4 | 16 | 3.5 | [3.5, 1, 1] | [2.5, 0, 0] | 1 |
| 6 | 150 | 7.5 | [7.5, 1, 1] | [6.5, 0, 0] | 1 |
| 8 | 1356 | 11 | [11, 1, 1] | [10, 0, 0] | 1 |

Counts are medians across 30 trials and can therefore be fractional. The first evaluation-key level rejects most candidates that pass the full public-key residual test in these particular toy instances; later levels are then checked only for the remaining candidates. This is a verification-work reduction after the join, not a reduction in the number of joined pairs: the join still produces 16/150/1356 median pairs for N=4/6/8.

The exact candidate sets matched exhaustive enumeration in all 90 trials, and the planted secret was retained in every trial. Timings are single CI-run observations and are not formal benchmarks: no repeated-run confidence intervals, hardware normalization, or release-mode benchmark campaign is provided. The speed ratios apply only to these tiny toy parameters and must not be extrapolated to N=8192 or interpreted as a practical attack.

## Complexity and limitations

The two lists each contain 3^(N/2) entries, but the current implementation probes 5^k error patterns per left entry, where k=2 selected coordinates. It also stores full polynomial contributions and performs full candidate verification on bucket hits. This gives a useful toy speedup, but does not establish a scalable algorithm at large N.

The prototype joins on the public-key equation; evaluation-key equations are applied after a candidate pair is found. It does not yet exploit evaluation-key structure to reduce list sizes. Memory usage, collision behavior, optimal coordinate selection, and larger-degree scaling remain open.

## Reproduction

```bash
python scripts/toy_evalkey_mitm.py
```

The script uses only the Python standard library.
## Coefficientwise short-circuit experiment

A follow-up variant evaluates each coefficient of the public and evaluation-key residual directly and stops at the first coefficient outside the centered interval [-2,2]. This is algebraically exact: it changes only the order and amount of computation, not the acceptance condition. The implementation records the number of coefficient checks.

CI run #397's Python audit completed successfully, with exact candidate-set agreement in all 90 trials. The single-run timing observations were:

| N | Exhaustive median | Coefficientwise MITM median | Observed ratio |
|---:|---:|---:|---:|
| 4 | 0.000383 s | 0.000368 s | 1.04x |
| 6 | 0.004830 s | 0.001780 s | 2.71x |
| 8 | 0.063299 s | 0.011699 s | 5.41x |

The median coefficient checks for the evaluation-key equations, by level, were [9, 4, 4] at N=4, [16, 6, 6] at N=6, and [26, 8, 8] at N=8. Median public-residual coefficient checks were 56.5, 564, and 5173, respectively. These are diagnostic counts, not operation-normalized benchmarks.

The coefficientwise version retained exactness but did **not** improve the observed MITM timing ratios relative to the previous staged implementation (1.32x, 4.17x, and 10.70x in CI #391). The current implementation therefore remains an experiment, not an established optimization. The measurements are noisy single-run CI timings and do not isolate interpreter overhead; a dedicated repeated microbenchmark is needed before deciding whether to retain this strategy in the main path. The Rust CI job for run #397 was still compiling benchmarks when these Python results were recorded.

## Exact form of the evaluation-key residual under the half split

For \(N=2m\), write \(s=u+X^m v\), with \(\deg u,\deg v<m\). In the negacyclic ring,
\[
s^2=u^2+2X^muv-v^2.
\]
For evaluation-key level \(j\), the residual is therefore
\[
r_j(u,v)=b_j+a_ju+X^ma_jv-B^ju^2-2B^jX^muv+B^jv^2.
\]
Grouping by halves gives
\[
r_j(u,v)=
\underbrace{b_j+a_ju-B^ju^2}_{\text{depends only on }u}
+
\underbrace{X^ma_jv+B^jv^2}_{\text{depends only on }v}
-
\underbrace{2B^jX^muv}_{\text{couples }u\text{ and }v}.
\]

The last term is the obstruction to an independent right-list hash: its value changes with the left half \(u\). Precomputing \(v^2\) and \(X^ma_jv\) for each right entry does not remove this \(u\)-dependent cross term. A correct alternative join would need to represent or otherwise account for \(uv\) exactly; simply hashing the two independent half contributions would be unsound. Computing the cross term separately for every \((u,v)\) pair risks restoring the original \(3^N\) pairwise work. This is an algebraic limitation of the naive split, not a proof that every more sophisticated join is impossible.

## Selected-coordinate sweep for the public-key hash

The MITM prototype was extended to test (k=1,2,3,4) selected public-key coordinates. For each left-half entry, the join enumerates (5^k) bounded-error patterns. All configurations were cross-checked against exhaustive search on the same 30 generated instances at each degree; every configuration achieved exact-set agreement in all 30 trials and retained the planted secret.

| N | k | Error probes per left entry | Median joined pairs | Median MITM time | Exhaustive/MITM ratio |
|---:|---:|---:|---:|---:|---:|
| 4 | 1 | 5 | 37 | 0.000218 s | 1.39x |
| 4 | 2 | 25 | 16 | 0.000259 s | 1.17x |
| 4 | 3 | 125 | 8 | 0.000742 s | 0.41x |
| 4 | 4 | 625 | 3.5 | 0.003461 s | 0.09x |
| 6 | 1 | 5 | 331.5 | 0.001488 s | 2.67x |
| 6 | 2 | 25 | 150 | 0.001318 s | 3.01x |
| 6 | 3 | 125 | 68 | 0.002510 s | 1.58x |
| 6 | 4 | 625 | 31.5 | 0.010402 s | 0.38x |
| 8 | 1 | 5 | 2982 | 0.012108 s | 4.31x |
| 8 | 2 | 25 | 1356 | 0.008722 s | 5.99x |
| 8 | 3 | 125 | 615 | 0.010296 s | 5.07x |
| 8 | 4 | 625 | 276 | 0.032440 s | 1.61x |

The median number of candidates passing the full public residual and the final evaluation-key survivor count were independent of (k) for a fixed instance set: 3.5 and 1 (N=4), 7.5 and 1 (N=6), 11 and 1 (N=8). Increasing (k) reduces join collisions, but the (5^k) probe growth eventually dominates. In this single CI run, (k=1) was fastest for N=4, while (k=2) was fastest for N=6 and N=8. This supports a degree- and cost-dependent choice of (k), not a universal optimum.

These timings are exploratory CI medians, not repeated controlled benchmarks. The tests use q=11 and N<=8 and do not establish performance at cryptographic parameters. The sweep is exact only because all candidate pairs retrieved through the selected-coordinate error patterns are subsequently checked against every coefficient of the full public residual and all evaluation-key equations.

## Repeated timing sweep (three runs per instance)

To reduce sensitivity to a single timing observation, the coordinate sweep was repeated three times for each of the 30 generated instances at each degree. The reported MITM timing below is the median over 90 executions per \(k,N\); the exhaustive baseline is the median over the 30 exhaustive executions.

| N | k | Probes per left entry | Median joined pairs | MITM median | Exhaustive/MITM ratio |
|---:|---:|---:|---:|---:|---:|
| 4 | 1 | 5 | 37 | 0.000181 s | 1.36x |
| 4 | 2 | 25 | 16 | 0.000222 s | 1.11x |
| 4 | 3 | 125 | 8 | 0.000624 s | 0.39x |
| 4 | 4 | 625 | 3.5 | 0.002876 s | 0.09x |
| 6 | 1 | 5 | 331.5 | 0.001234 s | 2.50x |
| 6 | 2 | 25 | 150 | 0.001116 s | 2.77x |
| 6 | 3 | 125 | 68 | 0.002117 s | 1.46x |
| 6 | 4 | 625 | 31.5 | 0.008689 s | 0.36x |
| 8 | 1 | 5 | 2982 | 0.010555 s | 3.77x |
| 8 | 2 | 25 | 1356 | 0.007531 s | 5.28x |
| 8 | 3 | 125 | 615 | 0.008914 s | 4.46x |
| 8 | 4 | 625 | 276 | 0.027773 s | 1.43x |

Every configuration again achieved exact-set agreement in all 30 instances for each degree. The fastest observed setting remained \(k=1\) for N=4 and \(k=2\) for N=6 and N=8. The \(k=4\) setting sharply reduced the median join output, but its 625 error probes per left entry made it slower than exhaustive search at N=4 and N=6. At N=8 it retained a 1.43x ratio, still well behind \(k=2\).

The timing repetition improves the stability of the toy comparison but does not turn it into a controlled benchmark: all runs share one CI environment, and the parameters remain q=11 and N<=8. The data support choosing \(k\) based on the balance between \(5^k\) probes and collision reduction; they do not establish a production-scale optimum.
