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
## Search complexity and scaling limits

The exhaustive routine enumerates all \(3^N\) ternary secrets. For each candidate it evaluates one public-key residual and, if that passes, up to three evaluation-key residuals. With the straightforward negacyclic multiplication in the script, the worst-case arithmetic cost is \(O(3^N L N^2)\) modular coefficient operations (plus the public-key check); replacing polynomial multiplication with an NTT-style method can reduce the polynomial factor but cannot remove the exponential \(3^N\) candidate count.

| N | Ternary candidates \(3^N\) |
|---:|---:|
| 8 | 6,561 |
| 16 | 43,046,721 |
| 32 | 1,853,020,188,851,841 |
| 64 | approximately 3.43 × 10^30 |
| 256 | approximately 1.04 × 10^122 |
| 8192 | approximately 10^3908.58 |

Thus the fact that the toy experiment leaves one candidate does **not** make exhaustive recovery scalable. The experiment tests information content in tiny instances, not an efficient attack. Any meaningful attack at production dimension would need a non-exhaustive method that exploits lattice structure, algebraic constraints, or another demonstrable shortcut.

### Local runtime sanity check

A separate local timing sanity check using the same straightforward implementation and deterministic instances completed 30 trials at N=4, 6, and 8 in approximately 0.009 s, 0.112 s, and 1.556 s respectively; 10 trials at N=10 took approximately 6.436 s, and 3 trials at N=12 took approximately 25.082 s. These are single-machine exploratory timings, not benchmark claims, and the seeds for this timing run differ from the fixed-seed candidate-count table above. They illustrate the rapid growth of exhaustive enumeration and must not be used to extrapolate precise runtimes to large N.
## Why meet-in-the-middle is not yet an attack

Split the coefficient vector into two blocks, \(s=u+X^m v\), where \(m=N/2\). For a fixed public polynomial \(a\), negacyclic multiplication is linear, so
\[a s=a u+aX^m v.\]
A meet-in-the-middle method could enumerate the \(3^m\) possible left contributions \(a u\) and right contributions \(aX^m v\), then seek pairs whose sum is within the centered error box around \(-b\). This reduces the raw list size from \(3^N\) to two lists of size \(3^{N/2}\), but it does **not** yield a simple exact hash lookup: the residual is not zero; every coefficient may lie in an interval of width five (for eta=2), and the target is modular. A correct join must enumerate or efficiently index the full error box, or use a rigorously analyzed approximate-neighbor data structure. Naively probing all \(5^N\) error vectors removes the apparent advantage.

### Random-residual heuristic for the toy counts

If a wrong ternary candidate produces a coefficientwise uniform residual modulo q, the probability that one residual coefficient lies in the accepted centered set \([-2,2]\) is \(5/q\). Under the simplifying independence heuristic, the expected number of false candidates passing one public sample is
\[ (3^N-1)(5/q)^N \approx (15/q)^N. \]
For q=11 this heuristic gives approximately 3.46, 6.43, and 11.96 false candidates for N=4,6,8, respectively. These are close in scale to the observed public-only medians (3.5, 7.5, 11), but the model is not exact: residual coefficients and candidate events can be correlated, and the planted candidate always passes. The agreement is a sanity check, not a proof.

If each of the three evaluation-key equations contributed an independent uniform residual constraint of the same width, the heuristic false-candidate expectation would acquire another factor \((5/q)^{3N}\). The actual equations share the same candidate and related target \(s^2\), so independence is not established; this calculation only explains why the toy combined system is highly selective.

### Current algorithmic conclusion

Meet-in-the-middle remains a possible research direction, but the noisy modular join is the central unresolved subproblem. The current repository contains no MITM implementation and makes no claim of a faster-than-exhaustive attack. A future implementation must report (i) exact join semantics including centered modular errors, (ii) memory and time as functions of N and q, (iii) false-positive/false-negative checks against exhaustive search at toy sizes, and (iv) whether evaluation-key equations can be incorporated without destroying the list-size advantage.