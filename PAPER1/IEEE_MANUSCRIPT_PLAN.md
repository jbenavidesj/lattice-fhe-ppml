# Paper 1 — IEEE manuscript plan

## Working title

An Experimental RNS-BFV Implementation with Exact Integer-Lift Multiplication and Reproducible Correctness Audits

The title is deliberately descriptive. Do not claim a new FHE construction, a new security reduction, or a production-optimized implementation unless subsequent independent work establishes that contribution.

## Proposed contribution statement

This paper reports an implementation and correctness study of an experimental leveled RNS-BFV prototype. Its defensible contributions are:
1. A four-lane RNS arithmetic implementation targeting N=8192, with candidate NTT parameters, CRT reconstruction, centered basis extension, and modular reduction routines.
2. An exact integer-lift tensor multiplication reference path using an auxiliary NTT/CRT basis so that quotient information required by BFV scale-and-round is retained.
3. Executable deterministic audits for arithmetic identities, auxiliary CRT range, and a conservative one-multiplication-plus-relinearization noise bound.
4. A transparent analysis of the structured evaluation-key transcript, explicitly identifying the related-secret target (s,s^2) and the limits of ordinary unstructured-LWE proxies.
5. Small-parameter exhaustive and MITM experiments as algorithmic diagnostics, not as a production-parameter attack.

These are implementation, validation, and analysis contributions. Novelty relative to prior BFV/RNS implementations must be established by a literature comparison before submission.

## Manuscript structure

1. Introduction — problem, scope, research questions, and carefully delimited contributions.
2. Background and notation — negacyclic ring, RNS representation, BFV phase, gadget decomposition, scale-and-round.
3. Parameterization and implementation architecture — N=8192, four-lane RNS, NTT/CRT, auxiliary basis, samplers, key/evaluation-key layout.
4. Exact multiplication and correctness argument — centered integer lifts, auxiliary CRT range, coefficientwise scale-and-round, one-level noise derivation.
5. Evaluation-key structure and security limitations — exact public relation, joint transcript, adjacent-level cancellation, what is and is not established.
6. Implementation validation — unit/integration tests, deterministic arithmetic audits, independent reference comparisons.
7. Toy candidate-search experiments — exhaustive baseline, MITM split, exact-set checks, coordinate sweep, adaptive selector and held-out protocol; explicitly separated from scheme security.
8. Performance evaluation — release-mode benchmarks only after collection under PAPER1/BENCHMARK_PROTOCOL.md.
9. Limitations and responsible claims — no concrete security level, no arbitrary depth, no side-channel claim, no production readiness.
10. Conclusion and future work.

## Figures and tables required

- Architecture/dataflow diagram: RNS lanes, auxiliary multiplication basis, CRT lift and scale-round path.
- Parameter table: exact moduli, NTT conditions, plaintext modulus, base, gadget levels, sampler distributions.
- Correctness table: each audit, command, test count, and CI commit/run.
- Noise-bound table: every term, exact rational value, total bound, decoding margin, assumptions.
- Security model table: public samples, secrets, error distributions, estimator coverage, unresolved attacks.
- Performance table: only release benchmarks with raw data, environment metadata, repeated samples and dispersion.
- Toy MITM table: N, q, eta, k, list sizes, probes, joined pairs, exact-set agreement, runtime; labelled toy-only.

## Closure status (2026-11-13)

The held-out selector audits, pinned rough-profile unstructured-LWE diagnostic, single-session release benchmark, source/proof consistency pass, focused BEHZ/HPS comparison, and internal claim/citation consolidation have been completed and recorded in the manuscript and validation ledger. The diagnostic estimator output is not a Ring-LWE security estimate. The benchmark is descriptive only; no performance superiority is claimed.

Remaining external gates are independent mathematical review, specialist cryptanalytic review of the joint public/evaluation-key transcript, and a venue-specific novelty assessment. The current branch contains a Markdown manuscript, not a final IEEEtran typeset submission package. A final production layout and page count still require conversion into the target journal's current template and review of the generated PDF.

## Submission blockers

- Obtain independent review of the noise proof and joint public/evaluation-key security model.
- Obtain a venue-specific novelty assessment for an implementation/reproducibility contribution.
- Convert the manuscript into the target venue's current IEEE template and inspect the generated PDF, references, equations, figures, and page count.
- Reconcile any reviewer findings and re-run relevant tests if source code changes.

## Abstract drafting rule

Do not finalize the abstract until the novelty comparison, held-out experiment, security interpretation, and release benchmarks are complete. Any abstract before then is a provisional summary, not a submission-ready claim.