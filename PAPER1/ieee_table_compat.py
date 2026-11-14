#!/usr/bin/env python3
"""Convert Pandoc longtable blocks into IEEEtran-compatible tabularx floats."""
from pathlib import Path
import re

path = Path("build/Paper1_IEEEtran.tex")
source = path.read_text(encoding="utf-8")

# Match the complete Pandoc longtable structure. Do not parse its column
# preamble: Pandoc emits nested braces and multiline p-column definitions.
pattern = re.compile(
    r"\\begin\{longtable\}.*?\\toprule\\noalign\{\}"
    r"(.*?)\\midrule\\noalign\{\}\\endhead"
    r"\\bottomrule\\noalign\{\}\\endlastfoot"
    r"(.*?)\\end\{longtable\}",
    re.S,
)
matches = list(pattern.finditer(source))
if len(matches) != 5:
    raise SystemExit(f"Expected 5 Pandoc longtables, found {len(matches)}")

def convert(match):
    header = match.group(1).strip()
    body = match.group(2).strip()
    columns = header.count("&") + 1
    if columns < 2:
        raise SystemExit(f"Unexpected table header with {columns} columns: {header!r}")
    if r"\bottomrule" in body:
        raise SystemExit("Unexpected bottomrule inside table body")
    return (
        r"\begin{table}[!t]" + "\n"
        + r"\centering\small" + "\n"
        + r"\begin{tabularx}{\columnwidth}{@{}" + "X" * columns + "@{}}" + "\n"
        + r"\toprule\noalign{}" + "\n"
        + header + "\n"
        + r"\midrule\noalign{}" + "\n"
        + body + "\n"
        + r"\bottomrule\noalign{}" + "\n"
        + r"\end{tabularx}" + "\n"
        + r"\end{table}"
    )

source, converted = pattern.subn(convert, source)
if converted != 5:
    raise SystemExit(f"Expected to convert 5 tables, converted {converted}")
if r"\begin{longtable}" in source or r"\end{longtable}" in source:
    raise SystemExit("Unconverted longtable environment remains")

# Confirm that every converted table has a valid width/spec pair and ordered rules.
table_pattern = re.compile(
    r"\\begin\{tabularx\}\{\\columnwidth\}\{@\{\}X+@\{\}\}(.*?)\\end\{tabularx\}",
    re.S,
)
tables = list(table_pattern.finditer(source))
if len(tables) != 5:
    raise SystemExit(f"Expected 5 IEEE tabularx tables, found {len(tables)}")
for table in tables:
    body = table.group(1)
    if not (body.find(r"\toprule") < body.find(r"\midrule") < body.rfind(r"\bottomrule")):
        raise SystemExit("Table rule ordering check failed")

path.write_text(source, encoding="utf-8")
print(f"Converted and verified {converted} IEEE-compatible tables.")
