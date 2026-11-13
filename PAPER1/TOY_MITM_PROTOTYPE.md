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