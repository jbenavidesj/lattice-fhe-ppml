#!/usr/bin/env python3
"""Convert Pandoc longtable blocks into IEEEtran-compatible tabularx floats."""
from pathlib import Path
import re

path = Path("build/Paper1_IEEEtran.tex")
source = path.read_text(encoding="utf-8")
pattern = re.compile(r"\\begin\{longtable\}\[\]\{(.*?)\}\s*\n\\toprule\\noalign\{\}", re.S)
matches = list(pattern.finditer(source))
if not matches:
    raise SystemExit("No Pandoc longtable blocks found; refusing to skip conversion")

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
        + r"\begin{tabularx}{\columnwidth}{@{}"
        + "X" * columns
        + "@{}}" + "\n"
        + r"\toprule\noalign{}"
    )
    source = source[:match.start()] + replacement + source[match.end():]

source = source.replace(r"\endhead", "").replace(r"\endlastfoot", "")
source = source.replace(r"\end{longtable}", r"\end{tabularx}" + "\n" + r"\end{table}")
if r"\begin{longtable}" in source or r"\end{longtable}" in source:
    raise SystemExit("Unconverted longtable environment remains")

# Pandoc places the longtable footer rule before the body rows. In a normal
# tabularx float, move that rule to the actual end of each table.
table_pattern = re.compile(r"(\\begin\{tabularx\}\{\columnwidth\}\{@\{\}X+@\{\}\})(.*?)(\\end\{tabularx\})", re.S)
def fix_table(match):
    body = match.group(2)
    footer = r"\bottomrule\noalign{}"
    if body.count(footer) != 1:
        raise SystemExit("Expected exactly one Pandoc bottomrule in each converted table")
    body = body.replace(footer, "", 1).rstrip() + "\n" + footer + "\n"
    return match.group(1) + body + match.group(3)

source, fixed = table_pattern.subn(fix_table, source)
if fixed != len(matches):
    raise SystemExit(f"Expected to repair {len(matches)} tables, repaired {fixed}")

# Verify that every table has the order top rule -> mid rule -> data -> bottom rule.
for m in table_pattern.finditer(source):
    body = m.group(2)
    if not (body.find(r"\toprule") < body.find(r"\midrule") < body.rfind(r"\bottomrule")):
        raise SystemExit("Table rule ordering check failed")

path.write_text(source, encoding="utf-8")
print(f"Converted and reordered rules in {fixed} tables.")
