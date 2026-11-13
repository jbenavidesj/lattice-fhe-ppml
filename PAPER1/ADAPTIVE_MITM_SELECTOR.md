# Adaptive MITM selector: parameterized model and validation scope

## Motivation

The original selector was specialized to q=11 and eta=2. Its score was

\[
\widehat C_N(k)=3^{N/2}5^k+4\cdot3^N(5/q)^k.
\]

The implementation now parameterizes the modulus, centered-error radius, candidate coordinate counts, and relative pair cost:

\[
\widehat C_{N,q,\eta}(k)
=3^{N/2}(2\eta+1)^k
+\lambda\,3^N\left(\frac{2\eta+1}{q}\right)^k.
\]

Here \(\lambda\) is a heuristic relative-cost weight. The expected-hit term assumes independent, uniform residues in the selected coordinates. That assumption is not proved for the structured negacyclic instance, so the expression is a transparent selection proxy, not a rigorous expected-runtime bound or a cryptographic complexity estimate.

## Parameter-grid audit

The new deterministic audit checks the arithmetic and admissible output of the selector over:

- q in {11, 17, 31, 97};
- eta in {0, 1, 2, 3}, retaining only q > 2 eta;
- even N in {4, 6, 8, 10, 12};
- candidate k values from 1 through min(N, 5).

It also checks that the default q=11, eta=2 choices remain k=(1,2,2) for N=(4,6,8). This audit tests the selector's formula and parameter handling; it does **not** establish that the selected k is empirically optimal at new q or eta values.

## Out-of-sample experimental protocol

A meaningful generalization claim requires empirical measurements, not only a parameter-grid unit audit. The next experiment should:

1. Generate independent training instances for each (q, eta, N) configuration.
2. Measure every admissible fixed k using the same instances and repeated timings.
3. Select lambda and any model refinements using training data only.
4. Freeze the model and evaluate it on disjoint held-out instances.
5. Compare predicted k with the empirically fastest fixed k, reporting regret, timing distributions, join counts, and memory.
6. Cross-check each candidate set against exhaustive search for toy degrees.

No out-of-sample performance claim is made in this note. The current selector remains a parameterized heuristic. The production cryptographic degree and modulus are far outside the validated exhaustive toy range.
