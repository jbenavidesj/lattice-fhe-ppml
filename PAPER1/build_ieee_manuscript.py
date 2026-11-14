#!/usr/bin/env python3
"""Prepare the reviewed Markdown manuscript for IEEEtran journal typesetting.

This is a formatting transform only. It does not alter technical claims or results.
"""
from pathlib import Path
import re

source = Path("PAPER1/IEEE_MANUSCRIPT_DRAFT.md")
target = Path("build/IEEE_MANUSCRIPT.md")
text = source.read_text(encoding="utf-8")
lines = text.splitlines()

# Markdown prose occasionally contains compact mathematical notation written
# without delimiters (for example, s^2). Put these simple powers into inline
# math mode before Pandoc emits LaTeX. Preserve already-delimited math.
def normalize_plaintext_powers(line):
    # Protect existing inline math and code spans from rewriting.
    parts = re.split(r"(\\\(.*?\\\)|\$.*?\$|`.*?`)", line)
    for i in range(0, len(parts), 2):
        parts[i] = re.sub(
            r"(?<![\w\\\\])([A-Za-z][A-Za-z0-9]*)\^([A-Za-z0-9]+)",
            lambda m: r"\(" + m.group(1) + "^{" + m.group(2) + r"}\)",
            parts[i],
        )
        parts[i] = re.sub(
            r"([A-Za-z])\^\(([^)]+)\)",
            lambda m: r"\(" + m.group(1) + "^{" + m.group(2) + r"}\)",
            parts[i],
        )
    return "".join(parts)

# Normalize compact powers only in prose. Do not rewrite any line inside a
# display-math block: doing so can nest inline \\( ... \\) delimiters
# inside Pandoc's \\[ ... \\] environment and corrupt equations such as
# B^j s^2.
normalized_lines = []
in_display_math = False
for line in lines:
    stripped = line.strip()
    if stripped.startswith(r"\\[") or stripped == r"\\begin{equation}":
        in_display_math = True
    normalized_lines.append(line if in_display_math else normalize_plaintext_powers(line))
    if stripped.endswith(r"\\]") or stripped == r"\\end{equation}":
        in_display_math = False
lines = normalized_lines

# Remove the Markdown title (provided by the IEEEtran template) and the
# internal editorial-status paragraph, neither of which belongs in the paper.
if lines and lines[0].startswith("# "):
    lines = lines[1:]
if lines and lines[0].startswith("**Manuscript status ("):
    lines = lines[1:]
    while lines and not lines[0].strip():
        lines.pop(0)

# Convert the abstract heading into IEEEtran's abstract environment.
try:
    abstract_idx = lines.index("## Abstract")
    intro_idx = lines.index("## 1. Introduction")
except ValueError as exc:
    raise SystemExit("Expected Abstract and Introduction headings were not found") from exc
lines[abstract_idx] = r"\begin{abstract}"
lines.insert(intro_idx + 1, "")  # preserve separation after the introduction heading
# Locate the introduction after insertion and close the abstract immediately before it.
intro_idx = lines.index("## 1. Introduction")
lines.insert(intro_idx, r"\end{abstract}")
lines.insert(intro_idx + 1, "")
lines.insert(intro_idx + 1, r"\begin{IEEEkeywords}")
lines.insert(intro_idx + 2, "fully homomorphic encryption, BFV, residue number system, lattice-based cryptography, exact arithmetic, reproducible validation")
lines.insert(intro_idx + 3, r"\end{IEEEkeywords}")

# IEEEtran appendix mode labels subsequent sections A, B, ... .
appendix_idx = next((i for i, line in enumerate(lines) if line.startswith("## Appendix A.")), None)
if appendix_idx is None:
    raise SystemExit("Appendix A heading was not found")
lines.insert(appendix_idx, r"\appendices")
lines.insert(appendix_idx + 1, "")

# Use IEEE's bibliography environment while preserving the checked reference text.
try:
    refs_idx = lines.index("## References")
except ValueError as exc:
    raise SystemExit("References heading was not found") from exc
reference_lines = [line for line in lines[refs_idx + 1:] if line.strip()]
if len(reference_lines) != 8 or not all(re.match(r"^\[\d+\]\s", line) for line in reference_lines):
    raise SystemExit(f"Expected exactly eight numbered references; found {len(reference_lines)}")
bib = [r"\begin{thebibliography}{8}"]
for line in reference_lines:
    match = re.match(r"^\[(\d+)\]\s+(.*)$", line)
    bib.append(r"\bibitem{ref" + match.group(1) + "} " + match.group(2))
bib.append(r"\end{thebibliography}")
lines = lines[:refs_idx] + [""] + bib + [""]

target.parent.mkdir(parents=True, exist_ok=True)
target.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
print(f"Prepared {target}: {len(lines)} lines; 8 bibliography entries.")
