# Security-estimation protocol for Paper 1

## Purpose and status

Run a **preliminary, bounded-cost unstructured-LWE screening diagnostic** for the power-of-two cyclotomic RNS-BFV candidate. This is not a Ring-LWE estimator or a security certificate. It does not model the evaluation-key samples whose target contains s^2.

The first-pass script intentionally uses `LWE.estimate.rough()` from the pinned estimator revision. At this revision that profile evaluates uSVP and dual-hybrid attacks (and Arora-GB only under its documented sample/noise conditions), rather than the full default attack sweep. It uses the estimator's ADPS16 reduction-cost model and GSA shape assumption. Its figures are **rough-profile screening outputs** and must not be described as the estimator's full default results or as a concrete security level.

## Pinned software and models

- Estimator: `malb/lattice-estimator`
- Commit: `7d59f866655362ea8eab803dbc833710c2bc362a`
- Runtime: SageMath 10.10 container; exact runtime version is printed.
- Rough-profile reduction cost model: ADPS16.
- Rough-profile reduction shape model: GSA.

## Candidate and comparison models

Candidate:
- n=8192
- q=421249165630599354127590185589164472945208468246547404789529362433
- secret: coefficientwise ternary {-1,0,1}
- error: centered-binomial eta=2, support [-2,2], standard deviation 1

Reference comparison:
- n=8192
- q=2^214
- secret: ternary
- error: discrete Gaussian, standard deviation 3.19

The bounded first-pass diagnostic uses m=N=8192 for each model. It does not run m=infinity. The m=N setting is a deliberately simplified scalar-LWE proxy with N equations and the same nominal secret dimension; it is **not** an exact distributional equivalence to one polynomial RLWE sample. Unrolling a polynomial sample produces a highly structured negacyclic matrix, whereas generic LWE estimators model matrices from their own sampling assumptions. Neither this proxy nor the rough attack profile removes the ring structure or proves security against ring-specific attacks. Evaluation-key samples are not counted as ordinary LWE samples.

## Interpretation and limitations

- The rough profile is deliberately narrower than the full default estimator API. Its results are suitable only for an initial screening comparison.
- The estimator's reported work factors are conditional heuristic estimates under the selected attacks, ADPS16 cost model, GSA shape assumption, and input distributions. They are not a proven lower bound, not a concrete security level for the scheme, and not a substitute for analysis of the joint public-key/evaluation-key distribution.
- Do not convert the minimum reported \\(\\log_2(\\mathrm{rop})\\) into an unqualified "bits of security" claim.
- Candidate and reference differ in both modulus and error distribution, so the comparison is diagnostic rather than a controlled one-variable comparison.
- A separate analysis is required for the evaluation-key exposure, secret-dependent implementation details, and algebraic/structural attacks.
- If the estimator fails, returns no finite cost, or omits an applicable attack, report that limitation rather than manufacturing a security number.

## Reproduction

```sh
git clone https://github.com/malb/lattice-estimator
cd lattice-estimator
git checkout 7d59f866655362ea8eab803dbc833710c2bc362a
sage -pip install -e .
sage -python /path/to/lattice-fhe-ppml/scripts/estimate_lwe_proxy.py
```

Preserve the full output. Record Sage version, estimator commit, exact parameter values, sample count, attack names, reduction model, shape assumption, and estimator warnings. A later full-profile run, if attempted, must be a separate explicitly budgeted experiment; it must not silently replace or be conflated with this rough screening pass.

## References

- Lattice estimator source: https://github.com/malb/lattice-estimator
- Pinned source commit: https://github.com/malb/lattice-estimator/commit/7d59f866655362ea8eab803dbc833710c2bc362a
- HE Standard v2 security-guideline parameter discussion: https://eprint.iacr.org/2024/463
- Homomorphic Encryption Standard v1.1: https://homomorphicencryption.org/wp-content/uploads/2024/08/Homomorphic-Encryption-Standard-v1.1.pdf
