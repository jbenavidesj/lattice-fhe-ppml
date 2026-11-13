# Toy exhaustive search for related evaluation-key samples

## Purpose

This experiment asks a narrow question: in a small negacyclic ring, do evaluation-key equations reduce the number of ternary secrets consistent with a public-key sample?

It is a finite toy experiment, **not** a security estimator, attack on the production parameters, or evidence of a concrete security level.

## Model

- Ring: \(\mathbb Z_{11}[X]/(X^N+1)\).
- Secret coefficients: independent uniform values in \(\{-1,0,1\}\).
- Public-key sample: \(b_{pk}=-a_{pk}s+e_{pk}\pmod{11}\).
- Evaluation-key levels: \(b_j=-a_js+3^js^2+e_j\pmod{11}\), for \(j=0,1,2\).
- Each \(a\) is sampled uniformly coefficientwise modulo 11.
- Each error coefficient is centered binomial eta=2, sampled as the difference of two independent Binomial(2, 1/2) variables, with support \([-2,2]\).
- Candidate acceptance requires every coefficient of every residual to have centered representative in \([-2,2]\).
- The script exhaustively enumerates all \(3^N\) ternary candidates and compares counts satisfying only the public-key sample with counts satisfying the public-key and all evaluation-key samples.

## Reproducible result

With deterministic seed `0xBF2` and 30 trials per degree, the observed candidate counts were:

| N | Median candidates: public sample only | Median candidates: public + evaluation key | Trials unique: public only | Trials unique: with evaluation key |
|---:|---:|---:|---:|---:|
| 4 | 3.5 | 1 | 2/30 | 30/30 |
| 6 | 7.5 | 1 | 0/30 | 30/30 |
| 8 | 11 | 1 | 0/30 | 30/30 |

The planted secret is checked to remain a valid candidate in every trial.

## Interpretation

For these deliberately tiny parameters, the evaluation-key equations substantially reduce the number of ternary candidates that satisfy the public-key equation alone. This is expected because they add more constraints on the same secret and related target \(s^2\).

This result **does not imply a practical key-recovery attack**. The experiment has tiny modulus and degree, uses only three evaluation-key levels, performs exhaustive search, and does not model the production RNS/CRT centered-lift implementation, key-switch digit decomposition, or realistic security parameters. In particular, the modulus 11 and base 3 are chosen for an informative toy search and are not the Paper 1 parameters.

The experiment measures candidate-set reduction under a specified residual threshold. It does not measure an attack's asymptotic complexity, distinguishability at production parameters, or security in bits. Extrapolation to \(N=8192\) is not justified.

## Reproduction

Run:

```bash
python scripts/toy_evalkey_exhaustive_search.py
```

The script uses only the Python standard library and a fixed random seed.