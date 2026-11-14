#!/usr/bin/env python3
"""Convert Pandoc longtable blocks to single-column IEEEtran tabularx floats."""
from pathlib import Path
import re

path = Path("build/Paper1_IEEEtran.tex")
source = path.read_text(encoding="utf-8")
pattern = re.compile(r"\\begin\{longtable\}\[\]\{(.*?)\}\s*\n\\toprule\\noalign\{\}", re.S)

def start_replacement(match):
    spec = match.group(1)
    columns = len(re.findall(r"(?:>\{[^}]*\})?(?:p\{|[rlc])", spec))
    if columns < 2:
        raise SystemExit(f"Could not determine longtable column count from: {spec!r}")
    return r"\begin{table}[!t]" + "\n" + r"\centering\small" + "\n" + r"\begin{tabularx}{\columnwidth}{@" + "X" * columns + "@{}}" + "\n" + r"\toprule\noalign{}"

source, count = pattern.subn(start_replacement, source)
if count == 0:
    raise SystemExit("No Pandoc longtable blocks found; refusing to silently skip table conversion")
source = source.replace(r"\endhead", "").replace(r"\endlastfoot", "")
source = source.replace(r"\end{longtable}", r"\end{tabularx}" + "\n" + r"\end{table}")
if r"\begin{longtable}" in source or r"\end{longtable}" in source:
    raise SystemExit("Unconverted longtable environment remains")
path.write_text(source, encoding="utf-8")
print(f"Converted {count} Pandoc longtable blocks to IEEE single-column tabularx floats.")
