# Paper 1 — Validation and CI Provenance

This file records workflow identifiers, historical execution corrections, and artifact locations that support the reproducibility statements in the manuscript. It is supplementary project documentation, not part of the scientific argument. A green workflow confirms only the checks actually executed by that workflow; it does not establish independent mathematical review, cryptanalytic security, or publication novelty.

## Current validation workflow

- Latest inspected run: [GitHub Actions run 43558638880](https://github.com/jbenavidesj/lattice-fhe-ppml/actions/runs/43558638880).
- Result at inspection: all four jobs passed:
  1. Python arithmetic audits.
  2. Pinned SageMath LWE-proxy diagnostic.
  3. IEEEtran journal typesetting and PDF inspection.
  4. Rust tests and benchmark compilation.
- Generated artifacts included `paper1-ieee-typeset` (artifact ID `14099123005`) and `sage-lwe-proxy-diagnostic` (artifact ID `14099810975`).
- The generated IEEEtran PDF was inspected as an eight-page letter-size document. The title/byline, affiliation, abstract, and IEEE section numbering rendered without the duplicate heading prefixes previously observed.
- This run predates the manuscript-only editorial commit that introduced this provenance document and moved CI history out of the paper. It must not be described as a CI run on that later commit.

## Historical workflow correction

- Historical run #617 invoked three Python audit scripts using `python` inside a SageMath container where that executable was unavailable. A `tee` pipeline masked the script failures. The scalar LWE proxy and LLL relation search did execute, but the three affected Python audits were not validated by that run.
- The workflow was corrected to invoke the scripts through `sage -python` and to propagate each script's exit status rather than relying on a pipeline whose final command could mask failure.
- The subsequent validation workflow #798 (run ID `43522369561`) passed its three configured jobs, including the SageMath diagnostic job. This did not retroactively validate the failed invocations in run #617.

## Experiment and audit run index

The following identifiers are retained for traceability. Numerical results and their limitations are described in the corresponding manuscript sections and appendices.

| Run | Recorded purpose | Commit / note |
|---|---|---|
| #3 | Initial Criterion release-mode benchmark baseline; virtualized Azure Linux VM; raw Criterion output and environment metadata | `be820f044647e8e2444d5e415503172bb1498a6f`; artifact name `paper1-release-benchmarks-be820f044647e8e2444d5e415503172bb1498a6f` |
| #676 | Four-way toy transcript filtering experiment | Values retained in Appendix F |
| #693 | Corrected SageMath exact one-coefficient error-PMF and Pareto-frontier audit | `8ff7f551f38b93af8ca85f51b3a67645674a5146` |
| #699 | Exact joint candidate-filter audit | Original residual constraints compared with anchor-plus-adjacent-differences representation |
| #712 | Stagewise exhaustive audit at N=2, q in {17,19}, B=2, six evaluation-key levels | 200 synthetic transcripts per modulus |
| #715 | Reporting rerun of the stagewise exhaustive audit | Same low-modulus toy setting |
| #722 | Dimension-growth exhaustive audit at N=3,4 and q in {17,19} | 100 seeded transcripts per setting |
| #729 | Extended conditional toy audit at N=5,6 and q in {17,19} | `2b862166bf4a84178250b728243995b0547171be` |
| #734 | Extended conditional toy audit across N=2,3,4,5,6 | `521d30278d101f88f9e84b6601edca0c7c562663` |
| #741 | Extended conditional toy audit at N=7,8 and q in {13,17} | `73fbebdab07453896ce06870c5fa716e71ea9b4e` |
| #798 | Corrected three-job validation workflow after the SageMath invocation fix | Run ID `43522369561` |

## Interpretation

- Toy exhaustive and MITM experiments enumerate small candidate spaces. Their results are finite-instance algorithmic diagnostics, not production-dimension attacks and not evidence of a concrete security level.
- The scalar unstructured-LWE proxy is not a Ring-LWE estimate and does not model the complete related-target public/evaluation-key transcript.
- The benchmark results come from one virtualized CI session. Within-run confidence intervals do not quantify cross-machine or cross-session variation.
- The successful IEEEtran build is a typesetting check. It does not clear the manuscript for journal submission.
- Independent mathematical review, specialist cryptanalysis of the joint transcript, and a venue-specific novelty assessment remain open external requirements.
