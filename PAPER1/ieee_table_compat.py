#!/usr/bin/env python3
"""Convert Pandoc longtable blocks into IEEEtran-compatible tabularx floats."""
from pathlib import Path
import re

path = Path("build/Paper1_IEEEtran.tex")
source = path.read_text(encoding="utf-8")

# Break the long MITM payload header inside its table cell; this is a
# presentation-only change and leaves the underlying label and values intact.
source = source.replace(
    "log2(payload bytes)",
    r"\shortstack{log2(payload\\ bytes)}",
)
if "log2(payload bytes)" in source:
    raise SystemExit("MITM payload header wrapping substitution failed")

# Make long decimal literals breakable without changing their values.
# seqsplit is used in text mode; the one display-math modulus is wrapped in text.
def format_display_modulus(match):
    digits = match.group(1)
    # Preserve the exact integer while splitting its display over aligned rows.
    chunks = [digits[i:i + 22] for i in range(0, len(digits), 22)]
    rows = [r"Q={}&\mathtt{" + chunks[0] + "}"]
    rows.extend(r"&\mathtt{" + chunk + "}" for chunk in chunks[1:])
    return r"\begin{aligned}" + r" \\ ".join(rows) + r"\end{aligned}"

source = re.sub(
    r"Q=(\d{40,})",
    format_display_modulus,
    source,
)
source = re.sub(
    r"(?<![A-Za-z0-9\{])([0-9]{14,})(?![A-Za-z0-9\}])",
    lambda m: r"\seqsplit{" + m.group(1) + "}",
    source,
)

# Permit long repository paths and identifiers to wrap at character boundaries.
source = re.sub(
    r"\\texttt\{([^{}]+)\}",
    lambda m: r"\texttt{\seqsplit{" + m.group(1) + "}}",
    source,
)

# Pandoc inserts line breaks between booktabs rules and longtable markers.
# Allow whitespace at those boundaries; do not parse the nested column preamble.
pattern = re.compile(
    r"\\begin\{longtable\}.*?\\toprule\\noalign\{\}\s*"
    r"(.*?)\s*\\midrule\\noalign\{\}\s*\\endhead\s*"
    r"\\bottomrule\\noalign\{\}\s*\\endlastfoot\s*"
    r"(.*?)\s*\\end\{longtable\}",
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
    # Keep all five MITM resource columns under tabularx width control. Fixed-width
    # X columns prevent natural-width header boxes from expanding the alignment.
    if "log2(half-table entries)" in header:
        table_font = r"\centering\scriptsize"
        column_spec = "@{}XXXXX@{}"
    else:
        table_font = r"\centering\small"
        column_spec = "@{}" + "X" * columns + "@{}"
    return (
        r"\begin{table}[!t]" + "\n"
        + table_font + "\n"
        + r"\begin{tabularx}{\columnwidth}{" + column_spec + "}" + "\n"
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
    r"\\begin\{tabularx\}\{\\columnwidth\}\{@\{\}(?:X+|rrXXX)@\{\}\}(.*?)\\end\{tabularx\}",
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
