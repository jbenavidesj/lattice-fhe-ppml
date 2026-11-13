# Preliminary unstructured-LWE proxy diagnostic — recorded results

## Status and provenance

This file records the bounded SageMath diagnostic produced by GitHub Actions workflow run [#582](https://github.com/jbenavidesj/lattice-fhe-ppml/actions/runs/43361043125) on the `paper1-validation-corrections` branch. The run completed successfully and uploaded the `sage-lwe-proxy-diagnostic` artifact.

- SageMath: 10.10
- `malb/lattice-estimator` commit: `7d59f866655362ea8eab803dbc833710c2bc362a`
- Profile: `LWE.estimate.rough()`
- Reduction-cost model: ADPS16
- Shape model: GSA
- Nominal dimension and sample count: n=8192, m=8192
- Candidate error: centered-binomial eta=2
- Reference error: discrete Gaussian, sigma=3.19

## Reported outputs

| Model | uSVP log2(rop) | dual-hybrid log2(rop) | Minimum among reported attacks |
|---|---:|---:|---:|
| Paper 1 candidate (eta=2) | 93.732 | 93.732 | 93.732 |
| HE Standard v2 comparison (sigma=3.19) | 97.528 | 97.236 | 97.236 |

The candidate's reported uSVP and dual-hybrid costs tie at approximately (2^{93.7}). The comparison model's minimum is the dual-hybrid result, approximately (2^{97.2}).

## Exact run output

```text
lattice-estimator commit: 7d59f866655362ea8eab803dbc833710c2bc362a
SageMath version: 10.10
rough-profile reduction cost model: ADPS16
rough-profile shape model: GSA
WARNING: preliminary unstructured-LWE rough profile only; not a Ring-LWE certificate.
Evaluation-key samples are not modelled.

[Paper1 candidate, eta=2 centered-binomial] n=8192; q=421249165630599354127590185589164472945208468246547404789529362433; m=8192; profile=rough
usvp :: rop: ≈2^93.7, red: ≈2^93.7, δ: 1.004628, β: 321, d: 15879, tag: usvp
dual_hybrid :: rop: ≈2^93.7, red: ≈2^93.7, guess: ≈2^68.1, β: 321, p: 3, ζ: 0, t: 30, β': 321, N: ≈2^57.6, m: ≈2^13.0
dual_hybrid: log2(rop)=93.7320; details=...
usvp: log2(rop)=93.7320; details=...
minimum rough estimated attack cost: 93.7320 bits

[HE Standard v2 comparison, Gaussian sigma=3.19] n=8192; q=26328072917139296674479506920917608079723773850137277813577744384; m=8192; profile=rough
usvp :: rop: ≈2^97.5, red: ≈2^97.5, δ: 1.004506, β: 334, d: 15730, tag: usvp
dual_hybrid :: rop: ≈2^97.2, red: ≈2^97.2, guess: ≈2^78.2, β: 333, p: 4, ζ: 0, t: 30, β': 333, N: ≈2^65.7, m: ≈2^13.0
dual_hybrid: log2(rop)=97.2360; details=...
usvp: log2(rop)=97.5280; details=...
minimum rough estimated attack cost: 97.2360 bits
```

## Interpretation — strict limitations

These are conditional heuristic work-factor outputs for the selected attacks under the stated rough profile, ADPS16 cost model, GSA shape assumption, and scalar unstructured-LWE proxy. The displayed “bits” are the estimator's base-2 logarithm of the reported attack cost; **they are not an established security level for the BFV scheme**.

In particular:

1. This run is not a Ring-LWE estimate, a proof, a lower bound, or a security certificate.
2. The evaluation-key samples targeting (s^2) are explicitly not modelled.
3. The proxy does not capture the negacyclic ring structure or the correlated-error representation derived for adjacent evaluation-key levels.
4. The candidate and comparison differ in both modulus and error distribution; this is not a controlled one-variable comparison.
5. No 128-bit (or other concrete) scheme-security claim follows from these values.

The next cryptographic task is a joint analysis of the public-key and evaluation-key transcript, including its related target (s^2), ring structure, and correlated errors. Until that analysis is completed and independently reviewed, the paper should present this run only as a preliminary diagnostic.

## Reproduction

See [SECURITY_ESTIMATION_PROTOCOL.md](SECURITY_ESTIMATION_PROTOCOL.md) for the pinned environment, parameter definitions, command, and reproduction protocol.
