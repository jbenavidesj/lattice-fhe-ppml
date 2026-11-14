#!/usr/bin/env python3
"""Convert Pandoc longtable blocks to single-column IEEEtran tabularx floats."""
from pathlib import Path
import re

path = Path("build/Paper1_IEEEtran.tex")
source = path.read_text(encoding="utf-8")
pattern = re.compile(r"\\begin\{longtable\}\[\]\{(.*?)\}\s*\n\\toprule\\noalign\{\}", re.S)

matches = list(pattern.finditer(source))
if not matches:
    raise SystemExit("No Pandoc longtable blocks found; refusing to silently skip table conversion")

# Count separators in the actual first header row, not letters in the column
# preamble (which may contain commands such as \raggedright and \arraybackslash).
for match in reversed(matches):
    header_end = source.find(r"\midrule\noalign{}", match.end())
    if header_end < 0:
        raise SystemExit("Could not locate the first table header terminator")
    header = source[match.end():header_end]
    columns = header.count("&") + 1
    if columns < 2:
        raise SystemExit(f"Unexpected one-column table header: {header!r}")
    replacement = (
        r"\begin{table}[!t]" + "\n"
        + r"\centering\small" + "\n"
        + r"\begin{tabularx}{\columnwidth}{@"
        + "X" * columns
        + "@{}}" + "\n"
        + r"\toprule\noalign{}"
    )
    source = source[:match.start()] + replacement + source[match.end():]

source = source.replace(r"\endhead", "").replace(r"\endlastfoot", "")
source = source.replace(r"\end{longtable}", r"\end{tabularx}" + "\n" + r"\end{table}")
if r"\begin{longtable}" in source or r"\end{longtable}" in source:
    raise SystemExit("Unconverted longtable environment remains")

# Structural sanity checks: every generated tabularx must have a nonempty X
# specification, and the number of table starts and ends must match.
starts = re.findall(r"\\begin\{tabularx\}\{\\columnwidth\}\{@(X+)@\{\}\}", source)
if len(starts) != len(matches) or source.count(r"\end{tabularx}") != len(matches):
    raise SystemExit("Tabularx structural check failed")
path.write_text(source, encoding="utf-8")
print("Converted tables with column counts: " + ", ".join(str(len(x)) for x in starts))
