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

The script uses q=11, base B=3, three evaluation-key levels, eta=2 errors, deterministic seed 0xBF2, and 30 trials at each even degree:

| N | Exact candidate-set agreement | Median exhaustive time | Median MITM time | Observed speed ratio |
|---:|---:|---:|---:|---:|
| 4 | 30/30 | 0.000240 s | 0.000211 s | 1.14x |
| 6 | 30/30 | 0.003516 s | 0.000854 s | 4.11x |
| 8 | 30/30 | 0.049400 s | 0.004212 s | 11.73x |

These timing figures are exploratory single-machine measurements, not formal benchmarks. Candidate sets agreed exactly in all 90 trials, and the planted secret was retained in every trial.

## Complexity and limitations

The two lists each contain 3^(N/2) entries, but the current implementation probes 5^k error patterns per left entry, where k=2 selected coordinates. It also stores full polynomial contributions and performs full candidate verification on bucket hits. This gives a useful toy speedup, but does not establish a scalable algorithm at large N.

The prototype joins on the public-key equation; evaluation-key equations are applied after a candidate pair is found. It does not yet exploit evaluation-key structure to reduce list sizes. Memory usage, collision behavior, optimal coordinate selection, and larger-degree scaling remain open.

## Reproduction

```bash
python scripts/toy_evalkey_mitm.py
```

The script uses only the Python standard library.