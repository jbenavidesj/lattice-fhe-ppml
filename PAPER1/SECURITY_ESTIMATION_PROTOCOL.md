# Security-estimation protocol for Paper 1

## Purpose

Run a reproducible unstructured-LWE diagnostic for the power-of-two cyclotomic RNS-BFV candidate. This is a heuristic proxy, **not a Ring-LWE security certificate**. It does not model the evaluation-key samples whose target contains s^2.

## Pinned software

- Estimator: `malb/lattice-estimator`
- Commit: `7d59f866655362ea8eab803dbc833710c2bc362a` (2026-11-09)
- SageMath: record the exact version printed by the script.
- Cost and shape models: record the values printed by the script from the pinned estimator configuration.

The estimator API accepts LWE parameters and evaluates multiple lattice attacks; its output depends on attack coverage, reduction cost model, and shape model. The exact estimator commit must be retained with the output.

## Candidate and comparison models

Candidate:
- n=8192
- q=421249165630599354127590185589164472945208468246547404789529362433
- secret: coefficientwise ternary {-1,0,1}
- error: centered-binomial eta=2, support [-2,2], standard deviation 1

Reference comparison from the estimator's HE Standard v2 parameter set:
- n=8192
- q=2^214
- secret: ternary
- error: discrete Gaussian, standard deviation 3.19

For each model the script evaluates m=N and m=infinity. The m=N setting treats one polynomial RLWE sample as N scalar LWE equations after unrolling; the m=infinity setting is a sample-rich sensitivity case. Neither removes the ring structure, so neither is a proof against ring-specific attacks. Evaluation-key samples are not counted as ordinary LWE samples.

## Reproduction

```sh
git clone https://github.com/malb/lattice-estimator
cd lattice-estimator
git checkout 7d59f866655362ea8eab803dbc833710c2bc362a
sage -pip install -e .
sage -python /path/to/lattice-fhe-ppml/scripts/estimate_lwe_proxy.py
```

Preserve the full output. Record the Sage version, estimator commit, exact parameter values, m, attack names, reduction cost/shape models, and any estimator warnings or failed attacks. Do not select only the most favorable attack result; report the minimum finite estimated attack cost and the complete per-attack table.

## Interpretation

- The candidate's eta=2 error is narrower than the Gaussian-3.19 reference; the resulting security estimate may be substantially lower.
- The candidate's Q is larger than the HE Standard v2 comparison q. Both differences affect security, and their effects cannot be inferred by a simple bit-length subtraction.
- A result from this script must be labelled an unstructured-LWE proxy under the power-of-two RLWE heuristic. It must not be called a proved Ring-LWE security level.
- A separate analysis is required for the evaluation-key exposure, secret-dependent implementation details, and algebraic/structural attacks.
- If the estimator fails, returns no finite cost, or omits an applicable attack, report that limitation rather than manufacturing a security number.

## References

- Lattice estimator source: https://github.com/malb/lattice-estimator
- Pinned source commit: https://github.com/malb/lattice-estimator/commit/7d59f866655362ea8eab803dbc833710c2bc362a
- HE Standard v2 security-guideline parameter discussion: https://eprint.iacr.org/2024/463
- Homomorphic Encryption Standard v1.1: https://homomorphicencryption.org/wp-content/uploads/2024/08/Homomorphic-Encryption-Standard-v1.1.pdf
